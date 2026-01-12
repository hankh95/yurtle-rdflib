# SPARQL Query Examples

This document demonstrates SPARQL queries using yurtle-rdflib with the example workspaces.

## Setup

```python
import yurtle_rdflib
from rdflib import Namespace

# Load workspaces
nautical = yurtle_rdflib.load_workspace("examples/nautical-project/")
lab = yurtle_rdflib.load_workspace("examples/lab-tests/")

# Define namespaces
YURTLE = Namespace("https://yurtle.dev/schema/")
LAB = Namespace("https://yurtle.dev/lab/")
MED = Namespace("https://yurtle.dev/medical/")
PROV = Namespace("https://yurtle.dev/provenance/")
```

---

## Basic Queries

### 1. List all documents

```sparql
PREFIX yurtle: <https://yurtle.dev/schema/>

SELECT ?doc ?title ?type WHERE {
    ?doc yurtle:title ?title .
    OPTIONAL { ?doc yurtle:type ?type }
}
ORDER BY ?title
```

### 2. Find by type

```sparql
PREFIX yurtle: <https://yurtle.dev/schema/>

SELECT ?person ?name WHERE {
    ?person yurtle:type "person" ;
            yurtle:title ?name .
}
```

### 3. Search by keyword (nugget)

```sparql
PREFIX yurtle: <https://yurtle.dev/schema/>

SELECT ?doc ?title ?nugget WHERE {
    ?doc yurtle:title ?title ;
         yurtle:nugget ?nugget .
    FILTER(CONTAINS(LCASE(?nugget), "sea"))
}
```

---

## Relationship Queries

### 4. Follow relates-to links

```sparql
PREFIX yurtle: <https://yurtle.dev/schema/>

SELECT ?from ?fromTitle ?to ?toTitle WHERE {
    ?from yurtle:relatesTo ?to ;
          yurtle:title ?fromTitle .
    ?to yurtle:title ?toTitle .
}
```

### 5. Find parent-child hierarchies

```sparql
PREFIX yurtle: <https://yurtle.dev/schema/>

SELECT ?parent ?parentTitle ?child ?childTitle WHERE {
    ?parent yurtle:indexChildren ?child ;
            yurtle:title ?parentTitle .
    ?child yurtle:title ?childTitle .
}
```

### 6. Traverse relationships (2 hops)

```sparql
PREFIX yurtle: <https://yurtle.dev/schema/>

SELECT ?start ?startTitle ?middle ?end ?endTitle WHERE {
    ?start yurtle:relatesTo ?middle ;
           yurtle:title ?startTitle .
    ?middle yurtle:relatesTo ?end .
    ?end yurtle:title ?endTitle .
    FILTER(?start != ?end)
}
```

---

## Aggregation Queries

### 7. Count documents by type

```sparql
PREFIX yurtle: <https://yurtle.dev/schema/>

SELECT ?type (COUNT(?doc) as ?count) WHERE {
    ?doc yurtle:type ?type .
}
GROUP BY ?type
ORDER BY DESC(?count)
```

### 8. Count relationships per document

```sparql
PREFIX yurtle: <https://yurtle.dev/schema/>

SELECT ?doc ?title (COUNT(?related) as ?relationCount) WHERE {
    ?doc yurtle:title ?title .
    OPTIONAL { ?doc yurtle:relatesTo ?related }
}
GROUP BY ?doc ?title
ORDER BY DESC(?relationCount)
```

### 9. Documents by domain

```sparql
PREFIX yurtle: <https://yurtle.dev/schema/>

SELECT ?domain (COUNT(?doc) as ?count) WHERE {
    ?doc yurtle:domain ?domain .
}
GROUP BY ?domain
```

---

## Laboratory Test Queries

### 10. Find all lab tests with LOINC codes

```sparql
PREFIX lab: <https://yurtle.dev/lab/>
PREFIX yurtle: <https://yurtle.dev/schema/>

SELECT ?test ?title ?loinc WHERE {
    ?test a lab:LaboratoryTest ;
          yurtle:title ?title ;
          lab:loincCode ?loinc .
}
ORDER BY ?loinc
```

### 11. Find tests for a clinical use

```sparql
PREFIX lab: <https://yurtle.dev/lab/>
PREFIX med: <https://yurtle.dev/medical/>
PREFIX yurtle: <https://yurtle.dev/schema/>

SELECT ?test ?title WHERE {
    ?test a lab:LaboratoryTest ;
          yurtle:title ?title ;
          med:clinicalUse ?use .
    FILTER(CONTAINS(LCASE(?use), "diabetes"))
}
```

### 12. List test components (panels)

```sparql
PREFIX lab: <https://yurtle.dev/lab/>
PREFIX yurtle: <https://yurtle.dev/schema/>

SELECT ?panel ?panelTitle ?component WHERE {
    ?panel a lab:Panel ;
           yurtle:title ?panelTitle ;
           lab:component ?component .
}
ORDER BY ?panelTitle
```

### 13. Find tests with critical values

```sparql
PREFIX lab: <https://yurtle.dev/lab/>
PREFIX yurtle: <https://yurtle.dev/schema/>

SELECT ?test ?title ?specimen WHERE {
    ?test a lab:LaboratoryTest ;
          yurtle:title ?title ;
          lab:specimen ?specimen .
}
```

---

## Provenance Queries

### 14. Find source files for triples

```sparql
PREFIX prov: <https://yurtle.dev/provenance/>
PREFIX yurtle: <https://yurtle.dev/schema/>

SELECT DISTINCT ?file WHERE {
    ?s prov:definedIn ?file .
}
ORDER BY ?file
```

### 15. Count triples per source file

```sparql
PREFIX prov: <https://yurtle.dev/provenance/>

SELECT ?file (COUNT(*) as ?tripleCount) WHERE {
    ?s prov:definedIn ?file .
}
GROUP BY ?file
ORDER BY DESC(?tripleCount)
```

---

## Advanced Queries

### 16. UNION - combine multiple patterns

```sparql
PREFIX yurtle: <https://yurtle.dev/schema/>

SELECT ?item ?title ?itemType WHERE {
    {
        ?item yurtle:type "person" ;
              yurtle:title ?title .
        BIND("Person" as ?itemType)
    }
    UNION
    {
        ?item yurtle:type "asset" ;
              yurtle:title ?title .
        BIND("Asset" as ?itemType)
    }
}
```

### 17. OPTIONAL - include missing data

```sparql
PREFIX yurtle: <https://yurtle.dev/schema/>

SELECT ?doc ?title ?status ?nugget WHERE {
    ?doc yurtle:title ?title .
    OPTIONAL { ?doc yurtle:status ?status }
    OPTIONAL { ?doc yurtle:nugget ?nugget }
}
```

### 18. FILTER with regex

```sparql
PREFIX yurtle: <https://yurtle.dev/schema/>

SELECT ?doc ?title WHERE {
    ?doc yurtle:title ?title .
    FILTER(REGEX(?title, "^(Captain|Navigator)", "i"))
}
```

### 19. CONSTRUCT - create new graph

```sparql
PREFIX yurtle: <https://yurtle.dev/schema/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

CONSTRUCT {
    ?doc skos:prefLabel ?title ;
         skos:scopeNote ?nugget .
}
WHERE {
    ?doc yurtle:title ?title ;
         yurtle:nugget ?nugget .
}
```

### 20. Subquery - find most connected documents

```sparql
PREFIX yurtle: <https://yurtle.dev/schema/>

SELECT ?doc ?title ?connections WHERE {
    {
        SELECT ?doc (COUNT(?related) as ?connections) WHERE {
            ?doc yurtle:relatesTo ?related .
        }
        GROUP BY ?doc
        ORDER BY DESC(?connections)
        LIMIT 5
    }
    ?doc yurtle:title ?title .
}
```

---

## Python Examples

### Run any query

```python
import yurtle_rdflib

graph = yurtle_rdflib.load_workspace("examples/nautical-project/")

results = graph.query("""
    PREFIX yurtle: <https://yurtle.dev/schema/>
    SELECT ?doc ?title WHERE {
        ?doc yurtle:title ?title .
    }
""")

for row in results:
    print(f"{row.title}")
```

### Convert results to DataFrame

```python
import pandas as pd

results = graph.query(query_string)
df = pd.DataFrame(results, columns=results.vars)
print(df)
```

### Export query results

```python
# To JSON
import json
results = graph.query(query_string)
data = [{"title": str(row.title)} for row in results]
print(json.dumps(data, indent=2))

# To CSV
import csv
with open("results.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerow(results.vars)
    writer.writerows(results)
```

---

## Tips

1. **Use OPTIONAL for sparse data** - Not all documents have all fields
2. **FILTER early** - Put filters close to the patterns they affect
3. **Limit results during development** - Add `LIMIT 10` while testing
4. **Use prefixes** - Define namespaces at the top for cleaner queries
5. **Check provenance** - Use `prov:definedIn` to trace where data came from
