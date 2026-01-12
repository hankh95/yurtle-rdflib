"""
YurtleStore - Bidirectional RDFlib Store for Yurtle Files
=========================================================

A custom RDFlib Store that provides full bidirectional synchronization between
an in-memory RDF graph and Yurtle files on disk.

THE INSIGHT:
The .md files ARE the knowledge graph. When you:
- Parse files -> graph contains provenance linking back to files
- Modify graph -> changes write back to correct files
- Query graph -> you're querying file content
- Save graph -> you're saving to files

Semantic equivalence: graph ~ filesystem at all times.

USAGE:
    from rdflib import Graph
    from yurtle_rdflib import YurtleStore

    # Create store with auto-flush (writes immediately)
    store = YurtleStore("workspace/", auto_flush=True)
    graph = Graph(store=store)

    # Add triple - auto-flushes to appropriate file
    graph.add((subject, predicate, object))

    # Or with manual flush
    store = YurtleStore("workspace/", auto_flush=False)
    graph = Graph(store=store)
    graph.add((subject, predicate, object))
    store.flush()  # Write all dirty files

License: MIT
"""

import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Dict, Optional, Any, Iterator, Tuple, Generator, Set, List
from dataclasses import dataclass
from datetime import datetime

from rdflib import Graph, URIRef, Literal, BNode, Namespace
from rdflib.store import Store
from rdflib.term import Node
from rdflib.namespace import RDF, RDFS, XSD

from .core import (
    YurtleParser,
    YurtleWriter,
    YurtleDocument,
    YURTLE,
    PM,
    BEING,
)
from .namespaces import PROVENANCE

logger = logging.getLogger(__name__)


@dataclass
class FileState:
    """Tracks the state of a single file in the store."""
    path: Path
    hash: str
    last_modified: float
    triple_count: int
    subject_uri: Optional[URIRef] = None
    is_dirty: bool = False
    markdown_content: str = ""  # Preserved for round-trip


class YurtleStore(Store):
    """
    Bidirectional RDFlib Store backed by Yurtle/Markdown files.

    This store provides full read/write synchronization between an in-memory
    RDF graph and Yurtle files on disk. Key features:

    - Hash-based change detection for efficient sync
    - Provenance tracking for bidirectional mapping
    - Automatic subject-to-file resolution for new triples
    - Markdown content preservation on round-trip
    - Optional auto-flush for immediate persistence

    Attributes:
        root_dir: Root directory containing Yurtle files
        patterns: Glob patterns for file matching (default: ['**/*.md'])
        auto_flush: If True, flush after every modification
        internal_graph: In-memory RDFlib graph (the cache)
        file_states: Map of file paths to their state
    """

    context_aware = False
    formula_aware = False
    transaction_aware = False

    def __init__(
        self,
        root_dir: str,
        configuration: Optional[str] = None,
        identifier: Optional[str] = None,
        patterns: Optional[List[str]] = None,
        auto_flush: bool = False,
    ):
        """
        Initialize YurtleStore.

        Args:
            root_dir: Root directory containing Yurtle files
            configuration: RDFlib store configuration (unused)
            identifier: Store identifier
            patterns: Glob patterns to match (default: ['**/*.md'])
            auto_flush: If True, flush changes immediately after each add/remove
        """
        super().__init__(configuration, identifier)

        self.root_dir = Path(root_dir)
        self.patterns = patterns or ["**/*.md"]
        self.auto_flush = auto_flush

        # Internal state
        self.internal_graph = Graph()
        self.file_states: Dict[Path, FileState] = {}
        self.parser = YurtleParser()
        self.writer = YurtleWriter()
        self._dirty_files: Set[Path] = set()

        # Bind common namespaces
        self.internal_graph.bind("prov", PROVENANCE)
        self.internal_graph.bind("yurtle", YURTLE)
        self.internal_graph.bind("pm", PM)
        self.internal_graph.bind("being", BEING)

        # Index file path
        self._index_path = self.root_dir / ".yurtle-store-index.json"

        # Load existing index
        self._load_index()

        # Initial sync from filesystem
        self.sync()

        logger.info(
            f"YurtleStore initialized at {self.root_dir} with "
            f"{len(self.file_states)} files, auto_flush={auto_flush}"
        )

    # =========================================================================
    # Index Persistence
    # =========================================================================

    def _load_index(self) -> None:
        """Load file state index from disk."""
        if not self._index_path.exists():
            return

        try:
            with open(self._index_path) as f:
                data = json.load(f)

            for path_str, state_data in data.get("files", {}).items():
                path = Path(path_str)
                self.file_states[path] = FileState(
                    path=path,
                    hash=state_data["hash"],
                    last_modified=state_data["last_modified"],
                    triple_count=state_data["triple_count"],
                    subject_uri=URIRef(state_data["subject_uri"]) if state_data.get("subject_uri") else None,
                    markdown_content=state_data.get("markdown_content", ""),
                )

            logger.debug(f"Loaded index with {len(self.file_states)} entries")

        except Exception as e:
            logger.warning(f"Failed to load index: {e}")
            self.file_states = {}

    def _save_index(self) -> None:
        """Persist file state index to disk."""
        try:
            data = {
                "version": "1.0",
                "updated": datetime.now().isoformat(),
                "root_dir": str(self.root_dir),
                "files": {
                    str(path): {
                        "hash": state.hash,
                        "last_modified": state.last_modified,
                        "triple_count": state.triple_count,
                        "subject_uri": str(state.subject_uri) if state.subject_uri else None,
                        "markdown_content": state.markdown_content,
                    }
                    for path, state in self.file_states.items()
                },
            }

            with open(self._index_path, "w") as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved index with {len(self.file_states)} entries")

        except Exception as e:
            logger.warning(f"Failed to save index: {e}")

    # =========================================================================
    # File Operations
    # =========================================================================

    def _compute_file_hash(self, path: Path) -> str:
        """Compute MD5 hash of file contents."""
        try:
            content = path.read_bytes()
            return hashlib.md5(content).hexdigest()
        except Exception as e:
            logger.warning(f"Failed to hash {path}: {e}")
            return ""

    def _file_uri(self, path: Path) -> URIRef:
        """Convert a file path to a file:// URI."""
        return URIRef(f"file://{path.resolve()}")

    def _uri_to_path(self, uri: URIRef) -> Optional[Path]:
        """Convert a file:// URI back to a Path."""
        uri_str = str(uri)
        if uri_str.startswith("file://"):
            return Path(uri_str[7:])
        return None

    # =========================================================================
    # Synchronization
    # =========================================================================

    def sync(self) -> int:
        """
        Synchronize internal graph with filesystem.

        Scans for new/modified/deleted files and updates the graph accordingly.
        Uses hash-based change detection for efficiency.

        Returns:
            Number of files that were re-synced
        """
        synced_count = 0
        current_files: Set[Path] = set()

        # Scan all matching files
        for pattern in self.patterns:
            for path in self.root_dir.glob(pattern):
                if path.is_file() and not path.name.startswith('.'):
                    current_files.add(path)

        # Check for new/modified files
        for path in current_files:
            file_hash = self._compute_file_hash(path)
            mtime = path.stat().st_mtime

            existing = self.file_states.get(path)

            if existing and existing.hash == file_hash and not existing.is_dirty:
                # File unchanged, skip
                continue

            # File is new or modified - sync it
            self._sync_file_read(path, file_hash, mtime)
            synced_count += 1

        # Check for deleted files
        deleted_files = set(self.file_states.keys()) - current_files
        for path in deleted_files:
            self._remove_file(path)
            synced_count += 1

        # Save index if anything changed
        if synced_count > 0:
            self._save_index()

        logger.info(f"Sync complete: {synced_count} files updated")
        return synced_count

    def _sync_file_read(self, path: Path, file_hash: str, mtime: float) -> None:
        """
        Read a file and sync its triples to the internal graph.

        Args:
            path: Path to the file
            file_hash: Pre-computed MD5 hash
            mtime: File modification time
        """
        logger.debug(f"Reading file: {path}")

        # Remove old triples for this file
        self._remove_file_triples(path)

        # Parse the file
        try:
            doc = self.parser.parse_file(path)
        except Exception as e:
            logger.warning(f"Failed to parse {path}: {e}")
            return

        # Add triples to internal graph
        triple_count = 0
        for s, p, o in doc.graph:
            self.internal_graph.add((s, p, o))
            triple_count += 1

        # Add provenance triple
        file_uri = self._file_uri(path)
        if doc.subject_uri:
            self.internal_graph.add((doc.subject_uri, PROVENANCE.definedIn, file_uri))
            triple_count += 1

        # Update file state
        self.file_states[path] = FileState(
            path=path,
            hash=file_hash,
            last_modified=mtime,
            triple_count=triple_count,
            subject_uri=doc.subject_uri,
            markdown_content=doc.content,
        )

        logger.debug(f"Read {path}: {triple_count} triples")

    def _remove_file(self, path: Path) -> None:
        """Remove a file from the store."""
        self._remove_file_triples(path)
        if path in self.file_states:
            del self.file_states[path]
        self._dirty_files.discard(path)
        logger.debug(f"Removed file: {path}")

    def _remove_file_triples(self, path: Path) -> None:
        """Remove all triples associated with a file."""
        file_uri = self._file_uri(path)

        # Find subjects defined in this file
        subjects_to_remove = set()
        for s in self.internal_graph.subjects(PROVENANCE.definedIn, file_uri):
            subjects_to_remove.add(s)

        # Remove all triples for those subjects
        for subject in subjects_to_remove:
            for p, o in list(self.internal_graph.predicate_objects(subject)):
                self.internal_graph.remove((subject, p, o))

        # Remove the definedIn triple itself
        self.internal_graph.remove((None, PROVENANCE.definedIn, file_uri))

    # =========================================================================
    # Write-Back (Flush)
    # =========================================================================

    def flush(self) -> int:
        """
        Write all dirty files back to disk.

        Groups modified triples by their source file (via provenance) and
        writes each file back with updated frontmatter while preserving
        markdown content.

        Returns:
            Number of files flushed
        """
        if not self._dirty_files:
            return 0

        flushed_count = 0
        for path in list(self._dirty_files):
            try:
                self._flush_file(path)
                flushed_count += 1
            except Exception as e:
                logger.error(f"Failed to flush {path}: {e}")

        self._dirty_files.clear()
        self._save_index()

        logger.info(f"Flushed {flushed_count} files")
        return flushed_count

    def _flush_file(self, path: Path) -> None:
        """
        Write a single file back to disk.

        Args:
            path: Path to the file to flush
        """
        logger.debug(f"Flushing file: {path}")

        state = self.file_states.get(path)
        if not state or not state.subject_uri:
            logger.warning(f"Cannot flush {path}: no state or subject URI")
            return

        # Collect all triples for this subject
        subject_graph = Graph()
        for prefix, ns in self.internal_graph.namespaces():
            subject_graph.bind(prefix, ns)

        for p, o in self.internal_graph.predicate_objects(state.subject_uri):
            # Skip provenance triples
            if p == PROVENANCE.definedIn:
                continue
            subject_graph.add((state.subject_uri, p, o))

        # Create YurtleDocument for serialization
        doc = YurtleDocument(
            graph=subject_graph,
            content=state.markdown_content,
            frontmatter_raw="",
            frontmatter_type="turtle",
            source_path=path,
            subject_uri=state.subject_uri,
        )

        # Write to file
        self.writer.write_file(doc, path)

        # Update state
        state.hash = self._compute_file_hash(path)
        state.last_modified = path.stat().st_mtime
        state.triple_count = len(subject_graph)
        state.is_dirty = False

        logger.debug(f"Flushed {path}: {state.triple_count} triples")

    def _resolve_file_for_subject(self, subject: URIRef) -> Optional[Path]:
        """
        Resolve which file a subject should be stored in.

        First checks if the subject has an existing definedIn provenance triple.
        If not, uses the subject URI pattern to determine the target file.

        Args:
            subject: The subject URI

        Returns:
            Path to the target file, or None if cannot be resolved
        """
        # Check existing provenance
        for file_uri in self.internal_graph.objects(subject, PROVENANCE.definedIn):
            path = self._uri_to_path(file_uri)
            if path:
                return path

        # Cannot resolve - return None
        logger.warning(f"Cannot resolve file for subject: {subject}")
        return None

    def _mark_file_dirty(self, path: Path) -> None:
        """Mark a file as needing to be flushed."""
        self._dirty_files.add(path)
        if path in self.file_states:
            self.file_states[path].is_dirty = True

    # =========================================================================
    # RDFlib Store Interface
    # =========================================================================

    def open(self, configuration: str, create: bool = False) -> Optional[int]:
        """Open the store."""
        self.sync()
        return 1

    def close(self, commit_pending_transaction: bool = False) -> None:
        """Close the store, flushing any pending changes."""
        if commit_pending_transaction or self._dirty_files:
            self.flush()
        self._save_index()

    def destroy(self, configuration: str) -> None:
        """Destroy the store."""
        if self._index_path.exists():
            self._index_path.unlink()
        self.internal_graph = Graph()
        self.file_states = {}
        self._dirty_files = set()

    def add(
        self,
        triple: Tuple[Node, Node, Node],
        context: Any = None,
        quoted: bool = False,
    ) -> None:
        """
        Add a triple to the store.

        The triple is added to the internal graph and the target file is
        marked as dirty. If auto_flush is True, the file is immediately
        written back to disk.

        Args:
            triple: (subject, predicate, object) tuple
            context: Graph context (unused)
            quoted: Whether the triple is quoted (unused)
        """
        s, p, o = triple
        self.internal_graph.add((s, p, o))

        # Determine target file
        if isinstance(s, URIRef):
            target_file = self._resolve_file_for_subject(s)
            if target_file:
                self._mark_file_dirty(target_file)

                # Ensure provenance triple exists
                file_uri = self._file_uri(target_file)
                if (s, PROVENANCE.definedIn, file_uri) not in self.internal_graph:
                    self.internal_graph.add((s, PROVENANCE.definedIn, file_uri))

                # Initialize file state if needed
                if target_file not in self.file_states:
                    self.file_states[target_file] = FileState(
                        path=target_file,
                        hash="",
                        last_modified=0,
                        triple_count=0,
                        subject_uri=s,
                        is_dirty=True,
                    )

                if self.auto_flush:
                    self._flush_file(target_file)

    def remove(
        self,
        triple: Tuple[Optional[Node], Optional[Node], Optional[Node]],
        context: Any = None,
    ) -> None:
        """
        Remove triples matching the pattern.

        Args:
            triple: (subject, predicate, object) with None as wildcard
            context: Graph context (unused)
        """
        s, p, o = triple

        # Find all matching triples first
        matching = list(self.internal_graph.triples((s, p, o)))

        for match_s, match_p, match_o in matching:
            self.internal_graph.remove((match_s, match_p, match_o))

            # Mark affected file as dirty
            if isinstance(match_s, URIRef):
                target_file = self._resolve_file_for_subject(match_s)
                if target_file:
                    self._mark_file_dirty(target_file)

        if self.auto_flush and self._dirty_files:
            self.flush()

    def triples(
        self,
        triple_pattern: Tuple[Optional[Node], Optional[Node], Optional[Node]],
        context: Any = None,
    ) -> Generator[Tuple[Tuple[Node, Node, Node], Any], None, None]:
        """
        Yield all triples matching the pattern.

        Args:
            triple_pattern: (subject, predicate, object) with None as wildcard
            context: Graph context (unused)

        Yields:
            Tuples of (triple, context)
        """
        s, p, o = triple_pattern
        for triple in self.internal_graph.triples((s, p, o)):
            yield triple, None

    def __len__(self, context: Any = None) -> int:
        """Return the number of triples in the store."""
        return len(self.internal_graph)

    def __contains__(self, triple: Tuple[Node, Node, Node]) -> bool:
        """Check if a triple exists in the store."""
        return triple in self.internal_graph

    def contexts(self, triple: Optional[Tuple[Node, Node, Node]] = None) -> Iterator:
        """Return contexts (empty for single-graph store)."""
        return iter([])

    # =========================================================================
    # Convenience Methods
    # =========================================================================

    def query(self, query_string: str, **kwargs) -> Any:
        """
        Execute a SPARQL query against the store.

        Syncs before querying to ensure results reflect latest file changes.

        Args:
            query_string: SPARQL query
            **kwargs: Additional arguments for graph.query()

        Returns:
            Query results
        """
        self.sync()
        return self.internal_graph.query(query_string, **kwargs)

    def get_file_for_subject(self, subject_uri: URIRef) -> Optional[Path]:
        """Get the source file for a subject URI."""
        return self._resolve_file_for_subject(subject_uri)

    def get_dirty_files(self) -> Set[Path]:
        """Get the set of files pending flush."""
        return self._dirty_files.copy()

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the store."""
        return {
            "root_dir": str(self.root_dir),
            "patterns": self.patterns,
            "auto_flush": self.auto_flush,
            "total_files": len(self.file_states),
            "dirty_files": len(self._dirty_files),
            "total_triples": len(self.internal_graph),
        }


# =============================================================================
# Convenience Functions
# =============================================================================

def create_yurtle_graph(
    root_dir: str,
    patterns: Optional[List[str]] = None,
    auto_flush: bool = False,
) -> Graph:
    """
    Create an RDFlib Graph backed by a YurtleStore.

    This is the recommended way to create a bidirectional graph over Yurtle files.

    Args:
        root_dir: Root directory containing Yurtle files
        patterns: Glob patterns to match (default: ['**/*.md'])
        auto_flush: If True, flush changes immediately

    Returns:
        RDFlib Graph with YurtleStore backend

    Example:
        graph = create_yurtle_graph("/path/to/workspace", auto_flush=True)
        graph.add((subject, predicate, object))  # Persists immediately
    """
    store = YurtleStore(root_dir=root_dir, patterns=patterns, auto_flush=auto_flush)
    return Graph(store=store)
