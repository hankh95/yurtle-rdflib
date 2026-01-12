"""
Tests for the Yurtle parser.
"""

import pytest
from pathlib import Path
from rdflib import Graph, URIRef, Literal

import yurtle_rdflib
from yurtle_rdflib import YurtleParser, YurtleDocument, YURTLE, PM


class TestYurtleParser:
    """Tests for the core YurtleParser class."""

    def test_parse_turtle_frontmatter(self, sample_turtle_doc):
        """Test parsing a document with Turtle frontmatter."""
        parser = YurtleParser()
        doc = parser.parse(sample_turtle_doc)

        assert doc.frontmatter_type == "turtle"
        assert doc.subject_uri == URIRef("urn:task:T-001")
        assert len(doc.graph) >= 4  # At least 4 triples

        # Check title
        title = doc.get_property(YURTLE.title)
        assert title == "Test Task"

        # Check status
        status = doc.get_property(PM.status)
        assert status == "pending"

    def test_parse_yaml_frontmatter(self, sample_yaml_doc):
        """Test parsing a document with YAML frontmatter."""
        parser = YurtleParser()
        doc = parser.parse(sample_yaml_doc)

        assert doc.frontmatter_type == "yaml"
        assert doc.subject_uri is not None
        assert len(doc.graph) >= 1

    def test_parse_no_frontmatter(self, sample_no_frontmatter):
        """Test parsing a document with no frontmatter."""
        parser = YurtleParser()
        doc = parser.parse(sample_no_frontmatter)

        assert doc.frontmatter_type == "none"
        assert len(doc.graph) == 0
        assert "Plain Document" in doc.content

    def test_parse_file(self, tmp_path, sample_turtle_doc):
        """Test parsing from a file."""
        file_path = tmp_path / "test.md"
        file_path.write_text(sample_turtle_doc)

        parser = YurtleParser()
        doc = parser.parse_file(file_path)

        assert doc.source_path == file_path
        assert doc.frontmatter_type == "turtle"

    def test_content_preserved(self, sample_turtle_doc):
        """Test that markdown content is preserved."""
        parser = YurtleParser()
        doc = parser.parse(sample_turtle_doc)

        assert "# T-001: Test Task" in doc.content
        assert "This is a test task" in doc.content

    def test_to_dict(self, sample_turtle_doc):
        """Test converting graph to dictionary."""
        parser = YurtleParser()
        doc = parser.parse(sample_turtle_doc)

        data = doc.to_dict()
        assert "title" in data
        assert data["title"] == "Test Task"

    def test_get_properties_multiple(self):
        """Test getting multiple values for a property."""
        text = '''---
@prefix yurtle: <https://yurtle.dev/schema/> .

<urn:doc:test> yurtle:tag "tag1", "tag2", "tag3" .
---

Content.
'''
        parser = YurtleParser()
        doc = parser.parse(text)

        tags = doc.get_properties(YURTLE.tag)
        assert len(tags) == 3
        assert "tag1" in tags
        assert "tag2" in tags
        assert "tag3" in tags


class TestYurtleRDFlibParser:
    """Tests for the RDFlib parser plugin."""

    def test_plugin_registered(self):
        """Test that the parser plugin is registered."""
        status = yurtle_rdflib.verify_plugins()
        assert status["parser"] is True

    def test_graph_parse(self, tmp_path, sample_turtle_doc):
        """Test parsing via Graph.parse()."""
        file_path = tmp_path / "test.md"
        file_path.write_text(sample_turtle_doc)

        graph = Graph()
        graph.parse(str(file_path), format="yurtle")

        assert len(graph) >= 4

        # Verify subject exists
        subjects = list(graph.subjects())
        assert URIRef("urn:task:T-001") in subjects

    def test_provenance_added(self, tmp_path, sample_turtle_doc):
        """Test that provenance triples are added."""
        file_path = tmp_path / "test.md"
        file_path.write_text(sample_turtle_doc)

        graph = Graph()
        graph.parse(str(file_path), format="yurtle", provenance=True)

        # Check for definedIn triple
        from yurtle_rdflib.namespaces import PROVENANCE
        defined_in_triples = list(graph.triples((None, PROVENANCE.definedIn, None)))
        assert len(defined_in_triples) >= 1

    def test_no_provenance_when_disabled(self, tmp_path, sample_turtle_doc):
        """Test that provenance can be disabled."""
        file_path = tmp_path / "test.md"
        file_path.write_text(sample_turtle_doc)

        graph = Graph()
        graph.parse(str(file_path), format="yurtle", provenance=False)

        # Should not have definedIn triples
        from yurtle_rdflib.namespaces import PROVENANCE
        defined_in_triples = list(graph.triples((None, PROVENANCE.definedIn, None)))
        assert len(defined_in_triples) == 0


class TestConvenienceFunctions:
    """Tests for convenience parsing functions."""

    def test_parse_yurtle(self, sample_turtle_doc):
        """Test parse_yurtle function."""
        doc = yurtle_rdflib.parse_yurtle(sample_turtle_doc)

        assert doc.frontmatter_type == "turtle"
        assert doc.subject_uri is not None

    def test_parse_yurtle_file(self, tmp_path, sample_turtle_doc):
        """Test parse_yurtle_file function."""
        file_path = tmp_path / "test.md"
        file_path.write_text(sample_turtle_doc)

        doc = yurtle_rdflib.parse_yurtle_file(file_path)

        assert doc.source_path == file_path

    def test_parse_file(self, tmp_path, sample_turtle_doc):
        """Test parse_file function."""
        file_path = tmp_path / "test.md"
        file_path.write_text(sample_turtle_doc)

        graph = yurtle_rdflib.parse_file(file_path)

        assert isinstance(graph, Graph)
        assert len(graph) >= 4
