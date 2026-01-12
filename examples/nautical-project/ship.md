---
yurtle: v1.3
id: nautical-project/ship
type: asset
title: Clipper Windchaser
domain:
  - nautical
version: 1.0.0
status: seaworthy
path: examples/nautical-project
index:
  discoverable: true
  parent: nautical-project/voyage
topics:
  - clipper
  - speed
relates-to:
  - nautical-project/voyage
  - nautical-project/crew
nugget: 1852 three-masted clipper — fastest trade-wind runner in the fleet
---

# Windchaser

Built in Aberdeen, copper-sheathed, Baltimore clipper lines.  
She has outrun typhoons and carried tea from Canton in 79 days.

```yurtle
ship:
  name: Windchaser
  type: Three-masted clipper
  built: 1852
  builder: Aberdeen Shipyard
  length: 62m
  hull: Copper-sheathed
  captain: crew-captain-reed
  crew-size: 20
```

## Current Condition

```yurtle
status:
  hull: excellent
  sails: good
  rigging: excellent
  water-remaining: 9400 gallons
  days-at-current-ration: 78
  last-inspection: Day 40
```

## Relationships

```yurtle
ship:
  part-of: voyage
  crewed-by: crew
  commanded-by: crew-captain-reed
  carries: manifest
```

## Notes

The fore-topsail was replaced after the Day 38 squall.  
Copper sheathing prevents barnacle buildup — essential for speed.
