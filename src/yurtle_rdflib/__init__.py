"""
Yurtle RDFlib Plugin - Unified Entry Point
==========================================

RDFlib integration for Yurtle files (Markdown with Turtle/YAML frontmatter).

Importing this module registers all Yurtle plugins with RDFlib:
- Parser: graph.parse("file.md", format="yurtle")
- Serializer: graph.serialize("file.md", format="yurtle")
- Store: YurtleStore for live bidirectional sync

QUICK START:
    from rdflib import Graph
    import yurtle_rdflib

    # Parse a single file
    graph = Graph()
    graph.parse("document.md", format="yurtle")

    # Load entire workspace
    graph = yurtle_rdflib.load_workspace("workspace/")

    # Modify and save back
    graph.add((subject, predicate, object))
    yurtle_rdflib.save_workspace(graph, "workspace/")

    # Or use live sync with YurtleStore
    graph = yurtle_rdflib.create_live_graph("workspace/", auto_flush=True)
    graph.add((subject, predicate, object))  # Persists immediately

License: MIT
"""

import logging
from pathlib import Path
from typing import Optional, List, Union

from rdflib import Graph, URIRef, Namespace
from rdflib.namespace import RDF, RDFS

# Import plugins (registers them with rdflib on import)
from .parser import YurtleRDFlibParser  # noqa: F401
from .serializer import YurtleRDFlibSerializer  # noqa: F401
from .store import YurtleStore, create_yurtle_graph

# Re-export core components
from .core import (
    YurtleParser,
    YurtleWriter,
    YurtleDocument,
    parse_yurtle,
    parse_yurtle_file,
    scan_workspace_graph,
)

# Re-export namespaces
from .namespaces import (
    YURTLE,
    PM,
    BEING,
    VOYAGE,
    KNOWLEDGE,
    PROVENANCE,
    STANDARD_NAMESPACES,
    bind_standard_namespaces,
)

logger = logging.getLogger(__name__)

# Version info
__version__ = "0.1.0"
__all__ = [
    # Version
    "__version__",
    # Classes
    "YurtleStore",
    "YurtleParser",
    "YurtleWriter",
    "YurtleDocument",
    "YurtleRDFlibParser",
    "YurtleRDFlibSerializer",
    # Functions
    "load_workspace",
    "save_workspace",
    "create_live_graph",
    "create_yurtle_graph",
    "parse_file",
    "serialize_file",
    "parse_yurtle",
    "parse_yurtle_file",
    "scan_workspace_graph",
    "bind_standard_namespaces",
    # Namespaces
    "YURTLE",
    "PM",
    "BEING",
    "VOYAGE",
    "KNOWLEDGE",
    "PROVENANCE",
    "STANDARD_NAMESPACES",
]


# =============================================================================
# Convenience Functions
# =============================================================================

def load_workspace(
    workspace_path: Union[str, Path],
    patterns: Optional[List[str]] = None,
) -> Graph:
    """
    Load all Yurtle files in a workspace into a unified graph.

    This scans the workspace directory for .md files, parses each one,
    and combines all triples into a single graph with provenance.

    Args:
        workspace_path: Root directory to scan
        patterns: Glob patterns to match (default: ['**/*.md'])

    Returns:
        RDFlib Graph containing all triples from workspace

    Example:
        graph = load_workspace("my-project/")
        results = graph.query("SELECT ?s ?title WHERE { ?s yurtle:title ?title }")
    """
    workspace = Path(workspace_path)
    patterns = patterns or ["**/*.md"]

    graph = Graph()
    parser = YurtleParser()

    # Bind standard namespaces
    bind_standard_namespaces(graph)

    files_parsed = 0
    triples_added = 0

    for pattern in patterns:
        for path in workspace.glob(pattern):
            if path.is_file() and not path.name.startswith('.'):
                try:
                    doc = parser.parse_file(path)

                    # Add all triples from the document
                    for triple in doc.graph:
                        graph.add(triple)
                        triples_added += 1

                    # Add provenance triple
                    if doc.subject_uri:
                        file_uri = URIRef(f"file://{path.resolve()}")
                        graph.add((doc.subject_uri, PROVENANCE.definedIn, file_uri))
                        triples_added += 1

                    files_parsed += 1

                except Exception as e:
                    logger.warning(f"Failed to parse {path}: {e}")

    logger.info(f"Loaded workspace: {files_parsed} files, {triples_added} triples")
    return graph


def save_workspace(
    graph: Graph,
    workspace_path: Union[str, Path],
) -> int:
    """
    Save a graph back to workspace files, grouped by provenance.

    This groups triples by their prov:definedIn provenance and writes
    each group back to its source file, preserving markdown content.

    Args:
        graph: RDFlib Graph to save
        workspace_path: Root directory of workspace

    Returns:
        Number of files written

    Example:
        graph = load_workspace("my-project/")
        graph.add((subject, predicate, object))
        save_workspace(graph, "my-project/")
    """
    workspace = Path(workspace_path)
    writer = YurtleWriter()

    # Group subjects by their source file
    file_subjects: dict[Path, list[URIRef]] = {}

    for subject, file_uri in graph.subject_objects(PROVENANCE.definedIn):
        if isinstance(subject, URIRef) and isinstance(file_uri, URIRef):
            file_str = str(file_uri)
            if file_str.startswith("file://"):
                file_path = Path(file_str[7:])
                if file_path not in file_subjects:
                    file_subjects[file_path] = []
                file_subjects[file_path].append(subject)

    files_written = 0

    for file_path, subjects in file_subjects.items():
        try:
            # Read existing markdown content
            markdown_content = ""
            if file_path.exists():
                markdown_content = _extract_markdown(file_path)

            # Build graph for this file
            file_graph = Graph()
            for prefix, ns in graph.namespaces():
                file_graph.bind(prefix, ns)

            for subject in subjects:
                for p, o in graph.predicate_objects(subject):
                    # Skip provenance triples
                    if p == PROVENANCE.definedIn:
                        continue
                    file_graph.add((subject, p, o))

            # Create document and write
            doc = YurtleDocument(
                graph=file_graph,
                content=markdown_content,
                frontmatter_raw="",
                frontmatter_type="turtle",
                source_path=file_path,
                subject_uri=subjects[0] if subjects else None,
            )

            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            writer.write_file(doc, file_path)
            files_written += 1

            logger.debug(f"Wrote {file_path}: {len(file_graph)} triples")

        except Exception as e:
            logger.error(f"Failed to write {file_path}: {e}")

    logger.info(f"Saved workspace: {files_written} files written")
    return files_written


def _extract_markdown(file_path: Path) -> str:
    """Extract markdown content from a Yurtle file."""
    import re

    try:
        content = file_path.read_text()

        # Match frontmatter
        pattern = re.compile(r'^---\s*\n.*?\n---\s*\n(.*)$', re.DOTALL)
        match = pattern.match(content)

        if match:
            return match.group(1)

        # No frontmatter
        return content

    except Exception:
        return ""


def create_live_graph(
    workspace_path: Union[str, Path],
    patterns: Optional[List[str]] = None,
    auto_flush: bool = True,
) -> Graph:
    """
    Create a graph with live bidirectional sync to workspace files.

    Unlike load_workspace(), this creates a YurtleStore-backed graph that:
    - Detects file changes and syncs automatically
    - Writes graph modifications back to files
    - Maintains semantic equivalence with filesystem

    Args:
        workspace_path: Root directory of workspace
        patterns: Glob patterns to match (default: ['**/*.md'])
        auto_flush: If True, persist changes immediately (default: True)

    Returns:
        RDFlib Graph backed by YurtleStore

    Example:
        graph = create_live_graph("my-project/", auto_flush=True)
        graph.add((subject, predicate, object))  # Persists immediately
    """
    return create_yurtle_graph(
        root_dir=str(workspace_path),
        patterns=patterns,
        auto_flush=auto_flush,
    )


def parse_file(file_path: Union[str, Path]) -> Graph:
    """
    Parse a single Yurtle file into a graph.

    Args:
        file_path: Path to the Yurtle file

    Returns:
        RDFlib Graph with parsed triples

    Example:
        graph = parse_file("document.md")
    """
    graph = Graph()
    graph.parse(str(file_path), format="yurtle")
    return graph


def serialize_file(
    graph: Graph,
    file_path: Union[str, Path],
    markdown_content: str = "",
) -> None:
    """
    Serialize a graph to a Yurtle file.

    Args:
        graph: RDFlib Graph to serialize
        file_path: Output file path
        markdown_content: Optional markdown content to include

    Example:
        serialize_file(graph, "output.md", "# My Document\\n\\nContent here...")
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    graph.serialize(
        destination=str(path),
        format="yurtle",
        markdown_content=markdown_content,
    )


# =============================================================================
# Plugin Registration Verification
# =============================================================================

def verify_plugins() -> dict:
    """
    Verify that all Yurtle plugins are properly registered.

    Returns:
        Dict with registration status for each plugin type
    """
    from rdflib.plugin import get as get_plugin
    from rdflib.parser import Parser
    from rdflib.serializer import Serializer

    results = {
        "parser": False,
        "serializer": False,
        "version": __version__,
    }

    try:
        parser = get_plugin("yurtle", Parser)
        results["parser"] = parser is not None
    except Exception:
        pass

    try:
        serializer = get_plugin("yurtle", Serializer)
        results["serializer"] = serializer is not None
    except Exception:
        pass

    return results


# Auto-verify on import (debug logging only)
if __name__ != "__main__":
    status = verify_plugins()
    if status["parser"] and status["serializer"]:
        logger.debug(f"Yurtle plugins registered successfully (v{__version__})")
    else:
        logger.warning(f"Yurtle plugin registration incomplete: {status}")
