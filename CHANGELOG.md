# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-03-04

### Added

- **Prefix inheritance**: Fenced `yurtle`/`turtle` blocks inherit `@prefix` declarations from the document-level graph, eliminating the need for redundant prefix lines in every block
- **YAML block detection**: Blocks containing YAML-like syntax (e.g., `scenarios:`, `corpus:`) inside `yurtle` fences are now silently skipped instead of producing parse errors
- **Merge conflict detection**: Blocks containing git merge conflict markers (`<<<<<<< HEAD`) are skipped with a debug-level log instead of noisy warnings

### Changed

- Parse failure logging downgraded from `warning` to `debug` level — blocks that fail to parse are expected in mixed-content documents and no longer spam stderr

### Fixed

- Eliminated 100+ spurious "Failed to parse fenced block" warnings when loading nusy-product-team and similar repos with mixed yurtle/YAML/example content

## [0.1.0] - 2026-01-12

### Added

- Initial release of yurtle-rdflib
- **YurtleRDFlibParser**: RDFlib parser plugin for Yurtle format
  - Supports Turtle frontmatter (native RDF)
  - Supports YAML frontmatter (converted to RDF)
  - Automatic subject URI generation
  - Provenance tracking via `prov:definedIn` triples
- **YurtleRDFlibSerializer**: RDFlib serializer plugin for Yurtle format
  - Serializes RDF triples to Turtle frontmatter
  - Preserves markdown content on round-trip
  - Filters provenance triples from output
- **YurtleStore**: Bidirectional RDFlib Store
  - Hash-based change detection for efficient sync
  - Automatic write-back to source files
  - Optional auto-flush for immediate persistence
- **Convenience functions**:
  - `load_workspace()`: Load all Yurtle files into a unified graph
  - `save_workspace()`: Save graph back to workspace files
  - `create_live_graph()`: Create store-backed graph with live sync
  - `parse_file()`: Parse a single Yurtle file
  - `serialize_file()`: Serialize graph to Yurtle file
- **Standard namespaces**: `YURTLE`, `PM`, `BEING`, `VOYAGE`, `KNOWLEDGE`, `PROVENANCE`
- Full type hints (PEP 561 compliant with py.typed marker)
- Comprehensive documentation and examples

### Dependencies

- rdflib >= 6.0.0
- pyyaml >= 6.0
- Python >= 3.9

[0.3.0]: https://github.com/hankh95/yurtle-rdflib/releases/tag/v0.3.0
[0.1.0]: https://github.com/hankh95/yurtle-rdflib/releases/tag/v0.1.0
