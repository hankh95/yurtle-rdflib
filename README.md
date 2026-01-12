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

This enables every `.md` file to be both a document AND a node in a knowledge graph.

```markdown
---
@prefix yurtle: <https://yurtle.dev/schema/> .
@prefix pm: <https://yurtle.dev/pm/> .

<urn:task:F-048> a yurtle:WorkItem ;
    pm:status "in-progress" ;
    pm:priority 2 ;
    yurtle:title "Production Hardening" .
---

# F-048: Production Hardening

Human-readable content here...
```

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

### Task Management System

```python
import yurtle_rdflib
from rdflib import URIRef, Literal

# Load all tasks
graph = yurtle_rdflib.load_workspace("tasks/")

# Find incomplete tasks
results = graph.query("""
    PREFIX pm: <https://yurtle.dev/pm/>
    SELECT ?task ?title WHERE {
        ?task pm:status "pending" ;
              yurtle:title ?title .
    }
""")

for row in results:
    print(f"TODO: {row.title}")
```

### Knowledge Base

```python
import yurtle_rdflib

# Create live-synced knowledge base
kb = yurtle_rdflib.create_live_graph("knowledge/", auto_flush=True)

# Add knowledge (persists immediately)
kb.add((
    URIRef("urn:concept:python"),
    yurtle_rdflib.KNOWLEDGE.relatedTo,
    URIRef("urn:concept:programming")
))

# Query relationships
results = kb.query("""
    SELECT ?concept ?related WHERE {
        ?concept knowledge:relatedTo ?related .
    }
""")
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
