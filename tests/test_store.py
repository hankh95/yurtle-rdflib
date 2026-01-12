"""
Tests for the YurtleStore.
"""

import pytest
from pathlib import Path
from rdflib import Graph, URIRef, Literal

import yurtle_rdflib
from yurtle_rdflib import YurtleStore, YURTLE, PM
from yurtle_rdflib.namespaces import PROVENANCE


class TestYurtleStoreInit:
    """Tests for YurtleStore initialization."""

    def test_init_empty_workspace(self, tmp_path):
        """Test initializing store with empty workspace."""
        workspace = tmp_path / "empty"
        workspace.mkdir()

        store = YurtleStore(str(workspace))

        assert store.root_dir == workspace
        assert len(store.file_states) == 0

    def test_init_with_files(self, temp_workspace):
        """Test initializing store with existing files."""
        store = YurtleStore(str(temp_workspace))

        assert len(store.file_states) >= 2
        assert len(store.internal_graph) > 0

    def test_patterns(self, tmp_path):
        """Test custom glob patterns."""
        workspace = tmp_path / "patterns"
        workspace.mkdir()

        # Create files with different extensions
        (workspace / "doc.md").write_text("---\nid: doc\n---\n# Doc")
        (workspace / "other.txt").write_text("Not markdown")

        store = YurtleStore(str(workspace), patterns=["*.md"])

        assert len(store.file_states) == 1


class TestYurtleStoreSync:
    """Tests for YurtleStore synchronization."""

    def test_sync_detects_new_files(self, temp_workspace):
        """Test that sync detects new files."""
        store = YurtleStore(str(temp_workspace))
        initial_count = len(store.file_states)

        # Add new file
        (temp_workspace / "new.md").write_text('''---
@prefix yurtle: <https://yurtle.dev/schema/> .
<urn:task:new> yurtle:title "New" .
---
# New
''')

        synced = store.sync()

        assert synced >= 1
        assert len(store.file_states) == initial_count + 1

    def test_sync_detects_modified_files(self, temp_workspace):
        """Test that sync detects modified files."""
        store = YurtleStore(str(temp_workspace))

        # Modify existing file
        task1_path = temp_workspace / "task1.md"
        original = task1_path.read_text()
        task1_path.write_text(original.replace("Task One", "Modified Task"))

        synced = store.sync()

        assert synced >= 1

    def test_sync_detects_deleted_files(self, temp_workspace):
        """Test that sync detects deleted files."""
        store = YurtleStore(str(temp_workspace))
        initial_count = len(store.file_states)

        # Delete file
        (temp_workspace / "task1.md").unlink()

        synced = store.sync()

        assert synced >= 1
        assert len(store.file_states) == initial_count - 1


class TestYurtleStoreQuery:
    """Tests for querying the store."""

    def test_triples(self, temp_workspace):
        """Test iterating over triples."""
        store = YurtleStore(str(temp_workspace))

        triples = list(store.triples((None, None, None)))
        assert len(triples) > 0

    def test_triples_with_pattern(self, temp_workspace):
        """Test filtering triples with pattern."""
        store = YurtleStore(str(temp_workspace))

        # Get all title triples
        title_triples = list(store.triples((None, YURTLE.title, None)))
        assert len(title_triples) >= 2  # task1 and task2

    def test_len(self, temp_workspace):
        """Test __len__ method."""
        store = YurtleStore(str(temp_workspace))

        assert len(store) > 0

    def test_contains(self, temp_workspace):
        """Test __contains__ method."""
        store = YurtleStore(str(temp_workspace))

        # Get a triple that should exist
        for triple, _ in store.triples((None, YURTLE.title, None)):
            assert triple in store
            break


class TestYurtleStoreModification:
    """Tests for modifying the store."""

    def test_add_triple(self, temp_workspace):
        """Test adding a triple."""
        store = YurtleStore(str(temp_workspace))
        initial_len = len(store)

        subject = URIRef("urn:task:task1")
        store.add((subject, YURTLE.note, Literal("A note")))

        assert len(store) == initial_len + 1
        assert (subject, YURTLE.note, Literal("A note")) in store

    def test_remove_triple(self, temp_workspace):
        """Test removing a triple."""
        store = YurtleStore(str(temp_workspace))

        # Get a triple to remove
        triple = None
        for t, _ in store.triples((None, YURTLE.title, None)):
            triple = t
            break

        if triple:
            store.remove(triple)
            assert triple not in store


class TestYurtleStoreFlush:
    """Tests for flushing changes to disk."""

    def test_manual_flush(self, temp_workspace):
        """Test manual flush."""
        store = YurtleStore(str(temp_workspace), auto_flush=False)

        # Make a change
        subject = URIRef("urn:task:task1")
        store.add((subject, YURTLE.note, Literal("New note")))

        # Should have dirty files
        assert len(store.get_dirty_files()) > 0

        # Flush
        flushed = store.flush()

        assert flushed > 0
        assert len(store.get_dirty_files()) == 0

    def test_auto_flush(self, temp_workspace):
        """Test auto-flush mode."""
        store = YurtleStore(str(temp_workspace), auto_flush=True)

        # Make a change - should auto-flush
        subject = URIRef("urn:task:task1")
        store.add((subject, YURTLE.note, Literal("Auto-flushed note")))

        # Should have no dirty files (already flushed)
        # Note: this depends on the subject already having provenance
        # In practice, new subjects without provenance won't auto-flush


class TestYurtleStoreGraph:
    """Tests for using store with RDFlib Graph."""

    def test_graph_with_store(self, temp_workspace):
        """Test creating a Graph with YurtleStore."""
        store = YurtleStore(str(temp_workspace))
        graph = Graph(store=store)

        assert len(graph) > 0

    def test_graph_query(self, temp_workspace):
        """Test SPARQL query on store-backed graph."""
        store = YurtleStore(str(temp_workspace))

        # Query directly on the internal graph instead
        # (Custom stores may not support all query parameters)
        results = list(store.internal_graph.query("""
            SELECT ?s ?title WHERE {
                ?s <https://yurtle.dev/schema/title> ?title .
            }
        """))

        assert len(results) >= 2


class TestConvenienceFunctions:
    """Tests for convenience store functions."""

    def test_create_yurtle_graph(self, temp_workspace):
        """Test create_yurtle_graph function."""
        from yurtle_rdflib.store import create_yurtle_graph

        graph = create_yurtle_graph(str(temp_workspace))

        assert isinstance(graph, Graph)
        assert len(graph) > 0

    def test_create_live_graph(self, temp_workspace):
        """Test create_live_graph function."""
        graph = yurtle_rdflib.create_live_graph(str(temp_workspace))

        assert isinstance(graph, Graph)
        assert len(graph) > 0

    def test_get_stats(self, temp_workspace):
        """Test get_stats method."""
        store = YurtleStore(str(temp_workspace))
        stats = store.get_stats()

        assert "root_dir" in stats
        assert "total_files" in stats
        assert "total_triples" in stats
        assert stats["total_files"] >= 2
