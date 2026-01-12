"""
Yurtle RDFlib Serializer Plugin
===============================

An RDFlib Serializer plugin that enables saving RDFlib graphs back to
Yurtle format (Markdown with Turtle frontmatter).

USAGE:
    from rdflib import Graph
    import yurtle_rdflib  # Registers the plugin

    graph = Graph()
    # ... add triples ...
    graph.serialize("output.md", format="yurtle")

FEATURES:
    - Serializes RDF triples to Turtle frontmatter
    - Preserves markdown content on round-trip (if provided)
    - Groups triples by subject for readable output
    - Filters provenance triples from output
    - Generates proper Yurtle file structure

ROUND-TRIP PRESERVATION:
    When serializing a graph that was parsed from an existing Yurtle file,
    the serializer can preserve the original markdown content. Pass the
    original content via the `markdown_content` keyword argument:

        graph.serialize("file.md", format="yurtle", markdown_content=original_md)

License: MIT
"""

import logging
import re
from io import BytesIO, StringIO
from pathlib import Path
from typing import IO, Optional, Union

from rdflib import Graph, URIRef, Literal, BNode, Namespace
from rdflib.serializer import Serializer
from rdflib.plugin import register
from rdflib.namespace import RDF, RDFS, XSD

from .namespaces import YURTLE, PM, BEING, PROVENANCE

logger = logging.getLogger(__name__)


class YurtleRDFlibSerializer(Serializer):
    """
    RDFlib Serializer plugin for Yurtle format (Markdown with Turtle frontmatter).

    This serializer produces Yurtle files with:
    - Turtle RDF frontmatter between --- markers
    - Optional markdown content after the frontmatter

    The serializer automatically:
    - Filters out provenance triples (definedIn)
    - Binds standard namespace prefixes
    - Groups triples by subject for readability
    - Preserves markdown content when provided
    """

    def __init__(self, store: Graph):
        """Initialize the serializer with a graph store."""
        super().__init__(store)

    def serialize(
        self,
        stream: IO[bytes],
        base: Optional[str] = None,
        encoding: str = "utf-8",
        **kwargs
    ) -> None:
        """
        Serialize the graph to Yurtle format.

        Args:
            stream: Output stream to write to
            base: Base URI (optional)
            encoding: Output encoding (default: utf-8)
            **kwargs: Additional arguments:
                - markdown_content: Markdown content to include after frontmatter
                - preserve_markdown: Path to file with markdown to preserve

        The output format is:
            ---
            @prefix yurtle: <https://yurtle.dev/schema/> .
            ...

            <subject> a <Type> ;
                predicate "value" .
            ---

            # Markdown content here...
        """
        # Get markdown content to preserve (if any)
        markdown_content = kwargs.get('markdown_content', '')

        # If preserve_markdown or original_file path provided, read from it
        preserve_path = kwargs.get('preserve_markdown') or kwargs.get('original_file')
        if preserve_path and not markdown_content:
            markdown_content = self._extract_markdown_from_file(preserve_path)

        # Create a filtered graph without provenance triples
        filtered_graph = self._filter_provenance_triples()

        # Serialize the filtered graph to Turtle
        turtle_content = self._serialize_to_turtle(filtered_graph)

        # Build Yurtle output
        output = self._build_yurtle_output(turtle_content, markdown_content)

        # Write to stream (always as bytes for RDFlib compatibility)
        actual_encoding = encoding if encoding else 'utf-8'
        stream.write(output.encode(actual_encoding))

    def _filter_provenance_triples(self) -> Graph:
        """
        Create a copy of the graph without provenance triples.

        Provenance triples (definedIn) are used internally for tracking
        source files but should not be serialized back to Yurtle files.

        Returns:
            New Graph with provenance triples removed
        """
        filtered = Graph()

        # Copy namespace bindings
        for prefix, namespace in self.store.namespaces():
            filtered.bind(prefix, namespace)

        # Copy all triples except provenance
        for s, p, o in self.store:
            # Skip definedIn provenance triples
            if p == PROVENANCE.definedIn:
                continue
            # Skip file:// URIs in object position (also provenance)
            if isinstance(o, URIRef) and str(o).startswith('file://'):
                continue
            filtered.add((s, p, o))

        return filtered

    def _serialize_to_turtle(self, graph: Graph) -> str:
        """
        Serialize a graph to Turtle format.

        Args:
            graph: Graph to serialize

        Returns:
            Turtle-formatted string
        """
        # Bind standard prefixes if not already bound
        prefixes_to_bind = [
            ('yurtle', YURTLE),
            ('pm', PM),
            ('being', BEING),
            ('rdf', RDF),
            ('rdfs', RDFS),
            ('xsd', XSD),
        ]

        for prefix, ns in prefixes_to_bind:
            try:
                graph.bind(prefix, ns, override=False)
            except Exception:
                pass  # Prefix already bound

        # Serialize to Turtle
        turtle_bytes = graph.serialize(format='turtle')

        # Handle bytes vs string return (depends on rdflib version)
        if isinstance(turtle_bytes, bytes):
            return turtle_bytes.decode('utf-8')
        return turtle_bytes

    def _build_yurtle_output(
        self,
        turtle_content: str,
        markdown_content: str = ""
    ) -> str:
        """
        Build the final Yurtle output with frontmatter and markdown.

        Args:
            turtle_content: Turtle-formatted RDF content
            markdown_content: Optional markdown content

        Returns:
            Complete Yurtle document string
        """
        # Clean up Turtle content (remove trailing whitespace)
        turtle_content = turtle_content.strip()

        # Build output
        parts = ["---", turtle_content, "---"]

        if markdown_content:
            # Ensure markdown starts on new line after frontmatter
            markdown_content = markdown_content.lstrip('\n')
            parts.append("")  # Empty line between frontmatter and content
            parts.append(markdown_content)

        return "\n".join(parts)

    def _extract_markdown_from_file(self, file_path: Union[str, Path]) -> str:
        """
        Extract markdown content from an existing Yurtle file.

        This is used for round-trip preservation - when updating a Yurtle file,
        we want to preserve its markdown content.

        Args:
            file_path: Path to existing Yurtle file

        Returns:
            Markdown content (everything after the frontmatter)
        """
        path = Path(file_path)
        if not path.exists():
            return ""

        try:
            content = path.read_text(encoding='utf-8')

            # Extract content after frontmatter
            frontmatter_pattern = re.compile(
                r'^---\s*\n.*?\n---\s*\n(.*)$',
                re.DOTALL
            )

            match = frontmatter_pattern.match(content)
            if match:
                return match.group(1)

            # No frontmatter - return entire content
            return content

        except Exception as e:
            logger.warning(f"Failed to extract markdown from {file_path}: {e}")
            return ""


# Register the serializer plugin with RDFlib
register(
    'yurtle',
    Serializer,
    'yurtle_rdflib.serializer',
    'YurtleRDFlibSerializer'
)
