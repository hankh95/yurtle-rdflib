# Yurtle RDFLib — Claude Code Instructions

Python library for parsing and querying Yurtle format (Markdown with TTL/YAML frontmatter) using rdflib as the backend.

## Project Overview

- **Language:** Python 3.11+
- **Build:** `pip install -e ".[dev]"`
- **Tests:** `pytest`

## Development Practices

### Branch + PR Pattern (Required)

All implementation work goes through feature branches and pull requests:

1. Create a feature branch: `git checkout -b feat-short-description`
2. Do all implementation work on the branch — **never push directly to main**
3. Run tests: `pytest`
4. Push and create PR: `gh pr create`
5. Get review from another developer/agent before merging

After merge, clean up:
```bash
git branch -d feat-short-description
git push origin --delete feat-short-description
```

### Testing

Run `pytest` before committing. Tests must pass before creating a PR.

```bash
pytest              # All tests
pytest -v           # Verbose
```

### Code Quality

- Always use type hints
- Prefer editing existing files over creating new ones
- Don't create files unless necessary

### Versioning

Semantic versioning. Version locations must stay in sync:
- `pyproject.toml` → `version`

## Multi-Agent Coordination

Multiple Claude Code agents may work on this project.

| Agent | GitHub | Platform |
|-------|--------|----------|
| **M5** | hankh95 | MacBook Pro M5 |
| **DGX** | hankh959 | DGX Spark |
| **Mini** | hankh1844 | Mac Mini M4 |

## Related Projects

- **yurtle** — The Yurtle format specification
- **nusy-product-team** — Primary consumer (brain/utils/yurtle_adapter.py)
- **acf-framework** — Uses yurtle-rdflib for graph queries
