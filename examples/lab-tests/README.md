# Laboratory Test Examples

This directory contains example Yurtle files representing common laboratory tests. Each file demonstrates how to use Yurtle format to represent rich medical/scientific data with:

- **Turtle frontmatter**: RDF triples for structured data (LOINC codes, reference ranges, etc.)
- **Yurtle blocks**: Inline structured data for components and interpretations
- **Markdown content**: Human-readable documentation and clinical guidelines

## Files

| File | Description | LOINC |
|------|-------------|-------|
| [complete-blood-count.md](complete-blood-count.md) | Complete Blood Count (CBC) panel | 58410-2 |
| [hemoglobin-a1c.md](hemoglobin-a1c.md) | Hemoglobin A1c for diabetes monitoring | 4548-4 |
| [lipid-panel.md](lipid-panel.md) | Cholesterol and triglyceride panel | 57698-3 |
| [basic-metabolic-panel.md](basic-metabolic-panel.md) | BMP with electrolytes and kidney function | 51990-0 |

## Namespaces Used

```turtle
@prefix yurtle: <https://yurtle.dev/schema/> .   # Core Yurtle properties
@prefix lab: <https://yurtle.dev/lab/> .         # Laboratory-specific properties
@prefix loinc: <https://loinc.org/> .            # LOINC codes
@prefix snomed: <http://snomed.info/id/> .       # SNOMED CT codes
@prefix med: <https://yurtle.dev/medical/> .     # Medical properties
```

## Usage with yurtle-rdflib

```python
import yurtle_rdflib
from rdflib import Namespace

# Load all lab test files
graph = yurtle_rdflib.load_workspace("examples/lab-tests/")

# Define namespaces
LAB = Namespace("https://yurtle.dev/lab/")
LOINC = Namespace("https://loinc.org/")

# Query for all lab tests
results = graph.query("""
    PREFIX lab: <https://yurtle.dev/lab/>
    PREFIX yurtle: <https://yurtle.dev/schema/>

    SELECT ?test ?title ?loinc WHERE {
        ?test a lab:LaboratoryTest ;
              yurtle:title ?title ;
              lab:loincCode ?loinc .
    }
""")

for row in results:
    print(f"{row.title}: LOINC {row.loinc}")

# Find tests for diabetes monitoring
diabetes_tests = graph.query("""
    PREFIX med: <https://yurtle.dev/medical/>
    PREFIX yurtle: <https://yurtle.dev/schema/>

    SELECT ?title WHERE {
        ?test med:clinicalUse "Diabetes monitoring" ;
              yurtle:title ?title .
    }
""")
```

## Data Sources

- [LOINC](https://loinc.org/) - Logical Observation Identifiers Names and Codes
- [Wikipedia](https://en.wikipedia.org/) - Medical test articles
- [Labcorp](https://www.labcorp.com/) - Reference ranges and clinical information
- [MedlinePlus](https://medlineplus.gov/) - Patient-focused test information

## Extending

To add more laboratory tests:

1. Create a new `.md` file in this directory
2. Add Turtle frontmatter with:
   - Subject URI: `<urn:lab:test-name>`
   - Type: `lab:LaboratoryTest` (and `lab:Panel` if applicable)
   - LOINC code: `lab:loincCode "XXXXX-X"`
   - Reference ranges: `lab:referenceRange...`
3. Add Yurtle blocks for components and interpretations
4. Include clinical documentation in markdown

## License

These example files are provided under the MIT License as part of the yurtle-rdflib package.
