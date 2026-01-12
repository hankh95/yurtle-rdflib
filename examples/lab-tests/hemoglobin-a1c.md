---
@prefix yurtle: <https://yurtle.dev/schema/> .
@prefix lab: <https://yurtle.dev/lab/> .
@prefix loinc: <https://loinc.org/> .
@prefix snomed: <http://snomed.info/id/> .
@prefix med: <https://yurtle.dev/medical/> .

<urn:lab:hemoglobin-a1c> a lab:LaboratoryTest ;
    yurtle:title "Hemoglobin A1c (HbA1c)" ;
    yurtle:description "Measures average blood glucose levels over the past 2-3 months" ;
    lab:abbreviation "HbA1c", "A1C", "Glycated Hemoglobin" ;
    lab:loincCode "4548-4" ;
    lab:loincName "Hemoglobin A1c/Hemoglobin.total in Blood" ;
    lab:loincCodeIFCC "59261-8" ;
    lab:loincCodeHPLC "17856-6" ;
    lab:loincCodeElectrophoresis "4549-2" ;
    lab:specimen "Blood" ;
    lab:method "Immunoassay", "HPLC", "Electrophoresis" ;
    lab:specialty "Clinical Chemistry", "Endocrinology" ;
    lab:units "%" ;
    lab:unitsIFCC "mmol/mol" ;
    lab:referenceRangeNormal "4.0-5.6" ;
    lab:referenceRangePrediabetes "5.7-6.4" ;
    lab:referenceRangeDiabetes ">6.5" ;
    lab:diabetesGoal "<7.0" ;
    lab:reflectsTimeframe "8-12 weeks" ;
    med:clinicalUse "Diabetes diagnosis", "Diabetes monitoring", "Prediabetes screening", "Glycemic control assessment" ;
    med:condition <snomed:73211009> ; # Diabetes mellitus
    med:condition <snomed:714628002> ; # Prediabetes
    lab:relatedTest <urn:lab:fasting-glucose>, <urn:lab:oral-glucose-tolerance> ;
    yurtle:source <https://loinc.org/4548-4>, <https://www.labcorp.com/tests/001453/hemoglobin-hb-a1c> .
---

# Hemoglobin A1c (HbA1c)

**Hemoglobin A1c** (also known as **glycated hemoglobin**, **A1C**, or **HbA1c**) is a blood test that measures average blood glucose (sugar) levels over the past 2-3 months. It is the primary test for diagnosing and monitoring diabetes.

## How It Works

Glucose in the blood attaches to hemoglobin in red blood cells. Since red blood cells have a lifespan of approximately 120 days, the HbA1c measurement reflects average glucose exposure over the past 8-12 weeks.

## Reference Ranges (NGSP Standard)

```yurtle
interpretation:
  normal:
    range: "<5.7%"
    ifcc: "<39 mmol/mol"
    meaning: Normal glycemic control

  prediabetes:
    range: "5.7-6.4%"
    ifcc: "39-47 mmol/mol"
    meaning: Increased risk of diabetes
    action: Lifestyle modifications recommended

  diabetes:
    range: "≥6.5%"
    ifcc: "≥48 mmol/mol"
    meaning: Diagnostic for diabetes mellitus
    action: Medical treatment indicated

  treatment-goals:
    general-adult: "<7.0%"
    less-stringent: "<8.0%"
    more-stringent: "<6.5%"
    note: Goals individualized based on patient factors
```

## NGSP to IFCC Conversion

| NGSP (%) | IFCC (mmol/mol) | Average Glucose (mg/dL) |
|----------|-----------------|-------------------------|
| 5.0 | 31 | 97 |
| 5.5 | 37 | 111 |
| 6.0 | 42 | 126 |
| 6.5 | 48 | 140 |
| 7.0 | 53 | 154 |
| 7.5 | 59 | 169 |
| 8.0 | 64 | 183 |
| 9.0 | 75 | 212 |
| 10.0 | 86 | 240 |

## Clinical Guidelines

### American Diabetes Association (ADA) Recommendations

- **Diagnosis**: HbA1c ≥6.5% confirms diabetes (requires two abnormal tests)
- **Prediabetes**: HbA1c 5.7-6.4% indicates increased risk
- **Monitoring Frequency**:
  - At goal with stable control: Every 6 months
  - Not at goal or therapy change: Every 3 months

### Treatment Targets

| Population | HbA1c Goal |
|------------|------------|
| Most adults with diabetes | <7.0% |
| Younger patients, short duration, no CVD | <6.5% |
| Older patients, comorbidities, hypoglycemia risk | <8.0% |
| Pregnancy (preexisting diabetes) | <6.5% |

## Limitations and Interferences

```yurtle
limitations:
  shortened-rbc-lifespan:
    causes:
      - Hemolytic anemia
      - Sickle cell disease
      - Recent blood loss
      - Pregnancy
    effect: Falsely decreased HbA1c

  hemoglobin-variants:
    causes:
      - HbS (sickle cell)
      - HbC
      - HbE
    effect: Method-dependent interference

  other-factors:
    - Iron deficiency (falsely elevated)
    - Recent transfusion (variable)
    - Uremia (method-dependent)
    - Certain medications
```

## Related Tests

- [[fasting-glucose]] - Fasting blood sugar
- [[oral-glucose-tolerance-test]] - 2-hour glucose tolerance
- [[fructosamine]] - 2-3 week glycemic average
- [[continuous-glucose-monitoring]] - Real-time glucose trends

## References

- [LOINC 4548-4](https://loinc.org/4548-4)
- [ADA Standards of Medical Care in Diabetes](https://diabetesjournals.org/care)
- [Labcorp HbA1c Test](https://www.labcorp.com/tests/001453/hemoglobin-hb-a1c)
