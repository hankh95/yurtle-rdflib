---
@prefix yurtle: <https://yurtle.dev/schema/> .
@prefix lab: <https://yurtle.dev/lab/> .
@prefix loinc: <https://loinc.org/> .
@prefix snomed: <http://snomed.info/id/> .
@prefix med: <https://yurtle.dev/medical/> .

<urn:lab:basic-metabolic-panel> a lab:LaboratoryTest, lab:Panel ;
    yurtle:title "Basic Metabolic Panel (BMP)" ;
    yurtle:description "Blood test measuring glucose, electrolytes, and kidney function" ;
    lab:abbreviation "BMP", "Chem-8", "SMA-8" ;
    lab:loincCode "51990-0" ;
    lab:loincName "Basic metabolic panel - Blood" ;
    lab:loincCodeAlternate "24321-2" ;
    lab:specimen "Serum", "Plasma" ;
    lab:cptCode "80048" ;
    lab:specialty "Clinical Chemistry" ;
    lab:fasting "Preferred for glucose accuracy" ;
    med:clinicalUse "Routine health screening", "Electrolyte monitoring", "Kidney function assessment", "Acid-base evaluation", "Diabetes monitoring" ;
    lab:component <urn:lab:glucose>, <urn:lab:sodium>, <urn:lab:potassium>, <urn:lab:chloride>, <urn:lab:bicarbonate>, <urn:lab:bun>, <urn:lab:creatinine>, <urn:lab:calcium> ;
    lab:calculatedValue <urn:lab:egfr>, <urn:lab:anion-gap>, <urn:lab:bun-creatinine-ratio> ;
    lab:relatedTest <urn:lab:comprehensive-metabolic-panel>, <urn:lab:renal-function-panel> ;
    yurtle:source <https://loinc.org/51990-0>, <https://medlineplus.gov/lab-tests/basic-metabolic-panel-bmp/> .
---

# Basic Metabolic Panel (BMP)

The **Basic Metabolic Panel (BMP)**, also known as Chem-8 or SMA-8, is a blood test that measures eight substances in the blood. It provides important information about the body's chemical balance, metabolism, and kidney function.

## Panel Components

```yurtle
glucose:
  name: Glucose
  loinc: 2345-7
  units: mg/dL
  reference-range:
    fasting: "74-99"
    random: "<140"
  critical-low: "<50"
  critical-high: ">500"
  clinical-significance: Energy metabolism; diabetes screening

sodium:
  name: Sodium
  loinc: 2951-2
  units: mmol/L
  reference-range: "136-144"
  critical-low: "<120"
  critical-high: ">160"
  clinical-significance: Fluid balance; nerve/muscle function

potassium:
  name: Potassium
  loinc: 2823-3
  units: mmol/L
  reference-range: "3.7-5.1"
  critical-low: "<2.5"
  critical-high: ">6.5"
  clinical-significance: Cardiac rhythm; muscle contraction
  note: Hemolysis causes falsely elevated results

chloride:
  name: Chloride
  loinc: 2075-0
  units: mmol/L
  reference-range: "98-107"
  clinical-significance: Acid-base balance; paired with sodium

bicarbonate:
  name: Bicarbonate (CO2)
  loinc: 1962-0
  units: mmol/L
  reference-range: "22-30"
  clinical-significance: Acid-base status indicator

bun:
  name: Blood Urea Nitrogen
  loinc: 3094-0
  units: mg/dL
  reference-range: "7-21"
  clinical-significance: Kidney function; protein metabolism
  elevated-causes: Kidney disease, dehydration, high protein diet, GI bleeding

creatinine:
  name: Creatinine
  loinc: 2160-0
  units: mg/dL
  reference-range:
    male: "0.70-1.30"
    female: "0.58-0.96"
  clinical-significance: Primary marker of kidney function
  note: More reliable than BUN; less affected by diet

calcium:
  name: Calcium (Total)
  loinc: 17861-6
  units: mg/dL
  reference-range: "8.5-10.2"
  critical-low: "<6.0"
  critical-high: ">13.0"
  clinical-significance: Bone health; nerve/muscle function
  note: Corrected calcium = measured + 0.8 × (4 - albumin)
```

## Calculated Values

```yurtle
egfr:
  name: Estimated GFR
  loinc: 33914-3
  units: mL/min/1.73m²
  formula: CKD-EPI 2021 (race-free)
  reference-range: ">90"
  ckd-staging:
    G1: "≥90 (Normal)"
    G2: "60-89 (Mildly decreased)"
    G3a: "45-59 (Mild-moderate decrease)"
    G3b: "30-44 (Moderate-severe decrease)"
    G4: "15-29 (Severely decreased)"
    G5: "<15 (Kidney failure)"

anion-gap:
  name: Anion Gap
  loinc: 33037-3
  units: mmol/L
  formula: "Na - (Cl + HCO3)"
  reference-range: "8-12"
  reference-with-K: "10-16"
  elevated-causes: "MUDPILES (Methanol, Uremia, DKA, Propylene glycol, INH/Iron, Lactic acidosis, Ethylene glycol, Salicylates)"

bun-creatinine-ratio:
  name: BUN/Creatinine Ratio
  reference-range: "10:1 to 20:1"
  elevated: ">20:1 suggests prerenal azotemia"
  decreased: "<10:1 suggests liver disease or malnutrition"
```

## Clinical Interpretation

### Electrolyte Patterns

| Pattern | Na | K | Cl | HCO3 | Common Causes |
|---------|----|----|----|----|---------------|
| Dehydration | ↑ | ↑ | ↑ | N | Volume loss |
| DKA | ↓/N | ↑ | N | ↓ | Insulin deficiency |
| Vomiting | N | ↓ | ↓ | ↑ | GI losses |
| Diarrhea | N | ↓ | ↑ | ↓ | GI losses |
| Renal failure | N/↑ | ↑ | N | ↓ | Decreased excretion |

### Critical Values Requiring Immediate Action

```yurtle
critical-values:
  requires-notification:
    sodium: "<120 or >160 mmol/L"
    potassium: "<2.5 or >6.5 mmol/L"
    glucose: "<50 or >500 mg/dL"
    calcium: "<6.0 or >13.0 mg/dL"
    bicarbonate: "<10 or >40 mmol/L"

  clinical-urgency:
    hyperkalemia: "Risk of cardiac arrhythmia"
    hyponatremia: "Risk of seizures, cerebral edema"
    hypoglycemia: "Risk of altered consciousness"
    hypercalcemia: "Risk of cardiac effects"
```

## Ordering Considerations

### When to Order

- **Routine health maintenance**
- **Emergency department evaluation**
- **Pre-operative assessment**
- **Monitoring patients on**:
  - Diuretics
  - ACE inhibitors/ARBs
  - Digoxin
  - Chemotherapy
- **Chronic disease monitoring**:
  - Diabetes
  - Kidney disease
  - Heart failure
  - Hypertension

### Specimen Requirements

```yurtle
specimen-requirements:
  preferred: "Serum (gold/red top)"
  acceptable: "Plasma (green top)"
  volume: "3-5 mL"
  fasting: "Preferred for glucose"
  avoid:
    - "Hemolyzed specimens (affects K)"
    - "Specimens drawn above IV line"
    - "Prolonged tourniquet application"
```

## Related Tests

- [[comprehensive-metabolic-panel]] - Adds liver function tests
- [[renal-function-panel]] - Focused kidney assessment
- [[electrolyte-panel]] - Na, K, Cl, CO2 only
- [[arterial-blood-gas]] - Precise acid-base assessment

## References

- [LOINC 51990-0](https://loinc.org/51990-0)
- [MedlinePlus BMP](https://medlineplus.gov/lab-tests/basic-metabolic-panel-bmp/)
- [Cleveland Clinic BMP](https://my.clevelandclinic.org/health/diagnostics/22020-basic-metabolic-panel-bmp)
