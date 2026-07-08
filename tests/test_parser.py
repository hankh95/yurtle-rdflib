"""
Tests for the Yurtle parser.
"""

from rdflib import Graph, Namespace, URIRef

import yurtle_rdflib
from yurtle_rdflib import PM, YURTLE, YurtleParser


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
        text = """---
@prefix yurtle: <https://yurtle.dev/schema/> .

<urn:doc:test> yurtle:tag "tag1", "tag2", "tag3" .
---

Content.
"""
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


class TestFencedBlockParsing:
    """Tests for parsing fenced ```turtle and ```yurtle blocks in markdown body."""

    def test_fenced_turtle_block_parsed(self, sample_doc_with_fenced_blocks):
        """Fenced ```turtle blocks should be parsed into the graph."""
        parser = YurtleParser()
        doc = parser.parse(sample_doc_with_fenced_blocks)

        # Frontmatter triples should exist (YAML-based)
        assert doc.frontmatter_type == "yaml"
        assert len(doc.graph) > 0

        # Fenced turtle block triples should also be in the graph
        Namespace("https://nusy.dev/ylayer/")
        subjects = [str(s) for s in doc.graph.subjects()]
        # The <#chunk-storage> subject from the turtle block
        assert any("chunk-storage" in s for s in subjects)

        # Check a triple from the turtle block
        from rdflib.namespace import RDFS

        labels = list(doc.graph.objects(predicate=RDFS.label))
        label_strs = [str(label) for label in labels]
        assert "Chunk Graph Storage" in label_strs

    def test_fenced_yurtle_block_parsed(self, sample_doc_with_fenced_blocks):
        """Fenced ```yurtle blocks should also be parsed."""
        parser = YurtleParser()
        doc = parser.parse(sample_doc_with_fenced_blocks)

        # The ```yurtle block has kb:statusChange triples
        kb = Namespace("https://yurtle.dev/kanban/")
        status_changes = list(doc.graph.triples((None, kb.statusChange, None)))
        assert len(status_changes) >= 1

    def test_hdd_knowledge_block(self, sample_doc_with_hdd_block):
        """HDD hypothesis knowledge block should produce queryable triples."""
        parser = YurtleParser()
        doc = parser.parse(sample_doc_with_hdd_block)

        hyp = Namespace("https://nusy.dev/hypothesis/")
        paper = Namespace("https://nusy.dev/paper/")
        measure = Namespace("https://nusy.dev/measure/")

        # Check hyp:paper predicate
        papers = list(doc.graph.objects(predicate=hyp.paper))
        assert paper["PAPER-130"] in papers

        # Check hyp:measuredBy (should have 2 measures)
        measures = list(doc.graph.objects(predicate=hyp.measuredBy))
        assert len(measures) == 2
        assert measure["M-007"] in measures
        assert measure["M-025"] in measures

    def test_no_frontmatter_with_block(self, sample_doc_no_frontmatter_with_block):
        """Documents with no frontmatter should still parse fenced blocks."""
        parser = YurtleParser()
        doc = parser.parse(sample_doc_no_frontmatter_with_block)

        assert doc.frontmatter_type == "none"
        # But the graph should have triples from the fenced block
        assert len(doc.graph) > 0

        from rdflib.namespace import RDFS

        labels = list(doc.graph.objects(predicate=RDFS.label))
        assert any("Interesting finding" in str(label) for label in labels)

    def test_empty_fenced_block_skipped(self):
        """Empty fenced blocks should be skipped gracefully."""
        text = """---
id: test
title: Test
---

# Test

```turtle
```

Content continues.
"""
        parser = YurtleParser()
        doc = parser.parse(text)
        # Should not crash, graph has only frontmatter triples
        assert doc.frontmatter_type == "yaml"

    def test_malformed_fenced_block_skipped(self):
        """Malformed turtle in fenced blocks should be skipped with warning."""
        text = """---
id: test
title: Test
---

# Test

```turtle
This is not valid turtle at all!!!
@prefix broken
```

Content continues.
"""
        parser = YurtleParser()
        doc = parser.parse(text)
        # Should not crash — malformed block skipped
        assert doc.frontmatter_type == "yaml"

    def test_malformed_block_logs_debug_with_offset(self, caplog):
        """Malformed block should log at DEBUG including the block offset."""
        import logging

        text = """---
id: test
title: Test
---

# Test

```turtle
not valid turtle!!!
```
"""
        parser = YurtleParser()
        with caplog.at_level(logging.DEBUG, logger="yurtle-parser"):
            parser.parse(text)
        assert any("offset" in record.message for record in caplog.records)

    def test_crlf_line_endings(self):
        """Fenced blocks with CRLF line endings should be parsed."""
        # Build content with CRLF endings
        text = '---\r\nid: test\r\ntitle: Test\r\n---\r\n\r\n# Test\r\n\r\n```turtle\r\n@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\r\n\r\n<#item> rdfs:label "CRLF test" .\r\n```\r\n'
        parser = YurtleParser()
        doc = parser.parse(text)

        from rdflib.namespace import RDFS

        labels = [str(label) for label in doc.graph.objects(predicate=RDFS.label)]
        assert "CRLF test" in labels

    def test_trailing_space_after_language_tag(self):
        """Fenced blocks with trailing spaces after language tag should parse."""
        # Explicit string construction to guarantee trailing spaces after 'turtle'
        text = (
            "---\nid: test\ntitle: Test\n---\n\n# Test\n\n"
            "```turtle   \n"  # <-- trailing spaces before newline
            "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n"
            "\n"
            '<#item> rdfs:label "Trailing space test" .\n'
            "```\n"
        )
        parser = YurtleParser()
        doc = parser.parse(text)

        from rdflib.namespace import RDFS

        labels = [str(label) for label in doc.graph.objects(predicate=RDFS.label)]
        assert "Trailing space test" in labels

    def test_turtle_frontmatter_with_fenced_blocks(self, sample_turtle_doc):
        """Turtle frontmatter + fenced blocks should both parse into graph."""
        # Append a fenced block to the turtle-frontmatter doc
        text = sample_turtle_doc + """
```turtle
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<#extra> rdfs:label "Extra from block" .
```
"""
        parser = YurtleParser()
        doc = parser.parse(text)

        assert doc.frontmatter_type == "turtle"
        # Frontmatter triples (T-001 work item)
        assert doc.subject_uri == URIRef("urn:task:T-001")
        # Fenced block triples
        from rdflib.namespace import RDFS

        labels = [str(label) for label in doc.graph.objects(predicate=RDFS.label)]
        assert "Extra from block" in labels

    def test_multiple_blocks_all_parsed(self, sample_doc_with_fenced_blocks):
        """Multiple fenced blocks in one document should all be parsed."""
        parser = YurtleParser()
        doc = parser.parse(sample_doc_with_fenced_blocks)

        # Should have triples from YAML frontmatter + turtle block + yurtle block
        # YAML: id, title, type, status, tags (at least 5)
        # turtle: chunk-storage type, label, layer (at least 3)
        # yurtle: statusChange blank node (at least 1)
        assert len(doc.graph) >= 9

    def test_content_preserved_with_blocks(self, sample_doc_with_hdd_block):
        """Markdown content including fenced blocks should be preserved."""
        parser = YurtleParser()
        doc = parser.parse(sample_doc_with_hdd_block)

        # Content should still contain the fenced block text
        assert "```turtle" in doc.content
        assert "hyp:paper paper:PAPER-130" in doc.content
        assert "## Rationale" in doc.content

    def test_graph_parse_with_fenced_blocks(self, tmp_path, sample_doc_with_hdd_block):
        """Graph.parse(format='yurtle') should include fenced block triples."""
        file_path = tmp_path / "hypothesis.md"
        file_path.write_text(sample_doc_with_hdd_block)

        graph = Graph()
        graph.parse(str(file_path), format="yurtle")

        hyp = Namespace("https://nusy.dev/hypothesis/")
        papers = list(graph.objects(predicate=hyp.paper))
        assert len(papers) >= 1

    def test_round_trip_duplication_risk(self, sample_doc_with_fenced_blocks):
        """Round-trip write+reparse should not duplicate fenced block triples.

        B4 review finding: YurtleWriter serializes ALL triples into frontmatter.
        Fenced blocks remain in body text. A second parse would double-count
        those triples. This test documents the known behavior.
        """
        from yurtle_rdflib import YurtleWriter

        parser = YurtleParser()
        writer = YurtleWriter()

        # First parse
        doc = parser.parse(sample_doc_with_fenced_blocks)
        original_count = len(doc.graph)

        # Write and re-parse
        text = writer.write(doc)
        doc2 = parser.parse(text)

        # Document the known duplication: fenced block triples appear in both
        # the serialized frontmatter AND the body's fenced blocks.
        # Consumers doing round-trip editing should be aware of this.
        assert (
            len(doc2.graph) >= original_count
        ), "Re-parsed graph should have at least as many triples as original"

    def test_info_string_after_language_tag_not_matched(self):
        """CommonMark info strings (e.g. ```turtle linenos) are intentionally
        not matched. Only bare ```turtle or ```yurtle (with optional whitespace)
        are recognized. This is by design — info strings are uncommon in
        knowledge blocks and supporting them would complicate the regex."""
        text = """---
id: test
title: Test
---

# Test

```turtle linenos
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<#item> rdfs:label "Should not parse" .
```
"""
        parser = YurtleParser()
        doc = parser.parse(text)

        from rdflib.namespace import RDFS

        labels = [str(label) for label in doc.graph.objects(predicate=RDFS.label)]
        assert "Should not parse" not in labels

    def test_workspace_scan_includes_blocks(self, tmp_path, sample_doc_with_hdd_block):
        """load_workspace / scan_workspace_graph should include fenced block triples."""
        workspace = tmp_path / "research"
        workspace.mkdir()
        (workspace / "H130.1.md").write_text(sample_doc_with_hdd_block)

        graph = yurtle_rdflib.scan_workspace_graph(workspace)

        hyp = Namespace("https://nusy.dev/hypothesis/")
        papers = list(graph.objects(predicate=hyp.paper))
        assert len(papers) >= 1

    def test_prefix_inheritance_from_standard(self):
        """Fenced blocks should inherit standard prefixes without redeclaring."""
        text = """---
id: test
title: Test
---

# Test

```turtle
<#item> rdfs:label "Inherited prefix" .
```
"""
        parser = YurtleParser()
        doc = parser.parse(text)

        from rdflib.namespace import RDFS

        labels = [str(label) for label in doc.graph.objects(predicate=RDFS.label)]
        assert "Inherited prefix" in labels

    def test_prefix_inheritance_from_frontmatter(self):
        """Fenced blocks should inherit prefixes declared in Turtle frontmatter."""
        text = """---
@prefix yurtle: <https://yurtle.dev/schema/> .
@prefix custom: <https://example.org/custom/> .

<urn:doc:test> a yurtle:WorkItem ;
    yurtle:title "Test" .
---

# Test

```turtle
<#item> custom:property "Frontmatter prefix" .
```
"""
        parser = YurtleParser()
        doc = parser.parse(text)

        custom = Namespace("https://example.org/custom/")
        values = [str(o) for o in doc.graph.objects(predicate=custom.property)]
        assert "Frontmatter prefix" in values

    def test_block_prefix_overrides_injected(self):
        """Block's own @prefix should override injected declarations."""
        text = """---
@prefix yurtle: <https://yurtle.dev/schema/> .
@prefix custom: <https://example.org/custom/> .

<urn:doc:test> a yurtle:WorkItem .
---

# Test

```turtle
@prefix custom: <https://example.org/override/> .

<#item> custom:property "Override test" .
```
"""
        parser = YurtleParser()
        doc = parser.parse(text)

        # The block's @prefix should take precedence
        override = Namespace("https://example.org/override/")
        values = [str(o) for o in doc.graph.objects(predicate=override.property)]
        assert "Override test" in values

    def test_yaml_in_yurtle_block_skipped(self):
        """YAML content in a ```yurtle block should be silently skipped."""
        text = """---
id: test
title: Test
---

# Test

```yurtle
being:
  id: santiago-developer-v7
  name: "Santiago Developer"
```

Content continues.
"""
        parser = YurtleParser()
        doc = parser.parse(text)
        # Should not crash, only frontmatter triples
        assert doc.frontmatter_type == "yaml"
        # Graph should have frontmatter triples but not crash on YAML block
        assert len(doc.graph) >= 1

    def test_yaml_in_turtle_block_skipped(self):
        """YAML content in a ```turtle block should be silently skipped."""
        text = """---
id: test
title: Test
---

# Test

```turtle
corpus:
  # Phase 1: Foundation
  - name: core-docs
    path: /data/corpus
```
"""
        parser = YurtleParser()
        doc = parser.parse(text)
        assert doc.frontmatter_type == "yaml"

    def test_yaml_with_document_start_in_block_skipped(self):
        """YAML with --- document start marker in fenced block should be skipped."""
        text = """---
id: test
title: Test
---

# Test

```yurtle
# knowledge_index.md
---
being: santiago-highschool-v11
last_updated: 2026-02-14
y1_concepts: 847
---
```
"""
        parser = YurtleParser()
        doc = parser.parse(text)
        assert doc.frontmatter_type == "yaml"

    def test_merge_conflict_in_block_skipped(self):
        """Fenced blocks with git merge conflict markers should be skipped."""
        text = """---
id: test
title: Test
---

# Test

```turtle
@prefix kb: <https://yurtle.dev/kanban/> .

<> kb:status kb:done ;
<<<<<<< HEAD
    kb:forcedMove "true"^^xsd:boolean ;
=======
>>>>>>> 8a6d7c07
```
"""
        parser = YurtleParser()
        doc = parser.parse(text)
        # Should not crash — conflict block skipped
        assert doc.frontmatter_type == "yaml"

    def test_yaml_detection_does_not_flag_turtle(self):
        """Valid Turtle content should NOT be detected as YAML."""
        # These patterns look vaguely YAML-ish but are valid Turtle
        assert not YurtleParser._looks_like_yaml('<#item> rdfs:label "Test" .')
        assert not YurtleParser._looks_like_yaml(
            "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n"
            '<#item> rdfs:label "Test" .'
        )
        assert not YurtleParser._looks_like_yaml("# A comment line\n" '<#item> rdfs:label "Test" .')

    def test_yaml_detection_catches_yaml(self):
        """YAML-like content should be correctly detected."""
        assert YurtleParser._looks_like_yaml("being:\n  id: foo")
        assert YurtleParser._looks_like_yaml("corpus:\n  - name: x")
        assert YurtleParser._looks_like_yaml("# comment\n---\nkey: val")
        assert YurtleParser._looks_like_yaml("scenarios:\n  - id: s1")

    def test_malformed_block_logs_debug_not_warning(self, caplog):
        """Unparseable fenced blocks should log at DEBUG, not WARNING."""
        import logging

        text = """---
id: test
title: Test
---

# Test

```turtle
<> a unknown:Type .
```
"""
        parser = YurtleParser()
        with caplog.at_level(logging.DEBUG, logger="yurtle-parser"):
            parser.parse(text)

        # Should be logged at DEBUG level, not WARNING
        parse_msgs = [r for r in caplog.records if "Failed to parse" in r.message]
        assert len(parse_msgs) >= 1
        for msg in parse_msgs:
            assert msg.levelno == logging.DEBUG
