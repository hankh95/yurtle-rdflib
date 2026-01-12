# yurtle-rdflib

[![PyPI version](https://badge.fury.io/py/yurtle-rdflib.svg)](https://badge.fury.io/py/yurtle-rdflib)
[![Python versions](https://img.shields.io/pypi/pyversions/yurtle-rdflib.svg)](https://pypi.org/project/yurtle-rdflib/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/hankh95/yurtle-rdflib/actions/workflows/ci.yml/badge.svg)](https://github.com/hankh95/yurtle-rdflib/actions/workflows/ci.yml)

RDFlib plugin for [Yurtle format](https://github.com/hankh95/yurtle) - Markdown files with Turtle/YAML frontmatter that form a queryable knowledge graph.

## What is Yurtle?

Yurtle (YAML/RDF + Turtle) is a file format that combines:
- **Markdown content** for human-readable documentation
- **Turtle or YAML frontmatter** for machine-readable RDF triples
- **Yurtle blocks** for inline structured data anywhere in the document

This enables every `.md` file to be both a document AND a node in a knowledge graph.

```markdown
---
yurtle: v1.3
id: nautical-project/ship
type: asset
title: Clipper Windchaser
relates-to:
  - nautical-project/voyage
  - nautical-project/crew
nugget: 1852 three-masted clipper - fastest trade-wind runner in the fleet
---

# Windchaser

Built in Aberdeen, copper-sheathed, Baltimore clipper lines.

` ` `yurtle
ship:
  name: Windchaser
  built: 1852
  length: 62m
  captain: crew-captain-reed
` ` `

She has outrun typhoons and carried tea from Canton in 79 days.
```

*(Remove spaces in fence markers above - shown for display)*

## Why Integrate Yurtle with RDFlib?

Yurtle files are human-readable and LLM-friendly on their own. So why add RDFlib?

### 1. **SPARQL Queries Across Your Entire Workspace**

Without RDFlib, finding "all lab tests related to diabetes" means writing custom code to parse each file. With RDFlib:

```python
graph.query("""
    SELECT ?test ?loinc WHERE {
        ?test med:clinicalUse ?use .
        FILTER(CONTAINS(?use, "diabetes"))
    }
""")
```

One query. Any complexity. Aggregations, joins, filters, graph traversal — all built-in.

### 2. **Interoperability with Standard Vocabularies**

RDFlib connects your Yurtle files to the wider semantic web:
- **LOINC** for laboratory tests
- **SNOMED-CT** for medical terminology
- **Schema.org** for web content
- **Dublin Core** for document metadata
- Any RDF vocabulary you need

### 3. **Bidirectional Sync: Files ↔ Graph**

Edit files in your favorite editor (Obsidian, VSCode, vim) — the graph updates.
Modify the graph programmatically — files update automatically.

```python
kb = create_live_graph("workspace/", auto_flush=True)
kb.add((subject, predicate, object))  # File written immediately
```

### 4. **Provenance Tracking**

Every triple knows where it came from:

```python
# Find which file defines a concept
graph.query("""
    SELECT ?file WHERE {
        ?concept yurtle:title "Diabetes" .
        ?concept prov:definedIn ?file .
    }
""")
```

### 5. **LLM + Structured Queries = Best of Both**

- **LLMs** excel at understanding prose and answering open-ended questions
- **SPARQL** excels at precise, repeatable, complex queries

Use both: LLMs read the markdown content, SPARQL queries the structured data.

### 6. **No Database Required**

Your knowledge graph is just markdown files in a folder:
- Version control with Git
- Edit anywhere
- No server to maintain
- Works offline

## Installation

```bash
pip install yurtle-rdflib
```

## Quick Start

### Parse a Yurtle file

```python
from rdflib import Graph
import yurtle_rdflib  # Registers the plugin

# Parse a single file
graph = Graph()
graph.parse("document.md", format="yurtle")

# Query with SPARQL
results = graph.query("""
    SELECT ?title ?status WHERE {
        ?task yurtle:title ?title ;
              pm:status ?status .
    }
""")
```

### Load an entire workspace

```python
import yurtle_rdflib

# Load all .md files in a directory
graph = yurtle_rdflib.load_workspace("my-project/")

# Query across all documents
results = graph.query("""
    SELECT ?doc ?title WHERE {
        ?doc yurtle:title ?title .
    }
""")
```

### Serialize to Yurtle format

```python
from rdflib import Graph, URIRef, Literal
import yurtle_rdflib

graph = Graph()
graph.add((
    URIRef("urn:task:T-001"),
    yurtle_rdflib.YURTLE.title,
    Literal("My Task")
))

# Serialize with markdown content
graph.serialize(
    "output.md",
    format="yurtle",
    markdown_content="# My Task\n\nDescription here..."
)
```

### Live bidirectional sync

```python
import yurtle_rdflib

# Create a graph backed by the filesystem
graph = yurtle_rdflib.create_live_graph("workspace/", auto_flush=True)

# Changes persist immediately to files
graph.add((subject, predicate, object))

# File changes sync automatically
graph.store.sync()
```

## Features

### Parser

- **Turtle frontmatter**: Native RDF parsing
- **YAML frontmatter**: Automatic conversion to RDF triples
- **Provenance tracking**: Each triple knows its source file
- **Works with rdflib**: `graph.parse("file.md", format="yurtle")`

### Serializer

- **Round-trip safe**: Preserves markdown content
- **Clean output**: Filters internal provenance triples
- **Standard prefixes**: Auto-binds common namespaces
- **Works with rdflib**: `graph.serialize("file.md", format="yurtle")`

### YurtleStore

- **Bidirectional sync**: Graph ↔ Filesystem
- **Hash-based change detection**: Efficient incremental sync
- **Auto-flush mode**: Immediate persistence
- **SPARQL queries**: Query files as a graph

## Standard Namespaces

```python
from yurtle_rdflib import YURTLE, PM, BEING, VOYAGE, KNOWLEDGE, PROVENANCE

# Use in your graphs
graph.add((subject, YURTLE.title, Literal("My Document")))
graph.add((task, PM.status, Literal("completed")))
```

| Prefix | Namespace | Purpose |
|--------|-----------|---------|
| `yurtle` | `https://yurtle.dev/schema/` | Core document properties |
| `pm` | `https://yurtle.dev/pm/` | Project management |
| `being` | `https://yurtle.dev/being/` | Agent/being properties |
| `voyage` | `https://yurtle.dev/voyage/` | Journey/process tracking |
| `knowledge` | `https://yurtle.dev/knowledge/` | Learning/knowledge |
| `prov` | `https://yurtle.dev/provenance/` | Source file tracking |

## API Reference

### Functions

| Function | Description |
|----------|-------------|
| `load_workspace(path)` | Load all Yurtle files into a unified graph |
| `save_workspace(graph, path)` | Save graph back to workspace files |
| `create_live_graph(path)` | Create store-backed graph with live sync |
| `parse_file(path)` | Parse a single Yurtle file |
| `serialize_file(graph, path)` | Serialize graph to Yurtle file |
| `verify_plugins()` | Check plugin registration status |

### Classes

| Class | Description |
|-------|-------------|
| `YurtleParser` | Core parser for Yurtle documents |
| `YurtleWriter` | Core writer for Yurtle documents |
| `YurtleDocument` | Parsed document with graph + content |
| `YurtleStore` | RDFlib Store for bidirectional sync |
| `YurtleRDFlibParser` | RDFlib Parser plugin |
| `YurtleRDFlibSerializer` | RDFlib Serializer plugin |

## Examples

See the [examples/](examples/) directory for complete workspaces:

- **[nautical-project/](examples/nautical-project/)** - Sailing voyage knowledge graph (from Yurtle spec)
- **[lab-tests/](examples/lab-tests/)** - Medical laboratory tests with LOINC codes
- **[QUERIES.md](examples/QUERIES.md)** - 20+ SPARQL query examples

### Load the Nautical Project

```python
import yurtle_rdflib

# Load the example workspace
graph = yurtle_rdflib.load_workspace("examples/nautical-project/")

# Find all crew members
results = graph.query("""
    PREFIX yurtle: <https://yurtle.dev/schema/>
    SELECT ?person ?name ?role WHERE {
        ?person yurtle:type "person" ;
                yurtle:title ?name .
        OPTIONAL { ?person yurtle:role ?role }
    }
""")

for row in results:
    print(f"{row.name}: {row.role or 'crew'}")
```

### Query Laboratory Tests

```python
import yurtle_rdflib

# Load lab tests
graph = yurtle_rdflib.load_workspace("examples/lab-tests/")

# Find diabetes-related tests
results = graph.query("""
    PREFIX lab: <https://yurtle.dev/lab/>
    PREFIX med: <https://yurtle.dev/medical/>
    PREFIX yurtle: <https://yurtle.dev/schema/>

    SELECT ?test ?title ?loinc WHERE {
        ?test a lab:LaboratoryTest ;
              yurtle:title ?title ;
              lab:loincCode ?loinc ;
              med:clinicalUse ?use .
        FILTER(CONTAINS(LCASE(?use), "diabetes"))
    }
""")

for row in results:
    print(f"{row.title} (LOINC {row.loinc})")
```

### Advanced: Graph Traversal

```python
# Find all items related to the voyage (2 hops)
results = graph.query("""
    PREFIX yurtle: <https://yurtle.dev/schema/>

    SELECT ?item ?title ?path WHERE {
        ?voyage yurtle:title "Voyage to the Sapphire Isles" .
        {
            ?voyage yurtle:relatesTo ?item .
            BIND("direct" as ?path)
        }
        UNION
        {
            ?voyage yurtle:relatesTo ?middle .
            ?middle yurtle:relatesTo ?item .
            BIND("via " + STR(?middle) as ?path)
        }
        ?item yurtle:title ?title .
    }
""")
```

### Advanced: Aggregation

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

for row in results:
    print(f"{row.type}: {row.count}")
```

### Live Sync with Filesystem

```python
import yurtle_rdflib
from rdflib import URIRef, Literal

# Create live-synced knowledge base
kb = yurtle_rdflib.create_live_graph("my-workspace/", auto_flush=True)

# Add knowledge (persists immediately to files)
kb.add((
    URIRef("urn:concept:python"),
    yurtle_rdflib.KNOWLEDGE.relatedTo,
    URIRef("urn:concept:programming")
))

# Changes in files sync back automatically
kb.store.sync()
```

## Yurtle Format Specification

See the [Yurtle Specification](https://github.com/hankh95/yurtle) for the full format documentation.

### Supported Frontmatter Types

**Turtle (recommended)**:
```markdown
---
@prefix yurtle: <https://yurtle.dev/schema/> .

<urn:doc:example> a yurtle:Document ;
    yurtle:title "Example" .
---
```

**YAML (auto-converted)**:
```markdown
---
id: example
title: Example
type: document
tags: [example, demo]
---
```

## Development

```bash
# Clone the repo
git clone https://github.com/hankh95/yurtle-rdflib.git
cd yurtle-rdflib

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=yurtle_rdflib

# Format code
black src tests
ruff check src tests
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Related Projects

- [Yurtle Specification](https://github.com/hankh95/yurtle) - The Yurtle format spec
- [RDFlib](https://github.com/RDFLib/rdflib) - Python RDF library
