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

import re
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Union, List
from dataclasses import dataclass
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD
import logging

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
    source_path: Optional[Path] = None

    # The subject URI (main entity this doc describes)
    subject_uri: Optional[URIRef] = None

    def get_property(self, predicate: URIRef) -> Optional[str]:
        """Get a single property value from the graph."""
        if self.subject_uri:
            for obj in self.graph.objects(self.subject_uri, predicate):
                return str(obj)
        return None

    def get_properties(self, predicate: URIRef) -> List[str]:
        """Get all values for a predicate."""
        if self.subject_uri:
            return [str(obj) for obj in self.graph.objects(self.subject_uri, predicate)]
        return []

    def to_dict(self) -> Dict[str, Any]:
        """Convert graph to dictionary (for YAML compatibility)."""
        result: Dict[str, Any] = {}
        if self.subject_uri:
            for pred, obj in self.graph.predicate_objects(self.subject_uri):
                key = str(pred).split('/')[-1].split('#')[-1]
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
    FRONTMATTER_PATTERN = re.compile(
        r'^---\s*\n(.*?)\n---\s*\n(.*)$',
        re.DOTALL
    )

    # Standard namespace prefixes
    STANDARD_PREFIXES = {
        'yurtle': YURTLE,
        'pm': PM,
        'being': BEING,
        'voyage': VOYAGE,
        'knowledge': KNOWLEDGE,
        'rdf': RDF,
        'rdfs': RDFS,
        'xsd': XSD,
    }

    def __init__(self):
        self.logger = logging.getLogger("yurtle-parser")

    def parse(self, text: str, source_path: Optional[Path] = None) -> YurtleDocument:
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
            # No frontmatter
            return YurtleDocument(
                graph=Graph(),
                content=text,
                frontmatter_raw="",
                frontmatter_type="none",
                source_path=source_path
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

        return YurtleDocument(
            graph=graph,
            content=content,
            frontmatter_raw=frontmatter_raw,
            frontmatter_type=frontmatter_type,
            source_path=source_path,
            subject_uri=subject_uri
        )

    def parse_file(self, path: Union[str, Path]) -> YurtleDocument:
        """Parse a Yurtle document from a file."""
        path = Path(path)
        text = path.read_text(encoding='utf-8')
        return self.parse(text, source_path=path)

    def _is_turtle(self, frontmatter: str) -> bool:
        """Check if frontmatter is Turtle format."""
        stripped = frontmatter.strip()
        # Turtle starts with @prefix, @base, or a URI
        return (
            stripped.startswith('@prefix') or
            stripped.startswith('@base') or
            stripped.startswith('<') or
            stripped.startswith('PREFIX') or
            stripped.startswith('BASE')
        )

    def _parse_turtle(self, frontmatter: str, source_path: Optional[Path]) -> Tuple[Graph, Optional[URIRef]]:
        """Parse Turtle frontmatter into an RDF graph."""
        graph = Graph()

        # Bind standard prefixes
        for prefix, ns in self.STANDARD_PREFIXES.items():
            graph.bind(prefix, ns)

        try:
            graph.parse(data=frontmatter, format='turtle')

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

    def _parse_yaml(self, frontmatter: str, source_path: Optional[Path]) -> Tuple[Graph, Optional[URIRef]]:
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
            elif 'id' in data:
                subject_uri = URIRef(f"urn:{data['id']}")
            else:
                subject_uri = URIRef("urn:unknown")

            # Convert YAML to RDF triples
            self._yaml_to_triples(graph, subject_uri, data)

            return graph, subject_uri

        except Exception as e:
            self.logger.error(f"Failed to parse YAML frontmatter: {e}")
            return Graph(), None

    def _yaml_to_triples(self, graph: Graph, subject: URIRef, data: Dict[str, Any]):
        """Convert YAML dict to RDF triples."""
        # Map common YAML keys to predicates
        key_mappings = {
            'type': RDF.type,
            'title': YURTLE.title,
            'status': PM.status,
            'priority': PM.priority,
            'assignee': PM.assignedTo,
            'assigned_to': PM.assignedTo,
            'created': YURTLE.created,
            'updated': YURTLE.updated,
            'tags': YURTLE.tag,
            'labels': YURTLE.label,
            'methodology': PM.methodology,
            'domain': BEING.domain,
            'name': YURTLE.name,
            'description': YURTLE.description,
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
        if isinstance(value, bool):
            obj = Literal(value, datatype=XSD.boolean)
        elif isinstance(value, int):
            obj = Literal(value, datatype=XSD.integer)
        elif isinstance(value, float):
            obj = Literal(value, datatype=XSD.decimal)
        elif isinstance(value, str) and value.startswith('urn:'):
            obj = URIRef(value)
        elif isinstance(value, str) and value.startswith('http'):
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
        result = graph.serialize(format='turtle')
        # Handle bytes vs string return (depends on rdflib version)
        if isinstance(result, bytes):
            return result.decode('utf-8')
        return result

    def write_file(self, doc: YurtleDocument, path: Union[str, Path]):
        """Write a YurtleDocument to a file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        text = self.write(doc)
        path.write_text(text, encoding='utf-8')


# Convenience functions

def parse_yurtle(text: str, source_path: Optional[Path] = None) -> YurtleDocument:
    """Parse a Yurtle document from text."""
    parser = YurtleParser()
    return parser.parse(text, source_path)


def parse_yurtle_file(path: Union[str, Path]) -> YurtleDocument:
    """Parse a Yurtle document from a file."""
    parser = YurtleParser()
    return parser.parse_file(path)


def scan_workspace_graph(workspace_path: Union[str, Path], patterns: Optional[List[str]] = None) -> Graph:
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
        patterns = ['**/*.md']

    parser = YurtleParser()
    unified_graph = Graph()

    # Bind standard prefixes
    for prefix, ns in parser.STANDARD_PREFIXES.items():
        unified_graph.bind(prefix, ns)

    files_parsed = 0
    triples_added = 0

    for pattern in patterns:
        for path in workspace_path.glob(pattern):
            if path.is_file() and not path.name.startswith('.'):
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
