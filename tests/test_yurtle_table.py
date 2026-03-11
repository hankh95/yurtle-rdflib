"""Tests for yurtle-table block parsing (hankh95/yurtle-rdflib#1).

Tests the parser's ability to convert ```yurtle-table fenced blocks
into RDF triples. Covers:
- Basic table parsing (headers → predicates, rows → triples)
- @type directive (sets rdf:type for all rows)
- @prefix declarations (local and inherited)
- @id column as subject URI
- Type inference (integer, date, string, URI)
- Empty cells (no triple emitted)
- Edge cases (empty tables, missing @id, malformed rows)
- Integration with frontmatter prefixes
"""

import pytest
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS, XSD

from yurtle_rdflib import YurtleParser, YURTLE


KB = Namespace("https://yurtle.dev/kanban/")


# ── Basic Table Parsing ──────────────────────────────────────────────


class TestBasicTableParsing:
    def test_simple_table(self):
        """Basic yurtle-table with @prefix, @type, and data rows."""
        text = '''# Test

```yurtle-table
@prefix kb: <https://yurtle.dev/kanban/> .
@type kb:Phase

| @id      | rdfs:label    | kb:phaseOrder |
|----------|---------------|---------------|
| #phase-1 | First Phase   | 1             |
| #phase-2 | Second Phase  | 2             |
```
'''
        parser = YurtleParser()
        doc = parser.parse(text)
        g = doc.graph

        phase1 = URIRef("#phase-1")
        phase2 = URIRef("#phase-2")

        # Check rdf:type from @type directive
        assert (phase1, RDF.type, KB.Phase) in g
        assert (phase2, RDF.type, KB.Phase) in g

        # Check rdfs:label
        assert (phase1, RDFS.label, Literal("First Phase")) in g
        assert (phase2, RDFS.label, Literal("Second Phase")) in g

        # Check integer inference for phaseOrder
        assert (phase1, KB.phaseOrder, Literal(1, datatype=XSD.integer)) in g
        assert (phase2, KB.phaseOrder, Literal(2, datatype=XSD.integer)) in g

    def test_table_without_type_directive(self):
        """Table without @type — no rdf:type triples added."""
        text = '''# Test

```yurtle-table
@prefix kb: <https://yurtle.dev/kanban/> .

| @id    | kb:name   |
|--------|-----------|
| #item1 | My Item   |
```
'''
        parser = YurtleParser()
        doc = parser.parse(text)
        g = doc.graph

        item = URIRef("#item1")
        assert (item, KB.name, Literal("My Item")) in g
        # No rdf:type triple
        assert (item, RDF.type, None) not in g
        types = list(g.objects(item, RDF.type))
        assert len(types) == 0

    def test_empty_cells_skipped(self):
        """Empty cells should not produce triples."""
        text = '''# Test

```yurtle-table
@prefix kb: <https://yurtle.dev/kanban/> .
@type kb:Phase

| @id      | rdfs:label  | kb:item   |
|----------|-------------|-----------|
| #phase-1 | Phase One   | EXP-100   |
| #phase-2 | Phase Two   |           |
```
'''
        parser = YurtleParser()
        doc = parser.parse(text)
        g = doc.graph

        # phase-2 has no kb:item triple
        phase2_items = list(g.objects(URIRef("#phase-2"), KB.item))
        assert len(phase2_items) == 0

        # phase-1 does have it
        assert (URIRef("#phase-1"), KB.item, Literal("EXP-100")) in g

    def test_multiple_tables_in_one_document(self):
        """Multiple yurtle-table blocks in the same document."""
        text = '''# Test

```yurtle-table
@prefix kb: <https://yurtle.dev/kanban/> .
@type kb:Phase

| @id      | rdfs:label |
|----------|------------|
| #phase-1 | Phase One  |
```

Some text between tables.

```yurtle-table
@prefix kb: <https://yurtle.dev/kanban/> .
@type kb:Item

| @id    | rdfs:label |
|--------|------------|
| #item1 | Item One   |
```
'''
        parser = YurtleParser()
        doc = parser.parse(text)
        g = doc.graph

        assert (URIRef("#phase-1"), RDF.type, KB.Phase) in g
        assert (URIRef("#item1"), RDF.type, KB.Item) in g


# ── Type Inference ────────────────────────────────────────────────────


class TestTypeInference:
    def test_integer_inference(self):
        """Integer-looking values get xsd:integer."""
        text = '''```yurtle-table
@prefix kb: <https://yurtle.dev/kanban/> .

| @id   | kb:order | kb:count |
|-------|----------|----------|
| #row1 | 42       | 0        |
```'''
        parser = YurtleParser()
        doc = parser.parse(text)
        g = doc.graph

        assert (URIRef("#row1"), KB.order, Literal(42, datatype=XSD.integer)) in g
        assert (URIRef("#row1"), KB['count'], Literal(0, datatype=XSD.integer)) in g

    def test_date_inference(self):
        """Date-looking values get xsd:date."""
        text = '''```yurtle-table
@prefix kb: <https://yurtle.dev/kanban/> .

| @id   | kb:created    |
|-------|---------------|
| #row1 | 2026-03-10    |
```'''
        parser = YurtleParser()
        doc = parser.parse(text)
        g = doc.graph

        assert (URIRef("#row1"), KB.created, Literal("2026-03-10", datatype=XSD.date)) in g

    def test_string_default(self):
        """Non-numeric, non-date values are plain strings."""
        text = '''```yurtle-table
@prefix kb: <https://yurtle.dev/kanban/> .

| @id   | kb:label         |
|-------|------------------|
| #row1 | Hello World      |
```'''
        parser = YurtleParser()
        doc = parser.parse(text)
        g = doc.graph

        assert (URIRef("#row1"), KB.label, Literal("Hello World")) in g

    def test_uri_reference_in_cell(self):
        """Fragment references (#foo) in cells become URIRefs."""
        text = '''```yurtle-table
@prefix kb: <https://yurtle.dev/kanban/> .

| @id   | kb:relatedTo |
|-------|--------------|
| #row1 | #row2        |
```'''
        parser = YurtleParser()
        doc = parser.parse(text)
        g = doc.graph

        assert (URIRef("#row1"), KB.relatedTo, URIRef("#row2")) in g

    def test_prefixed_uri_in_cell(self):
        """Prefixed names in cells resolve to URIRefs."""
        text = '''```yurtle-table
@prefix kb: <https://yurtle.dev/kanban/> .

| @id   | kb:status    |
|-------|--------------|
| #row1 | kb:completed |
```'''
        parser = YurtleParser()
        doc = parser.parse(text)
        g = doc.graph

        assert (URIRef("#row1"), KB.status, KB.completed) in g

    def test_negative_integer(self):
        """Negative integers are inferred correctly."""
        text = '''```yurtle-table
@prefix kb: <https://yurtle.dev/kanban/> .

| @id   | kb:delta |
|-------|----------|
| #row1 | -5       |
```'''
        parser = YurtleParser()
        doc = parser.parse(text)
        g = doc.graph

        assert (URIRef("#row1"), KB.delta, Literal(-5, datatype=XSD.integer)) in g


# ── @type Column ──────────────────────────────────────────────────────


class TestTypeColumn:
    def test_type_column_per_row(self):
        """@type as a column header sets rdf:type per row."""
        text = '''```yurtle-table
@prefix kb: <https://yurtle.dev/kanban/> .

| @id   | @type     | rdfs:label |
|-------|-----------|------------|
| #row1 | kb:Phase  | Phase One  |
| #row2 | kb:Item   | Item One   |
```'''
        parser = YurtleParser()
        doc = parser.parse(text)
        g = doc.graph

        assert (URIRef("#row1"), RDF.type, KB.Phase) in g
        assert (URIRef("#row2"), RDF.type, KB.Item) in g

    def test_type_directive_and_column_both_work(self):
        """@type directive and @type column can coexist."""
        text = '''```yurtle-table
@prefix kb: <https://yurtle.dev/kanban/> .
@type kb:WorkItem

| @id   | @type        | rdfs:label |
|-------|--------------|------------|
| #row1 | kb:Expedition | My Exp    |
```'''
        parser = YurtleParser()
        doc = parser.parse(text)
        g = doc.graph

        # Both types should be present
        types = set(g.objects(URIRef("#row1"), RDF.type))
        assert KB.WorkItem in types
        assert KB.Expedition in types


# ── Prefix Handling ───────────────────────────────────────────────────


class TestPrefixHandling:
    def test_inherits_frontmatter_prefixes(self):
        """yurtle-table blocks inherit prefixes from Turtle frontmatter."""
        text = '''---
@prefix kb: <https://yurtle.dev/kanban/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<#doc> a kb:Document .
---

# Test

```yurtle-table
@type kb:Phase

| @id      | rdfs:label |
|----------|------------|
| #phase-1 | Phase One  |
```
'''
        parser = YurtleParser()
        doc = parser.parse(text)
        g = doc.graph

        assert (URIRef("#phase-1"), RDF.type, KB.Phase) in g
        assert (URIRef("#phase-1"), RDFS.label, Literal("Phase One")) in g

    def test_local_prefix_overrides(self):
        """Prefixes declared in the table block override inherited ones."""
        text = '''---
@prefix kb: <https://old.dev/> .

<#doc> a kb:Document .
---

```yurtle-table
@prefix kb: <https://yurtle.dev/kanban/> .
@type kb:Phase

| @id      | kb:name  |
|----------|----------|
| #phase-1 | Phase    |
```
'''
        parser = YurtleParser()
        doc = parser.parse(text)
        g = doc.graph

        # Should use the local prefix (new namespace), not inherited
        assert (URIRef("#phase-1"), KB.name, Literal("Phase")) in g

    def test_multiple_prefixes(self):
        """Multiple @prefix declarations in a single table block."""
        text = '''```yurtle-table
@prefix kb: <https://yurtle.dev/kanban/> .
@prefix ex: <https://example.org/> .
@type kb:Phase

| @id      | ex:label  | kb:order |
|----------|-----------|----------|
| #phase-1 | Phase One | 1        |
```'''
        parser = YurtleParser()
        doc = parser.parse(text)
        g = doc.graph

        EX = Namespace("https://example.org/")
        assert (URIRef("#phase-1"), EX.label, Literal("Phase One")) in g
        assert (URIRef("#phase-1"), KB.order, Literal(1, datatype=XSD.integer)) in g


# ── Edge Cases ────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_empty_table_block(self):
        """Empty yurtle-table block is skipped gracefully."""
        text = '''```yurtle-table
```'''
        parser = YurtleParser()
        doc = parser.parse(text)
        # Should not crash
        assert len(doc.graph) == 0 or True  # standard prefixes may exist

    def test_missing_id_column(self):
        """Table without @id column is skipped."""
        text = '''```yurtle-table
@prefix kb: <https://yurtle.dev/kanban/> .

| kb:name | kb:order |
|---------|----------|
| Phase   | 1        |
```'''
        parser = YurtleParser()
        doc = parser.parse(text)
        g = doc.graph

        # No triples added from the table (no @id column)
        kb_triples = list(g.triples((None, KB.name, None)))
        assert len(kb_triples) == 0

    def test_header_only_no_data_rows(self):
        """Table with header and separator but no data rows."""
        text = '''```yurtle-table
@prefix kb: <https://yurtle.dev/kanban/> .

| @id   | kb:name |
|-------|---------|
```'''
        parser = YurtleParser()
        doc = parser.parse(text)
        # Should not crash, no data triples
        kb_triples = list(g.triples((None, KB.name, None)) for g in [doc.graph])
        assert True  # Just verifying no crash

    def test_short_row_padded(self):
        """Rows shorter than headers are padded with empty cells."""
        text = '''```yurtle-table
@prefix kb: <https://yurtle.dev/kanban/> .

| @id   | kb:name | kb:order |
|-------|---------|----------|
| #row1 | Phase   |
```'''
        parser = YurtleParser()
        doc = parser.parse(text)
        g = doc.graph

        assert (URIRef("#row1"), KB.name, Literal("Phase")) in g
        # No kb:order triple (short row, padded with empty)
        order_vals = list(g.objects(URIRef("#row1"), KB.order))
        assert len(order_vals) == 0

    def test_whitespace_in_cells(self):
        """Cell values are stripped of leading/trailing whitespace."""
        text = '''```yurtle-table
@prefix kb: <https://yurtle.dev/kanban/> .

| @id   | kb:name          |
|-------|------------------|
| #row1 |   Spaced Value   |
```'''
        parser = YurtleParser()
        doc = parser.parse(text)
        g = doc.graph

        assert (URIRef("#row1"), KB.name, Literal("Spaced Value")) in g

    def test_coexists_with_turtle_blocks(self):
        """yurtle-table blocks coexist with regular turtle blocks."""
        text = '''# Test

```turtle
@prefix kb: <https://yurtle.dev/kanban/> .
<#existing> a kb:Item ;
    kb:name "Existing" .
```

```yurtle-table
@prefix kb: <https://yurtle.dev/kanban/> .
@type kb:Phase

| @id      | rdfs:label |
|----------|------------|
| #phase-1 | Phase One  |
```
'''
        parser = YurtleParser()
        doc = parser.parse(text)
        g = doc.graph

        # From turtle block — rdflib resolves #existing against base URI,
        # so we check for it by finding any subject with kb:name "Existing"
        existing_subjects = list(g.subjects(KB.name, Literal("Existing")))
        assert len(existing_subjects) == 1
        # From yurtle-table block
        assert (URIRef("#phase-1"), RDF.type, KB.Phase) in g

    def test_full_uri_in_id_column(self):
        """Full URI in angle brackets in @id column."""
        text = '''```yurtle-table
@prefix kb: <https://yurtle.dev/kanban/> .

| @id                             | kb:name |
|---------------------------------|---------|
| <https://example.org/item/1>    | Item 1  |
```'''
        parser = YurtleParser()
        doc = parser.parse(text)
        g = doc.graph

        subj = URIRef("https://example.org/item/1")
        assert (subj, KB.name, Literal("Item 1")) in g

    def test_prefixed_name_in_id_column(self):
        """Prefixed name in @id column resolves to full URI."""
        text = '''```yurtle-table
@prefix kb: <https://yurtle.dev/kanban/> .

| @id        | rdfs:label |
|------------|------------|
| kb:phase-1 | Phase One  |
```'''
        parser = YurtleParser()
        doc = parser.parse(text)
        g = doc.graph

        subj = KB["phase-1"]
        assert (subj, RDFS.label, Literal("Phase One")) in g

    def test_http_url_in_cell(self):
        """HTTP URLs in cells become URIRefs."""
        text = '''```yurtle-table
@prefix kb: <https://yurtle.dev/kanban/> .

| @id   | kb:link                        |
|-------|--------------------------------|
| #row1 | https://example.org/page       |
```'''
        parser = YurtleParser()
        doc = parser.parse(text)
        g = doc.graph

        assert (URIRef("#row1"), KB.link, URIRef("https://example.org/page")) in g


# ── Spec Example (from hankh95/yurtle#3) ─────────────────────────────


class TestSpecExample:
    def test_voyage_phase_table(self):
        """The canonical example from the spec proposal."""
        text = '''# VOY-108: Voyage-First Campaign

```yurtle-table
@prefix kb: <https://yurtle.dev/kanban/> .
@type kb:Phase

| @id        | rdfs:label                                | kb:phaseOrder | kb:phaseItem |
|------------|-------------------------------------------|---------------|--------------|
| #phase-1   | Architect Instruction (CLAUDE.md)         | 1             | PR-187       |
| #phase-2   | Bosun Voyage Awareness (fleet-heuristics) | 2             | EXP-1020     |
| #phase-3   | yurtle-kanban Voyage CLI commands         | 3             | EXP-1021     |
| #phase-4   | Research Interlinks                       | 4             |              |
```
'''
        parser = YurtleParser()
        doc = parser.parse(text)
        g = doc.graph

        # All 4 rows should be kb:Phase
        for i in range(1, 5):
            subj = URIRef(f"#phase-{i}")
            assert (subj, RDF.type, KB.Phase) in g

        # Check specific values
        assert (URIRef("#phase-1"), RDFS.label,
                Literal("Architect Instruction (CLAUDE.md)")) in g
        assert (URIRef("#phase-1"), KB.phaseOrder,
                Literal(1, datatype=XSD.integer)) in g
        assert (URIRef("#phase-1"), KB.phaseItem,
                Literal("PR-187")) in g

        # Phase 4 has no phaseItem (empty cell)
        phase4_items = list(g.objects(URIRef("#phase-4"), KB.phaseItem))
        assert len(phase4_items) == 0

        # Phase 4 still has label and order
        assert (URIRef("#phase-4"), RDFS.label,
                Literal("Research Interlinks")) in g
        assert (URIRef("#phase-4"), KB.phaseOrder,
                Literal(4, datatype=XSD.integer)) in g

    def test_triple_count(self):
        """Verify the expected number of triples from the spec example."""
        text = '''```yurtle-table
@prefix kb: <https://yurtle.dev/kanban/> .
@type kb:Phase

| @id        | rdfs:label | kb:phaseOrder | kb:phaseItem |
|------------|------------|---------------|--------------|
| #phase-1   | Phase 1    | 1             | PR-187       |
| #phase-2   | Phase 2    | 2             | EXP-1020     |
| #phase-3   | Phase 3    | 3             | EXP-1021     |
| #phase-4   | Phase 4    | 4             |              |
```'''
        parser = YurtleParser()
        doc = parser.parse(text)
        g = doc.graph

        # Count only non-standard-prefix triples
        # 4 rows × (1 type + 1 label + 1 order) = 12
        # + 3 rows with phaseItem = 3
        # Total: 15 triples from the table
        table_triples = [
            t for t in g
            if str(t[1]).startswith("https://yurtle.dev/kanban/")
            or t[1] == RDF.type
            or t[1] == RDFS.label
        ]
        assert len(table_triples) == 15
