"""
Tests for workspace loading and saving.
"""

import pytest
from pathlib import Path
from rdflib import Graph, URIRef, Literal

import yurtle_rdflib
from yurtle_rdflib import YURTLE, PM
from yurtle_rdflib.namespaces import PROVENANCE


class TestLoadWorkspace:
    """Tests for load_workspace function."""

    def test_load_workspace(self, temp_workspace):
        """Test loading a workspace."""
        graph = yurtle_rdflib.load_workspace(str(temp_workspace))

        assert isinstance(graph, Graph)
        assert len(graph) > 0

    def test_load_workspace_with_patterns(self, temp_workspace):
        """Test loading with specific patterns."""
        # Only load top-level files
        graph = yurtle_rdflib.load_workspace(
            str(temp_workspace),
            patterns=["*.md"]
        )

        # Should have task1 and task2, but not project1 (in subdirectory)
        titles = [str(o) for o in graph.objects(None, YURTLE.title)]
        assert "Task One" in titles
        assert "Task Two" in titles

    def test_load_workspace_provenance(self, temp_workspace):
        """Test that provenance triples are added."""
        graph = yurtle_rdflib.load_workspace(str(temp_workspace))

        # Should have definedIn triples
        provenance_triples = list(graph.triples((None, PROVENANCE.definedIn, None)))
        assert len(provenance_triples) >= 2

    def test_load_empty_workspace(self, tmp_path):
        """Test loading an empty workspace."""
        empty = tmp_path / "empty"
        empty.mkdir()

        graph = yurtle_rdflib.load_workspace(str(empty))

        assert len(graph) == 0


class TestSaveWorkspace:
    """Tests for save_workspace function."""

    def test_save_workspace(self, temp_workspace, tmp_path):
        """Test saving a workspace."""
        # Load
        graph = yurtle_rdflib.load_workspace(str(temp_workspace))

        # Modify
        subject = URIRef("urn:task:task1")
        graph.add((subject, YURTLE.note, Literal("Added note")))

        # Save to new location
        output = tmp_path / "output"
        output.mkdir()

        # We need to update provenance to point to new location
        # For this test, we'll save to the original location
        files_written = yurtle_rdflib.save_workspace(graph, str(temp_workspace))

        assert files_written >= 2

    def test_save_preserves_markdown(self, temp_workspace):
        """Test that saving preserves markdown content."""
        # Load
        graph = yurtle_rdflib.load_workspace(str(temp_workspace))

        # Save
        yurtle_rdflib.save_workspace(graph, str(temp_workspace))

        # Check content preserved
        task1_content = (temp_workspace / "task1.md").read_text()
        assert "# Task One" in task1_content


class TestScanWorkspaceGraph:
    """Tests for scan_workspace_graph function."""

    def test_scan_workspace_graph(self, temp_workspace):
        """Test scanning a workspace."""
        graph = yurtle_rdflib.scan_workspace_graph(temp_workspace)

        assert isinstance(graph, Graph)
        assert len(graph) > 0

    def test_scan_with_patterns(self, temp_workspace):
        """Test scanning with specific patterns."""
        # Only scan top-level
        graph = yurtle_rdflib.scan_workspace_graph(
            temp_workspace,
            patterns=["*.md"]
        )

        assert len(graph) > 0


class TestNamespaces:
    """Tests for namespace handling."""

    def test_standard_namespaces(self):
        """Test that standard namespaces are available."""
        assert yurtle_rdflib.YURTLE is not None
        assert yurtle_rdflib.PM is not None
        assert yurtle_rdflib.BEING is not None
        assert yurtle_rdflib.VOYAGE is not None
        assert yurtle_rdflib.KNOWLEDGE is not None
        assert yurtle_rdflib.PROVENANCE is not None

    def test_bind_standard_namespaces(self):
        """Test binding standard namespaces to a graph."""
        graph = Graph()
        yurtle_rdflib.bind_standard_namespaces(graph)

        # Check namespaces are bound
        namespaces = dict(graph.namespaces())
        assert 'yurtle' in namespaces
        assert 'pm' in namespaces
        assert 'rdf' in namespaces

    def test_namespace_uris(self):
        """Test namespace URIs are correct."""
        assert str(yurtle_rdflib.YURTLE) == "https://yurtle.dev/schema/"
        assert str(yurtle_rdflib.PM) == "https://yurtle.dev/pm/"


class TestVerifyPlugins:
    """Tests for plugin verification."""

    def test_verify_plugins(self):
        """Test verify_plugins function."""
        status = yurtle_rdflib.verify_plugins()

        assert "parser" in status
        assert "serializer" in status
        assert "version" in status
        assert status["parser"] is True
        assert status["serializer"] is True
        assert status["version"] == yurtle_rdflib.__version__
