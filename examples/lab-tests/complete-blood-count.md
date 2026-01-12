---
@prefix yurtle: <https://yurtle.dev/schema/> .
@prefix lab: <https://yurtle.dev/lab/> .
@prefix loinc: <https://loinc.org/> .
@prefix snomed: <http://snomed.info/id/> .
@prefix med: <https://yurtle.dev/medical/> .

<urn:lab:complete-blood-count> a lab:LaboratoryTest, lab:Panel ;
    yurtle:title "Complete Blood Count (CBC)" ;
    yurtle:description "A common blood test that measures several components and features of blood" ;
    lab:abbreviation "CBC" ;
    lab:loincCode "58410-2" ;
    lab:loincName "CBC panel - Blood by Automated count" ;
    lab:loincShortName "CBC Pnl Bld Auto" ;
    lab:loincClass "PANEL.HEM/BC" ;
    lab:specimen "Blood" ;
    lab:method "Automated count" ;
    lab:specialty "Hematology" ;
    lab:commonTestRank 162 ;
    lab:firstReleasedVersion "2.30" ;
    lab:lastUpdatedVersion "2.73" ;
    lab:orderVsObservation "Order" ;
    med:clinicalUse "Routine health screening", "Diagnose anemia", "Diagnose infection", "Monitor blood disorders", "Monitor chemotherapy effects" ;
    lab:relatedTest <urn:lab:cbc-with-differential>, <urn:lab:reticulocyte-count> ;
    lab:component <urn:lab:wbc>, <urn:lab:rbc>, <urn:lab:hemoglobin>, <urn:lab:hematocrit>, <urn:lab:mcv>, <urn:lab:mch>, <urn:lab:mchc>, <urn:lab:rdw>, <urn:lab:platelets>, <urn:lab:mpv> ;
    yurtle:source <https://en.wikipedia.org/wiki/Complete_blood_count>, <https://loinc.org/58410-2> .
---

# Complete Blood Count (CBC)

The **Complete Blood Count (CBC)** is one of the most commonly ordered blood tests. It provides important information about the types and numbers of cells in the blood, especially red blood cells, white blood cells, and platelets.

## Clinical Uses

- **Routine health screening** as part of a regular checkup
- **Diagnosing medical conditions** like anemia, infection, and many other disorders
- **Monitoring** existing blood disorders or treatment effects (e.g., chemotherapy)
- **Pre-surgical evaluation** to assess bleeding risk

## Panel Components

```yurtle
wbc:
  name: White Blood Cell Count
  loinc: 6690-2
  units: 10³/µL
  reference-range-adult: 4.5-11.0
  clinical-significance: Elevated in infection, inflammation; decreased in bone marrow disorders

rbc:
  name: Red Blood Cell Count
  loinc: 789-8
  units: 10⁶/µL
  reference-range-male: 4.5-5.5
  reference-range-female: 4.0-5.0
  clinical-significance: Decreased in anemia; elevated in polycythemia

hemoglobin:
  name: Hemoglobin
  loinc: 718-7
  units: g/dL
  reference-range-male: 13.5-17.5
  reference-range-female: 12.0-16.0
  clinical-significance: Primary indicator of oxygen-carrying capacity

hematocrit:
  name: Hematocrit
  loinc: 4544-3
  units: "%"
  reference-range-male: 38.8-50.0
  reference-range-female: 34.9-44.5
  clinical-significance: Percentage of blood volume occupied by RBCs

mcv:
  name: Mean Corpuscular Volume
  loinc: 787-2
  units: fL
  reference-range-adult: 80-100
  clinical-significance: Indicates RBC size; helps classify anemia type

mch:
  name: Mean Corpuscular Hemoglobin
  loinc: 785-6
  units: pg
  reference-range-adult: 27-33
  clinical-significance: Average hemoglobin per RBC

mchc:
  name: Mean Corpuscular Hemoglobin Concentration
  loinc: 786-4
  units: g/dL
  reference-range-adult: 32-36
  clinical-significance: Average hemoglobin concentration per RBC

rdw:
  name: Red Cell Distribution Width
  loinc: 788-0
  units: "%"
  reference-range-adult: 11.5-14.5
  clinical-significance: Variation in RBC size; elevated in mixed anemias

platelets:
  name: Platelet Count
  loinc: 777-3
  units: 10³/µL
  reference-range-adult: 150-450
  clinical-significance: Essential for blood clotting
```

## Interpretation Guidelines

| Finding | Possible Causes |
|---------|-----------------|
| Low RBC/Hemoglobin | Anemia (iron deficiency, B12 deficiency, chronic disease) |
| High RBC/Hemoglobin | Polycythemia, dehydration, lung disease |
| Low WBC | Bone marrow disorders, viral infections, autoimmune |
| High WBC | Infection, inflammation, leukemia |
| Low Platelets | Thrombocytopenia, ITP, leukemia |
| High Platelets | Thrombocytosis, inflammation, iron deficiency |

## Related Tests

- [[cbc-with-differential]] - Includes breakdown of WBC types
- [[reticulocyte-count]] - Measures immature RBCs
- [[peripheral-blood-smear]] - Microscopic examination

## References

- [LOINC 58410-2](https://loinc.org/58410-2)
- [Wikipedia: Complete Blood Count](https://en.wikipedia.org/wiki/Complete_blood_count)
