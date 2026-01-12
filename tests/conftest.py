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
