# Examples

This directory contains example Yurtle workspaces demonstrating different use cases.

## Directories

### [nautical-project/](nautical-project/)

The flagship example from the [Yurtle spec](https://github.com/hankh95/yurtle) - a complete knowledge graph for a sailing voyage:

- **voyage.md** - The main project with status tracking
- **ship.md** - Asset with yurtle blocks for structured data
- **crew.md** - Group with parent/children hierarchy
- **crew-captain-reed.md** - Person with relationships
- **manifest.md** - Inventory tracking
- **logbook-2025-12.md** - Temporal entries

**Demonstrates:**
- Three-layer model (frontmatter, wiki-links, yurtle blocks)
- Hierarchical relationships (parent/children)
- YAML frontmatter format

### [lab-tests/](lab-tests/)

Medical laboratory tests with LOINC codes and reference ranges:

- **complete-blood-count.md** - CBC panel (LOINC 58410-2)
- **hemoglobin-a1c.md** - HbA1c diabetes marker (LOINC 4548-4)
- **lipid-panel.md** - Cholesterol panel (LOINC 57698-3)
- **basic-metabolic-panel.md** - BMP electrolytes (LOINC 51990-0)

**Demonstrates:**
- Turtle frontmatter format with full RDF
- Rich medical vocabulary (LOINC, SNOMED)
- Yurtle blocks for test components
- Real-world reference data

---

## Quick Start

```python
import yurtle_rdflib

# Load the nautical project
graph = yurtle_rdflib.load_workspace("examples/nautical-project/")
print(f"Loaded {len(graph)} triples")

# Load lab tests
lab_graph = yurtle_rdflib.load_workspace("examples/lab-tests/")
print(f"Loaded {len(lab_graph)} triples from lab tests")
```

---

## Example Queries

See [QUERIES.md](QUERIES.md) for comprehensive SPARQL examples.

### Basic: Find all documents

```python
results = graph.query("""
    PREFIX yurtle: <https://yurtle.dev/schema/>
    SELECT ?doc ?title WHERE {
        ?doc yurtle:title ?title .
    }
""")
for row in results:
    print(f"{row.doc}: {row.title}")
```

### Intermediate: Follow relationships

```python
# Find what the ship is part of
results = graph.query("""
    PREFIX yurtle: <https://yurtle.dev/schema/>
    SELECT ?ship ?voyage WHERE {
        ?ship yurtle:title "Clipper Windchaser" ;
              yurtle:relatesTo ?voyage .
        ?voyage a yurtle:project .
    }
""")
```

### Advanced: Aggregate statistics

```python
# Count documents by type
results = graph.query("""
    PREFIX yurtle: <https://yurtle.dev/schema/>
    SELECT ?type (COUNT(?doc) as ?count) WHERE {
        ?doc yurtle:type ?type .
    }
    GROUP BY ?type
    ORDER BY DESC(?count)
""")
```
