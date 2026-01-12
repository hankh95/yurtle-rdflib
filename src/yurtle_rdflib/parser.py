"""
Yurtle RDFlib Parser Plugin
===========================

An RDFlib Parser plugin that enables parsing Yurtle files (Markdown with
Turtle/YAML frontmatter) directly into RDFlib Graphs.

USAGE:
    from rdflib import Graph
    import yurtle_rdflib  # Registers the plugin

    graph = Graph()
    graph.parse("document.md", format="yurtle")

FEATURES:
    - Supports Turtle frontmatter (native RDF)
    - Supports YAML frontmatter (converted to RDF)
    - Automatic subject URI generation
    - Provenance tracking (optional)
    - Works with both file paths and streams

License: MIT
"""

import logging
from io import BytesIO, StringIO
from pathlib import Path
from typing import IO, Optional, Union

from rdflib import Graph, URIRef, Namespace
from rdflib.parser import Parser
from rdflib.plugin import register

from .core import YurtleParser as CoreYurtleParser

logger = logging.getLogger(__name__)

# Provenance namespace
PROVENANCE = Namespace("https://yurtle.dev/provenance/")


class YurtleRDFlibParser(Parser):
    """
    RDFlib Parser plugin for Yurtle format (Markdown with Turtle/YAML frontmatter).

    This parser wraps the core YurtleParser and provides the RDFlib Parser interface.
    It supports:
    - Turtle frontmatter (parsed natively as RDF)
    - YAML frontmatter (converted to RDF triples)
    - Provenance tracking via definedIn triples

    Usage:
        graph = Graph()
        graph.parse("document.md", format="yurtle")

        # With provenance tracking
        graph.parse("document.md", format="yurtle", provenance=True)
    """

    def __init__(self):
        """Initialize the parser."""
        super().__init__()
        self._core_parser = CoreYurtleParser()

    def parse(
        self,
        source,
        sink: Graph,
        format: Optional[str] = None,
        encoding: str = "utf-8",
        **kwargs
    ) -> None:
        """
        Parse a Yurtle document into an RDFlib graph.

        Args:
            source: InputSource object containing the data
            sink: Graph to add triples to
            format: Format identifier (ignored, always "yurtle")
            encoding: Character encoding (default: utf-8)
            **kwargs: Additional arguments:
                - provenance: If True, add nusy:definedIn triples (default: True)

        The source can be:
        - A file path (string or Path)
        - A file-like object (BytesIO, StringIO)
        - An InputSource with a stream
        """
        add_provenance = kwargs.get('provenance', True)

        # Extract content from source
        content = self._get_content(source, encoding)

        # Get source path for provenance
        source_path = self._get_source_path(source)

        # Parse using core parser
        doc = self._core_parser.parse(content, source_path)

        # Add all triples to sink
        for triple in doc.graph:
            sink.add(triple)

        # Add provenance triple if requested and we have both subject and path
        if add_provenance and doc.subject_uri and source_path:
            file_uri = URIRef(f"file://{source_path.resolve()}")
            sink.add((doc.subject_uri, PROVENANCE.definedIn, file_uri))

        logger.debug(
            f"Parsed {source_path or 'stream'}: "
            f"{len(doc.graph)} triples, subject={doc.subject_uri}"
        )

    def _get_content(self, source, encoding: str) -> str:
        """Extract text content from various source types."""
        # Try to get the input stream
        if hasattr(source, 'getByteStream'):
            stream = source.getByteStream()
            if stream:
                content = stream.read()
                if isinstance(content, bytes):
                    return content.decode(encoding)
                return content

        if hasattr(source, 'getCharacterStream'):
            stream = source.getCharacterStream()
            if stream:
                return stream.read()

        # Try to get system ID (file path)
        if hasattr(source, 'getSystemId'):
            system_id = source.getSystemId()
            if system_id:
                # Handle file:// URIs
                if system_id.startswith('file://'):
                    system_id = system_id[7:]
                path = Path(system_id)
                if path.exists():
                    return path.read_text(encoding=encoding)

        # Source might be a file path directly
        if isinstance(source, (str, Path)):
            path = Path(source)
            if path.exists():
                return path.read_text(encoding=encoding)

        raise ValueError(f"Cannot extract content from source: {type(source)}")

    def _get_source_path(self, source) -> Optional[Path]:
        """Extract file path from source if available."""
        # Try system ID
        if hasattr(source, 'getSystemId'):
            system_id = source.getSystemId()
            if system_id:
                if system_id.startswith('file://'):
                    system_id = system_id[7:]
                return Path(system_id)

        # Direct path
        if isinstance(source, (str, Path)):
            return Path(source)

        return None


# Register the parser plugin with RDFlib
register(
    'yurtle',
    Parser,
    'yurtle_rdflib.parser',
    'YurtleRDFlibParser'
)
