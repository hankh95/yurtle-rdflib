"""
Yurtle Parser - Markdown with Turtle Frontmatter
=================================================

Parses Markdown files that have Turtle (RDF) frontmatter, enabling
every document to be a node in the knowledge graph.

THE INSIGHT:
- Yurtle = Markdown + Turtle frontmatter
- Every document IS the knowledge graph
- Files are the interface

EXAMPLE FILE:
```markdown
---
@prefix yurtle: <https://yurtle.dev/schema/> .
@prefix pm: <https://yurtle.dev/pm/> .

<urn:task:F-048> a yurtle:WorkItem ;
    pm:status "in-progress" ;
    pm:priority 2 .
---

# F-048: Production Hardening

Human-readable content here...
```

BACKWARDS COMPATIBLE:
- If frontmatter starts with `@prefix`, parse as Turtle
- Otherwise, parse as YAML (existing behavior)
- Files stay as .md - all tools work

License: MIT
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, XSD

logger = logging.getLogger(__name__)

# Standard Yurtle namespaces
YURTLE = Namespace("https://yurtle.dev/schema/")
PM = Namespace("https://yurtle.dev/pm/")
BEING = Namespace("https://yurtle.dev/being/")
VOYAGE = Namespace("https://yurtle.dev/voyage/")
KNOWLEDGE = Namespace("https://yurtle.dev/knowledge/")


@dataclass
class YurtleDocument:
    """A parsed Yurtle document with both graph and content."""

    # The RDF graph from frontmatter (or converted from YAML)
    graph: Graph

    # The markdown content below frontmatter
    content: str

    # Original frontmatter text
    frontmatter_raw: str

    # Whether frontmatter was Turtle or YAML
    frontmatter_type: str  # "turtle" | "yaml" | "none"

    # File path if loaded from file
    source_path: Path | None = None

    # The subject URI (main entity this doc describes)
    subject_uri: URIRef | None = None

    def get_property(self, predicate: URIRef) -> str | None:
        """Get a single property value from the graph."""
        if self.subject_uri:
            for obj in self.graph.objects(self.subject_uri, predicate):
                return str(obj)
        return None

    def get_properties(self, predicate: URIRef) -> list[str]:
        """Get all values for a predicate."""
        if self.subject_uri:
            return [str(obj) for obj in self.graph.objects(self.subject_uri, predicate)]
        return []

    def to_dict(self) -> dict[str, Any]:
        """Convert graph to dictionary (for YAML compatibility)."""
        result: dict[str, Any] = {}
        if self.subject_uri:
            for pred, obj in self.graph.predicate_objects(self.subject_uri):
                key = str(pred).split("/")[-1].split("#")[-1]
                value = str(obj)
                if key in result:
                    if isinstance(result[key], list):
                        result[key].append(value)
                    else:
                        result[key] = [result[key], value]
                else:
                    result[key] = value
        return result


class YurtleParser:
    """
    Parser for Yurtle documents (Markdown with Turtle frontmatter).

    Supports:
    - Turtle frontmatter (RDF triples)
    - YAML frontmatter (converted to RDF)
    - No frontmatter (empty graph)
    """

    # Regex to extract frontmatter
    FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)

    # Regex to extract fenced turtle/yurtle blocks from markdown body.
    # Handles: trailing spaces after language tag, CRLF line endings,
    # and line-anchored closing fence (CommonMark compliance).
    FENCED_BLOCK_PATTERN = re.compile(
        r"```(?:turtle|yurtle)\s*\r?\n(.*?)^```", re.DOTALL | re.MULTILINE
    )

    # Regex to extract fenced yurtle-table blocks from markdown body.
    FENCED_TABLE_PATTERN = re.compile(r"```yurtle-table\s*\r?\n(.*?)^```", re.DOTALL | re.MULTILINE)

    # Patterns for yurtle-table directive parsing
    _TABLE_TYPE_DIRECTIVE = re.compile(r"^@type\s+(.+?)\s*$", re.MULTILINE)
    _TABLE_PREFIX_DECL = re.compile(r"^@prefix\s+(\w*):\s*<([^>]+)>\s*\.\s*$", re.MULTILINE)
    _TABLE_SEPARATOR = re.compile(r"^\|[\s:]*-+[\s:|-]*\|$")
    _DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    # Standard namespace prefixes
    STANDARD_PREFIXES = {
        "yurtle": YURTLE,
        "pm": PM,
        "being": BEING,
        "voyage": VOYAGE,
        "knowledge": KNOWLEDGE,
        "rdf": RDF,
        "rdfs": RDFS,
        "xsd": XSD,
    }

    def __init__(self):
        self.logger = logging.getLogger("yurtle-parser")

    def parse(self, text: str, source_path: Path | None = None) -> YurtleDocument:
        """
        Parse a Yurtle document from text.

        Args:
            text: The full document text
            source_path: Optional path for URI generation

        Returns:
            YurtleDocument with parsed graph and content
        """
        match = self.FRONTMATTER_PATTERN.match(text)

        if not match:
            # No frontmatter — still parse fenced blocks from body
            graph = Graph()
            for prefix, ns in self.STANDARD_PREFIXES.items():
                graph.bind(prefix, ns)
            self._parse_blocks(text, graph)
            return YurtleDocument(
                graph=graph,
                content=text,
                frontmatter_raw="",
                frontmatter_type="none",
                source_path=source_path,
            )

        frontmatter_raw = match.group(1)
        content = match.group(2)

        # Detect frontmatter type
        if self._is_turtle(frontmatter_raw):
            graph, subject_uri = self._parse_turtle(frontmatter_raw, source_path)
            frontmatter_type = "turtle"
        else:
            graph, subject_uri = self._parse_yaml(frontmatter_raw, source_path)
            frontmatter_type = "yaml"

        # Parse fenced turtle/yurtle blocks and yurtle-table blocks
        self._parse_blocks(content, graph)

        return YurtleDocument(
            graph=graph,
            content=content,
            frontmatter_raw=frontmatter_raw,
            frontmatter_type=frontmatter_type,
            source_path=source_path,
            subject_uri=subject_uri,
        )

    def parse_file(self, path: str | Path) -> YurtleDocument:
        """Parse a Yurtle document from a file."""
        path = Path(path)
        text = path.read_text(encoding="utf-8")
        return self.parse(text, source_path=path)

    # Heuristic patterns for detecting non-Turtle content in fenced blocks
    _YAML_FIRST_LINE = re.compile(r"^[a-zA-Z_][\w-]*:\s*$")
    _MERGE_CONFLICT = re.compile(r"^<{7}\s|^={7}\s*$|^>{7}\s", re.MULTILINE)

    def _parse_blocks(self, content: str, graph: Graph) -> None:
        """
        Extract and parse fenced turtle/yurtle blocks from markdown body.

        Handles both ```turtle and ```yurtle fenced code blocks.
        Each block's Turtle content is parsed and merged into the
        document's graph. Malformed blocks are skipped with a warning.

        Prefix inheritance: blocks automatically inherit all namespace
        bindings from the document's graph (standard prefixes plus any
        declared in Turtle frontmatter).

        Robustness: blocks that look like YAML or contain git merge
        conflict markers are silently skipped.

        Note: CommonMark info strings (e.g. ```turtle linenos) are
        intentionally not matched — only bare language tags with optional
        trailing whitespace are supported.

        Warning: Round-trip duplication — YurtleWriter serializes all triples
        into frontmatter while fenced blocks remain in body text. A subsequent
        parse will double-count those triples. Consumers should be aware of
        this when doing write+reparse cycles.
        """
        # Build @prefix header from graph's namespace bindings so fenced
        # blocks inherit the document's prefix context.
        prefix_header = self._build_prefix_header(graph)

        for match in self.FENCED_BLOCK_PATTERN.finditer(content):
            block_content = match.group(1).strip()
            if not block_content:
                continue

            # Skip blocks that look like YAML, not Turtle
            if self._looks_like_yaml(block_content):
                self.logger.debug(
                    "Skipping non-Turtle content in fenced block " f"at offset {match.start()}"
                )
                continue

            # Skip blocks with git merge conflict markers
            if self._MERGE_CONFLICT.search(block_content):
                self.logger.debug(
                    "Skipping fenced block with merge conflict markers "
                    f"at offset {match.start()}"
                )
                continue

            try:
                # Prepend prefix declarations so blocks inherit document
                # namespace context.  Any @prefix in the block itself will
                # override the injected ones (last declaration wins).
                enriched = prefix_header + block_content
                graph.parse(data=enriched, format="turtle")
            except Exception as e:
                self.logger.debug(f"Failed to parse fenced block at offset {match.start()}: {e}")

        # Parse yurtle-table blocks
        self._parse_table_blocks(content, graph)

    def _parse_table_blocks(self, content: str, graph: Graph) -> None:
        """Parse ```yurtle-table fenced blocks into RDF triples.

        A yurtle-table block contains:
        1. Optional @prefix declarations
        2. Optional @type directive (sets rdf:type for all rows)
        3. A markdown table where:
           - Headers are predicate URIs (resolved against prefixes)
           - @id column is the subject URI for each row
           - Empty cells produce no triple
        """
        for match in self.FENCED_TABLE_PATTERN.finditer(content):
            block_content = match.group(1).strip()
            if not block_content:
                continue
            try:
                self._parse_single_table_block(block_content, graph)
            except Exception as e:
                self.logger.debug(
                    f"Failed to parse yurtle-table block at offset " f"{match.start()}: {e}"
                )

    def _parse_single_table_block(self, block_content: str, graph: Graph) -> None:
        """Parse a single yurtle-table block and add triples to graph."""
        # 1. Collect prefixes: inherited from graph + declared in block
        prefixes: dict[str, str] = {}
        for prefix, ns in graph.namespace_manager.namespaces():
            if prefix:
                prefixes[prefix] = str(ns)

        for m in self._TABLE_PREFIX_DECL.finditer(block_content):
            prefix_name = m.group(1)
            prefix_uri = m.group(2)
            prefixes[prefix_name] = prefix_uri
            graph.bind(prefix_name, Namespace(prefix_uri))

        # 2. Extract @type directive
        row_type_uri: URIRef | None = None
        type_match = self._TABLE_TYPE_DIRECTIVE.search(block_content)
        if type_match:
            raw_type = type_match.group(1).strip()
            row_type_uri = self._resolve_prefixed_name(raw_type, prefixes)

        # 3. Find the markdown table lines
        lines = block_content.split("\n")
        table_lines: list[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("|"):
                table_lines.append(stripped)

        if len(table_lines) < 2:
            return  # Need at least header + separator (or header + data)

        # 4. Parse header row → predicate URIs
        header_line = table_lines[0]
        headers = [h.strip() for h in header_line.split("|")[1:-1]]

        # Find the @id column index
        id_col: int | None = None
        predicate_map: dict[int, URIRef | None] = {}

        for i, header in enumerate(headers):
            if header == "@id":
                id_col = i
                predicate_map[i] = None  # @id is not a predicate
            elif header == "@type":
                predicate_map[i] = RDF.type
            else:
                predicate_map[i] = self._resolve_prefixed_name(header, prefixes)

        if id_col is None:
            self.logger.debug("yurtle-table block missing @id column")
            return

        # 5. Parse data rows (skip separator rows)
        for table_line in table_lines[1:]:
            if self._TABLE_SEPARATOR.match(table_line):
                continue

            cells = [c.strip() for c in table_line.split("|")[1:-1]]

            # Pad cells if row is shorter than header
            while len(cells) < len(headers):
                cells.append("")

            # Get subject from @id column
            subject_raw = cells[id_col] if id_col < len(cells) else ""
            if not subject_raw:
                continue

            subject = self._resolve_prefixed_name(subject_raw, prefixes)

            # Add @type triple if @type directive present
            if row_type_uri is not None:
                graph.add((subject, RDF.type, row_type_uri))

            # Add triples for each non-empty cell
            for col_idx, cell_value in enumerate(cells):
                if col_idx == id_col:
                    continue
                if not cell_value:
                    continue

                predicate = predicate_map.get(col_idx)
                if predicate is None:
                    continue

                # For @type column, resolve as URI
                obj: Literal | URIRef
                if predicate == RDF.type:
                    obj = self._resolve_prefixed_name(cell_value, prefixes)
                    graph.add((subject, predicate, obj))
                else:
                    obj = self._infer_literal(cell_value, prefixes)
                    graph.add((subject, predicate, obj))

    def _resolve_prefixed_name(self, name: str, prefixes: dict[str, str]) -> URIRef:
        """Resolve a prefixed name (e.g., 'kb:Phase') to a full URIRef.

        Handles:
        - Prefixed names: 'kb:Phase' → URIRef(kb_namespace + 'Phase')
        - Fragment references: '#phase-1' → URIRef('#phase-1')
        - Full URIs: '<http://...>' → URIRef('http://...')
        - Bare names: 'something' → URIRef('something')
        """
        name = name.strip()

        # Full URI in angle brackets
        if name.startswith("<") and name.endswith(">"):
            return URIRef(name[1:-1])

        # Fragment reference
        if name.startswith("#"):
            return URIRef(name)

        # Prefixed name
        if ":" in name:
            prefix, local = name.split(":", 1)
            ns = prefixes.get(prefix)
            if ns is not None:
                return URIRef(ns + local)

        return URIRef(name)

    def _infer_literal(self, value: str, prefixes: dict[str, str]) -> Literal | URIRef:
        """Infer the RDF type of a table cell value.

        Type inference:
        - Integer-looking values ('1', '42') → xsd:integer
        - Date-looking values ('2026-02-27') → xsd:date
        - URI references ('#foo', 'http://...', 'prefix:local') → URIRef
        - Everything else → xsd:string (plain Literal)
        """
        # Check for URI-like values
        if value.startswith("#") or value.startswith("<"):
            return self._resolve_prefixed_name(value, prefixes)
        if value.startswith("http://") or value.startswith("https://"):
            return URIRef(value)

        # Check for prefixed name that looks like a URI reference
        if ":" in value and not self._DATE_PATTERN.match(value):
            prefix = value.split(":", 1)[0]
            if prefix in prefixes:
                return self._resolve_prefixed_name(value, prefixes)

        # Date
        if self._DATE_PATTERN.match(value):
            return Literal(value, datatype=XSD.date)

        # Integer
        try:
            int_val = int(value)
            return Literal(int_val, datatype=XSD.integer)
        except ValueError:
            pass

        # Plain string
        return Literal(value)

    @staticmethod
    def _build_prefix_header(graph: Graph) -> str:
        """Build @prefix declarations from the graph's namespace bindings.

        Returns a string of @prefix lines that can be prepended to fenced
        block content, allowing blocks to use any prefix declared in the
        document's frontmatter or in the standard set.
        """
        lines = []
        for prefix, ns in sorted(graph.namespace_manager.namespaces()):
            if prefix:  # Skip default (empty) namespace
                lines.append(f"@prefix {prefix}: <{ns}> .")
        return "\n".join(lines) + "\n\n" if lines else ""

    @classmethod
    def _looks_like_yaml(cls, content: str) -> bool:
        """Heuristic: detect content that looks like YAML rather than Turtle.

        Checks the first non-empty, non-comment line for YAML patterns:
        - ``---`` (YAML document start marker)
        - ``key:`` at end of line (YAML block mapping key)

        These patterns don't occur in valid Turtle, so false positives
        are unlikely.
        """
        for line in content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # YAML document start
            if line == "---":
                return True
            # YAML block mapping key: "key:" at end of line
            # In Turtle, "prefix:" is always followed by a local name
            if cls._YAML_FIRST_LINE.match(line):
                return True
            # First real line found — not YAML-like
            return False
        return False

    def _is_turtle(self, frontmatter: str) -> bool:
        """Check if frontmatter is Turtle format."""
        stripped = frontmatter.strip()
        # Turtle starts with @prefix, @base, or a URI
        return (
            stripped.startswith("@prefix")
            or stripped.startswith("@base")
            or stripped.startswith("<")
            or stripped.startswith("PREFIX")
            or stripped.startswith("BASE")
        )

    def _parse_turtle(
        self, frontmatter: str, source_path: Path | None
    ) -> tuple[Graph, URIRef | None]:
        """Parse Turtle frontmatter into an RDF graph."""
        graph = Graph()

        # Bind standard prefixes
        for prefix, ns in self.STANDARD_PREFIXES.items():
            graph.bind(prefix, ns)

        try:
            graph.parse(data=frontmatter, format="turtle")

            # Find the main subject (first subject that's a URIRef)
            subject_uri = None
            for s in graph.subjects():
                if isinstance(s, URIRef):
                    subject_uri = s
                    break

            # If no subject found, create one from file path
            if not subject_uri and source_path:
                subject_uri = self._uri_from_path(source_path)
                graph.add((subject_uri, RDF.type, YURTLE.Document))

            return graph, subject_uri

        except Exception as e:
            self.logger.error(f"Failed to parse Turtle frontmatter: {e}")
            return Graph(), None

    def _parse_yaml(
        self, frontmatter: str, source_path: Path | None
    ) -> tuple[Graph, URIRef | None]:
        """Parse YAML frontmatter and convert to RDF graph."""
        graph = Graph()

        # Bind standard prefixes
        for prefix, ns in self.STANDARD_PREFIXES.items():
            graph.bind(prefix, ns)

        try:
            data = yaml.safe_load(frontmatter)
            if not data:
                return graph, None

            # Create subject URI
            if source_path:
                subject_uri = self._uri_from_path(source_path)
            elif "id" in data:
                subject_uri = URIRef(f"urn:{data['id']}")
            else:
                subject_uri = URIRef("urn:unknown")

            # Convert YAML to RDF triples
            self._yaml_to_triples(graph, subject_uri, data)

            return graph, subject_uri

        except Exception as e:
            self.logger.error(f"Failed to parse YAML frontmatter: {e}")
            return Graph(), None

    def _yaml_to_triples(self, graph: Graph, subject: URIRef, data: dict[str, Any]):
        """Convert YAML dict to RDF triples."""
        # Map common YAML keys to predicates
        key_mappings = {
            "type": RDF.type,
            "title": YURTLE.title,
            "status": PM.status,
            "priority": PM.priority,
            "assignee": PM.assignedTo,
            "assigned_to": PM.assignedTo,
            "created": YURTLE.created,
            "updated": YURTLE.updated,
            "tags": YURTLE.tag,
            "labels": YURTLE.label,
            "methodology": PM.methodology,
            "domain": BEING.domain,
            "name": YURTLE.name,
            "description": YURTLE.description,
        }

        for key, value in data.items():
            predicate = key_mappings.get(key, YURTLE[key])

            if isinstance(value, list):
                for item in value:
                    self._add_triple(graph, subject, predicate, item)
            else:
                self._add_triple(graph, subject, predicate, value)

    def _add_triple(self, graph: Graph, subject: URIRef, predicate: URIRef, value: Any):
        """Add a triple with appropriate literal type."""
        obj: Literal | URIRef
        if isinstance(value, bool):
            obj = Literal(value, datatype=XSD.boolean)
        elif isinstance(value, int):
            obj = Literal(value, datatype=XSD.integer)
        elif isinstance(value, float):
            obj = Literal(value, datatype=XSD.decimal)
        elif isinstance(value, str) and value.startswith("urn:"):
            obj = URIRef(value)
        elif isinstance(value, str) and value.startswith("http"):
            obj = URIRef(value)
        else:
            obj = Literal(str(value))

        graph.add((subject, predicate, obj))

    def _uri_from_path(self, path: Path) -> URIRef:
        """Generate a URIRef from a file path."""
        # Use file stem as default
        return URIRef(f"urn:doc:{path.stem}")


class YurtleWriter:
    """Write Yurtle documents with Turtle frontmatter."""

    def __init__(self):
        self.parser = YurtleParser()

    def write(self, doc: YurtleDocument) -> str:
        """Serialize a YurtleDocument back to text."""
        if doc.frontmatter_type == "turtle" or doc.graph:
            frontmatter = self._serialize_turtle(doc.graph)
        elif doc.frontmatter_raw:
            frontmatter = doc.frontmatter_raw
        else:
            # No frontmatter
            return doc.content

        return f"---\n{frontmatter}\n---\n{doc.content}"

    def _serialize_turtle(self, graph: Graph) -> str:
        """Serialize graph to Turtle format."""
        result = graph.serialize(format="turtle")
        # Handle bytes vs string return (depends on rdflib version)
        if isinstance(result, bytes):
            return result.decode("utf-8")
        return result

    def write_file(self, doc: YurtleDocument, path: str | Path):
        """Write a YurtleDocument to a file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        text = self.write(doc)
        path.write_text(text, encoding="utf-8")


# Convenience functions


def parse_yurtle(text: str, source_path: Path | None = None) -> YurtleDocument:
    """Parse a Yurtle document from text."""
    parser = YurtleParser()
    return parser.parse(text, source_path)


def parse_yurtle_file(path: str | Path) -> YurtleDocument:
    """Parse a Yurtle document from a file."""
    parser = YurtleParser()
    return parser.parse_file(path)


def scan_workspace_graph(workspace_path: str | Path, patterns: list[str] | None = None) -> Graph:
    """
    Scan a workspace and build a unified knowledge graph from all Yurtle files.

    Args:
        workspace_path: Root of the workspace
        patterns: Glob patterns to match (default: ['**/*.md'])

    Returns:
        A unified Graph containing all triples from all files
    """
    workspace_path = Path(workspace_path)
    if patterns is None:
        patterns = ["**/*.md"]

    parser = YurtleParser()
    unified_graph = Graph()

    # Bind standard prefixes
    for prefix, ns in parser.STANDARD_PREFIXES.items():
        unified_graph.bind(prefix, ns)

    files_parsed = 0
    triples_added = 0

    for pattern in patterns:
        for path in workspace_path.glob(pattern):
            if path.is_file() and not path.name.startswith("."):
                try:
                    doc = parser.parse_file(path)
                    if doc.graph:
                        initial_size = len(unified_graph)
                        unified_graph += doc.graph
                        triples_added += len(unified_graph) - initial_size
                        files_parsed += 1
                except Exception as e:
                    logger.warning(f"Failed to parse {path}: {e}")

    logger.info(f"Scanned {files_parsed} files, extracted {triples_added} triples")
    return unified_graph
