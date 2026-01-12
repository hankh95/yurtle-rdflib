---
yurtle: v1.2
id: nautical-project/index
type: index
title: Windchaser — Voyage to the Sapphire Isles
path: examples/nautical-project
index:
  discoverable: true
  parent: examples
  children:
    - nautical-project/voyage
    - nautical-project/ship
    - nautical-project/crew
    - nautical-project/manifest
    - nautical-project/logbook-2025-12
nugget: A complete, living knowledge graph built only with Markdown + Yurtle
---

# The Windchaser Project

One voyage. One ship. Twenty souls.  
Everything below is a single Markdown file with Yurtle front matter.

```mermaid
graph TD
    V[voyage.md<br/>Voyage to the Sapphire Isles] --> S[ship.md]
    V --> C[crew.md]
    V --> M[manifest.md]
    V --> L[logbook-2025-12.md]
    S --> C
    C --> CR[crew-captain-reed.md]
    C --> NL[crew-navigator-lee.md]
```

