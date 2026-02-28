"""
Shared pytest fixtures for yurtle-rdflib tests.
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from rdflib import Graph, URIRef, Literal, Namespace

# Import the package to register plugins
import yurtle_rdflib


@pytest.fixture
def yurtle_ns():
    """Return the Yurtle namespace."""
    return yurtle_rdflib.YURTLE


@pytest.fixture
def pm_ns():
    """Return the PM namespace."""
    return yurtle_rdflib.PM


@pytest.fixture
def sample_turtle_doc():
    """Sample Yurtle document with Turtle frontmatter."""
    return '''---
@prefix yurtle: <https://yurtle.dev/schema/> .
@prefix pm: <https://yurtle.dev/pm/> .

<urn:task:T-001> a yurtle:WorkItem ;
    yurtle:title "Test Task" ;
    pm:status "pending" ;
    pm:priority 1 .
---

# T-001: Test Task

This is a test task for unit testing.

## Description

A simple task used in tests.
'''


@pytest.fixture
def sample_yaml_doc():
    """Sample Yurtle document with YAML frontmatter."""
    return '''---
id: T-002
title: YAML Task
status: in-progress
priority: 2
tags:
  - test
  - yaml
---

# T-002: YAML Task

This task uses YAML frontmatter.
'''


@pytest.fixture
def sample_no_frontmatter():
    """Sample document with no frontmatter."""
    return '''# Plain Document

This document has no frontmatter.

Just plain markdown content.
'''


@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary workspace with sample files."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    # Create sample files
    (workspace / "task1.md").write_text('''---
@prefix yurtle: <https://yurtle.dev/schema/> .
@prefix pm: <https://yurtle.dev/pm/> .

<urn:task:task1> a yurtle:WorkItem ;
    yurtle:title "Task One" ;
    pm:status "pending" .
---

# Task One

First task.
''')

    (workspace / "task2.md").write_text('''---
@prefix yurtle: <https://yurtle.dev/schema/> .
@prefix pm: <https://yurtle.dev/pm/> .

<urn:task:task2> a yurtle:WorkItem ;
    yurtle:title "Task Two" ;
    pm:status "completed" .
---

# Task Two

Second task.
''')

    # Create subdirectory with files
    subdir = workspace / "projects"
    subdir.mkdir()
    (subdir / "project1.md").write_text('''---
id: project1
title: Project One
type: project
---

# Project One

A project file.
''')

    return workspace


@pytest.fixture
def sample_doc_with_fenced_blocks():
    """Sample Yurtle document with YAML frontmatter and fenced turtle blocks."""
    return '''---
id: EXP-981
title: "Y0/Y1 Chunk Graph Storage"
type: expedition
status: done
tags: [ylayer, knowledge]
---

# EXP-981: Y0/Y1 Chunk Graph Storage

Implementation of chunk-level graph storage for Y0/Y1 layers.

```turtle
@prefix ylayer: <https://nusy.dev/ylayer/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<#chunk-storage> a ylayer:Feature ;
    rdfs:label "Chunk Graph Storage" ;
    ylayer:layer "Y0", "Y1" .
```

## Results

The feature was implemented successfully.

```yurtle
@prefix kb: <https://yurtle.dev/kanban/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<> kb:statusChange [
    kb:status kb:done ;
    kb:at "2026-02-25T23:46:48"^^xsd:dateTime ;
    kb:by "DGX" ;
  ] .
```
'''


@pytest.fixture
def sample_doc_with_hdd_block():
    """Sample HDD hypothesis file with turtle knowledge block."""
    return '''---
id: H130.1
title: "V12 accuracy improves"
type: hypothesis
status: draft
paper: PAPER-130
target: ">=85%"
tags: [paper-130]
---

# H130.1: V12 accuracy improves

```turtle
@prefix hyp: <https://nusy.dev/hypothesis/> .
@prefix paper: <https://nusy.dev/paper/> .
@prefix measure: <https://nusy.dev/measure/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<#H130.1> a hyp:Hypothesis ;
    rdfs:label "V12 accuracy improves" ;
    hyp:paper paper:PAPER-130 ;
    hyp:target ">=85%" ;
    hyp:measuredBy measure:M-007, measure:M-025 .
```

## Rationale

We hypothesize that V12's cognitive signal fusion improves accuracy.
'''


@pytest.fixture
def sample_doc_no_frontmatter_with_block():
    """Document with no frontmatter but a fenced turtle block."""
    return '''# Standalone Notes

Some notes with an inline knowledge block.

```turtle
@prefix note: <https://nusy.dev/note/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<#observation-1> a note:Observation ;
    rdfs:label "Interesting finding" .
```
'''


@pytest.fixture
def empty_graph():
    """Return an empty RDFlib Graph."""
    return Graph()


@pytest.fixture
def sample_graph():
    """Return a Graph with sample triples."""
    graph = Graph()
    yurtle_rdflib.bind_standard_namespaces(graph)

    subject = URIRef("urn:test:subject")
    graph.add((subject, yurtle_rdflib.YURTLE.title, Literal("Test Subject")))
    graph.add((subject, yurtle_rdflib.PM.status, Literal("active")))
    graph.add((subject, yurtle_rdflib.PM.priority, Literal(1)))

    return graph
