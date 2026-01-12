---
@prefix yurtle: <https://yurtle.dev/schema/> .
@prefix lab: <https://yurtle.dev/lab/> .
@prefix loinc: <https://loinc.org/> .
@prefix snomed: <http://snomed.info/id/> .
@prefix med: <https://yurtle.dev/medical/> .

<urn:lab:lipid-panel> a lab:LaboratoryTest, lab:Panel ;
    yurtle:title "Lipid Panel" ;
    yurtle:description "Blood test measuring cholesterol and triglyceride levels for cardiovascular risk assessment" ;
    lab:abbreviation "Lipids" ;
    lab:loincCode "57698-3" ;
    lab:loincName "Lipid panel with direct LDL - Serum or Plasma" ;
    lab:loincCodeBasic "100898-6" ;
    lab:specimen "Serum", "Plasma" ;
    lab:method "Enzymatic", "Direct measurement" ;
    lab:specialty "Clinical Chemistry", "Cardiology" ;
    lab:cptCode "80061" ;
    lab:fasting "Preferred but not required for screening" ;
    med:clinicalUse "Cardiovascular risk assessment", "Dyslipidemia diagnosis", "Statin therapy monitoring", "Pancreatitis risk assessment" ;
    med:condition <snomed:13644009> ; # Hypercholesterolemia
    med:condition <snomed:302870006> ; # Hypertriglyceridemia
    lab:component <urn:lab:total-cholesterol>, <urn:lab:ldl-cholesterol>, <urn:lab:hdl-cholesterol>, <urn:lab:triglycerides>, <urn:lab:vldl-cholesterol> ;
    lab:relatedTest <urn:lab:apolipoprotein-b>, <urn:lab:lipoprotein-a>, <urn:lab:hs-crp> ;
    yurtle:source <https://loinc.org/57698-3>, <https://www.labcorp.com/tests/303756/lipid-panel> .
---

# Lipid Panel

A **Lipid Panel** (also called a lipid profile or cholesterol panel) measures fats and fatty substances in the blood that are used as energy sources. It is a key test for assessing cardiovascular disease (CVD) risk.

## Panel Components

```yurtle
total-cholesterol:
  name: Total Cholesterol
  loinc: 2093-3
  units: mg/dL
  reference-ranges:
    desirable: "<200"
    borderline-high: "200-239"
    high: "≥240"
  clinical-significance: Sum of all cholesterol fractions

ldl-cholesterol:
  name: LDL Cholesterol (Bad Cholesterol)
  loinc: 13457-7
  loinc-direct: 18262-6
  units: mg/dL
  reference-ranges:
    optimal: "<100"
    near-optimal: "100-129"
    borderline-high: "130-159"
    high: "160-189"
    very-high: "≥190"
  clinical-significance: Primary target for therapy; major CVD risk factor
  calculation: Friedewald equation (Total - HDL - TG/5) if TG <400

hdl-cholesterol:
  name: HDL Cholesterol (Good Cholesterol)
  loinc: 2085-9
  units: mg/dL
  reference-ranges:
    low-risk: "<40"
    average: "40-59"
    protective: "≥60"
  clinical-significance: Inverse relationship with CVD risk
  note: Levels ≥60 mg/dL considered negative risk factor

triglycerides:
  name: Triglycerides
  loinc: 2571-8
  units: mg/dL
  reference-ranges:
    normal: "<150"
    borderline-high: "150-199"
    high: "200-499"
    very-high: "≥500"
  clinical-significance: Very high levels increase pancreatitis risk
  note: Fasting preferred for accurate measurement

vldl-cholesterol:
  name: VLDL Cholesterol
  loinc: 13458-5
  units: mg/dL
  reference-range: "5-40"
  calculation: Triglycerides / 5
  clinical-significance: Carries triglycerides; contributes to atherosclerosis

non-hdl-cholesterol:
  name: Non-HDL Cholesterol
  loinc: 43396-1
  units: mg/dL
  calculation: Total Cholesterol - HDL
  reference-range: "<130"
  clinical-significance: Secondary target after LDL; includes all atherogenic particles
```

## Risk Classification (NCEP ATP III)

| Risk Category | LDL Goal | Non-HDL Goal |
|--------------|----------|--------------|
| Very High Risk (CVD + diabetes) | <70 mg/dL | <100 mg/dL |
| High Risk (CHD or equivalent) | <100 mg/dL | <130 mg/dL |
| Moderately High Risk (2+ risk factors) | <130 mg/dL | <160 mg/dL |
| Moderate Risk (2+ risk factors, 10-yr risk <10%) | <130 mg/dL | <160 mg/dL |
| Low Risk (0-1 risk factors) | <160 mg/dL | <190 mg/dL |

## Cardiovascular Risk Factors

```yurtle
cvd-risk-factors:
  positive:
    - "Age (men ≥45, women ≥55)"
    - "Family history of premature CHD"
    - "Cigarette smoking"
    - "Hypertension (BP ≥140/90 or on medication)"
    - "Low HDL cholesterol (<40 mg/dL)"
    - "Diabetes mellitus"
    - "Chronic kidney disease"

  negative:
    - "High HDL cholesterol (≥60 mg/dL)"
    - note: Subtracts one risk factor from total count
```

## Testing Recommendations

### Screening Intervals

| Population | Frequency |
|------------|-----------|
| Adults 40-75 years | Every 4-6 years |
| Adults with CVD risk factors | Every 1-2 years |
| On lipid-lowering therapy | 4-12 weeks after starting, then annually |
| Very high triglycerides (>500) | More frequent monitoring |

### Fasting Requirements

- **Non-fasting acceptable** for screening (per 2018 guidelines)
- **Fasting (9-12 hours)** preferred when:
  - Triglycerides expected to be elevated
  - Monitoring response to therapy
  - Calculating LDL using Friedewald equation

## Limitations

```yurtle
limitations:
  ldl-calculation:
    friedewald-invalid-when:
      - "Triglycerides >400 mg/dL"
      - "Type III hyperlipoproteinemia"
      - "Non-fasting specimen"
    solution: Use direct LDL measurement

  biological-variability:
    cholesterol: "5-10%"
    triglycerides: "20-30%"
    note: Confirm abnormal results with repeat testing

  interferences:
    - "Recent illness or surgery (wait 6-8 weeks)"
    - "Pregnancy (levels increase)"
    - "Certain medications"
```

## Related Tests

- [[apolipoprotein-b]] - Better predictor of CVD risk
- [[lipoprotein-a]] - Independent CVD risk factor
- [[hs-crp]] - Inflammatory marker for CVD risk
- [[advanced-lipid-panel]] - Particle number and size

## References

- [LOINC 57698-3](https://loinc.org/57698-3)
- [Labcorp Lipid Panel](https://www.labcorp.com/tests/303756/lipid-panel)
- [ACC/AHA Cholesterol Guidelines](https://www.acc.org)
