# Medication List Database & Toxicology Test Associations

**Date**: October 27, 2025
**Purpose**: Comprehensive medication database with toxicology test mappings for LCMS workflows

---

## Overview

This system provides a structured medication reference database that maps medications to their corresponding toxicology tests. Essential for:
- LCMS method selection based on patient medications
- Therapeutic drug monitoring (TDM) workflows
- Toxicology screening panel selection
- Result interpretation with medication context
- Insurance pre-authorization for specific drug tests

---

## Medication Database Structure

### Core Medication Entity

```python
class Medication(BaseEntity):
    """
    Comprehensive medication reference database
    """
    # Drug Identification
    name: str                           # Generic name (e.g., "Metformin")
    brand_names: JSONB                  # ["Glucophage", "Fortamet", "Riomet"]
    drug_class: str                     # "Antidiabetic - Biguanide"
    therapeutic_category: str           # "Diabetes Management"

    # Chemical Properties
    chemical_name: str | None           # IUPAC name
    molecular_formula: str | None       # C4H11N5
    molecular_weight: float | None      # 129.16 g/mol
    cas_number: str | None             # 657-24-9

    # Classification Codes
    atc_code: str | None               # A10BA02 (Anatomical Therapeutic Chemical)
    ndc_codes: JSONB | None            # National Drug Codes
    rxcui: str | None                  # RxNorm Concept Unique Identifier

    # Clinical Information
    mechanism_of_action: str | None
    indications: JSONB                  # ["Type 2 Diabetes", "PCOS"]
    contraindications: JSONB
    half_life: str | None              # "4-8 hours"

    # Dosing Information
    typical_dose_range: str | None     # "500-2000 mg/day"
    dosage_forms: JSONB                # ["Tablet", "Liquid", "ER"]
    routes_of_administration: JSONB    # ["Oral", "IV"]

    # Metabolism & Excretion
    primary_metabolism: str | None     # "Hepatic CYP2D6"
    active_metabolites: JSONB          # List of metabolites
    excretion_route: str | None        # "Renal 90%, Fecal 10%"

    # Toxicology Relevance
    is_controlled_substance: bool
    dea_schedule: str | None           # I, II, III, IV, V
    therapeutic_window: str | None     # "5-20 mcg/mL"
    toxic_level: str | None            # ">30 mcg/mL"

    # Testing Information
    commonly_screened: bool            # Include in standard tox panels
    requires_confirmation: bool        # Needs confirmatory testing
    detection_window_urine: str | None # "2-4 days"
    detection_window_blood: str | None # "4-6 hours"

    # Reference Data
    fda_approved: bool
    approval_date: date | None
    black_box_warning: bool
    pregnancy_category: str | None     # A, B, C, D, X

    # System Fields
    is_active: bool
    synonyms: JSONB                    # Alternative names
    notes: str | None
```

---

## Toxicology Test Entity

### ToxicologyTest Model

```python
class ToxicologyTest(LabScopedEntity):
    """
    Defines specific toxicology tests/assays
    """
    # Test Identification
    test_name: str                     # "Benzodiazepine Screen"
    test_code: str                     # "BENZO-SCRN"
    cpt_code: str | None              # 80307 for billing
    loinc_code: str | None            # Standard test identifier

    # Test Classification
    test_category: str                 # "Drug Screen", "Therapeutic Monitoring", "Confirmation"
    test_type: str                     # "Immunoassay", "LCMS", "GCMS"
    specimen_type: str                 # "Urine", "Blood", "Oral Fluid"

    # Analytical Information
    method: str                        # "LC-MS/MS", "EMIT", "ELISA"
    instrument_type: str | None       # "Agilent 6460", "Roche Cobas"
    analytical_range: str | None      # "5-1000 ng/mL"
    limit_of_detection: str | None    # "2 ng/mL"
    limit_of_quantitation: str | None # "5 ng/mL"

    # Test Performance
    cutoff_value: float | None        # Screening cutoff
    cutoff_units: str | None          # "ng/mL"
    turnaround_time: str | None       # "Same day", "24 hours"

    # Clinical Context
    clinical_utility: str | None
    interpretation_notes: str | None

    # Regulatory
    clia_complexity: str | None       # "Waived", "Moderate", "High"
    requires_medical_necessity: bool

    # Status
    is_active: bool
    is_stat_available: bool
```

---

## Medication-Test Association

### MedicationTestAssociation (Many-to-Many)

```python
class MedicationTestAssociation(BaseEntity):
    """
    Maps medications to toxicology tests
    """
    medication_uid: str                # FK to Medication
    toxicology_test_uid: str          # FK to ToxicologyTest

    # Association Details
    association_type: str              # "primary", "metabolite", "cross_reactive"

    # Detection Information
    is_direct_detection: bool          # True if drug itself is detected
    detected_as: str | None           # "Parent drug" or "Metabolite name"
    cross_reactivity_level: str | None # "High", "Moderate", "Low"

    # Clinical Relevance
    clinical_significance: str | None
    interpretation_guidance: str | None

    # Interference
    causes_false_positive: bool
    causes_false_negative: bool
    interference_notes: str | None

    # Priority & Recommendations
    is_preferred_test: bool
    is_confirmatory_test: bool
    requires_additional_testing: bool

    # Status
    is_active: bool
    notes: str | None
```

---

## Common Toxicology Test Panels

### Standard Drug Screen Panels

```yaml
panel_configurations:
  standard_5_panel:
    name: "DOT/Workplace 5-Panel"
    tests:
      - Amphetamines (AMP)
      - Cocaine Metabolites (COC)
      - Marijuana Metabolites (THC)
      - Opiates (OPI)
      - Phencyclidine (PCP)
    specimen: Urine
    cpt_code: "80305"

  standard_10_panel:
    name: "Standard 10-Panel"
    tests:
      - 5-Panel tests
      - Benzodiazepines (BZO)
      - Barbiturates (BAR)
      - Methadone (MTD)
      - Methaqualone (MQL)
      - Propoxyphene (PPX)
    specimen: Urine
    cpt_code: "80307"

  comprehensive_pain_management:
    name: "Comprehensive Pain Management"
    tests:
      - Opioids (natural, synthetic, semi-synthetic)
      - Benzodiazepines
      - Muscle Relaxants
      - Non-opioid analgesics
      - Stimulants
      - Sedatives
    specimen: Urine
    method: "LC-MS/MS"
    cpt_code: "G0483"
```

---

## Medication Categories & Test Mappings

### 1. Opioids / Opiates

**Natural Opiates**:
```yaml
morphine:
  tests:
    - Opiate Immunoassay (screening)
    - Morphine Confirmation (LC-MS/MS)
  detection_window: "2-3 days (urine)"
  therapeutic_range: "10-80 ng/mL (pain management)"

codeine:
  tests:
    - Opiate Immunoassay (screening)
    - Codeine Confirmation (LC-MS/MS)
  metabolizes_to: Morphine
  detection_window: "1-2 days"
  note: "Can cause positive morphine screen"
```

**Semi-Synthetic Opioids**:
```yaml
hydrocodone:
  brand_names: ["Vicodin", "Norco", "Lortab"]
  tests:
    - Hydrocodone Specific (LC-MS/MS)
    - May cross-react with opiate immunoassay
  metabolizes_to: Hydromorphone
  detection_window: "2-4 days"

oxycodone:
  brand_names: ["OxyContin", "Percocet", "Roxicodone"]
  tests:
    - Oxycodone Specific (LC-MS/MS)
    - Does NOT cross-react with opiate immunoassay
  metabolizes_to: Oxymorphone
  detection_window: "1-3 days"
  requires_specific_test: true
```

**Synthetic Opioids**:
```yaml
fentanyl:
  tests:
    - Fentanyl Specific (LC-MS/MS)
    - Does NOT cross-react with opiate immunoassay
  detection_window: "8-24 hours (urine)"
  note: "Requires specific testing"

methadone:
  tests:
    - Methadone Immunoassay
    - Methadone Confirmation (LC-MS/MS)
  metabolites: ["EDDP"]
  detection_window: "3-7 days"

buprenorphine:
  brand_names: ["Suboxone", "Subutex"]
  tests:
    - Buprenorphine Immunoassay
    - Buprenorphine Confirmation (LC-MS/MS)
  detection_window: "Up to 7 days"
  note: "Often tested in MAT programs"
```

---

### 2. Benzodiazepines

```yaml
diazepam:
  brand_names: ["Valium"]
  tests:
    - Benzodiazepine Immunoassay
    - Diazepam Confirmation (LC-MS/MS)
  metabolites: ["Nordiazepam", "Temazepam", "Oxazepam"]
  detection_window: "Up to 30 days (long half-life)"

alprazolam:
  brand_names: ["Xanax"]
  tests:
    - Benzodiazepine Immunoassay (may not detect well)
    - Alprazolam Specific (LC-MS/MS) recommended
  detection_window: "1-5 days"
  note: "Short half-life, may need specific test"

clonazepam:
  brand_names: ["Klonopin"]
  tests:
    - Benzodiazepine Immunoassay (limited detection)
    - 7-aminoclonazepam Confirmation (LC-MS/MS)
  detection_window: "Up to 7 days"

lorazepam:
  brand_names: ["Ativan"]
  tests:
    - Benzodiazepine Immunoassay
    - Lorazepam Confirmation (LC-MS/MS)
  detection_window: "1-6 days"
```

---

### 3. Stimulants

```yaml
amphetamine:
  tests:
    - Amphetamine Immunoassay
    - Amphetamine Confirmation (LC-MS/MS)
  detection_window: "1-3 days"
  note: "Metabolite of methamphetamine"

methamphetamine:
  tests:
    - Amphetamine Immunoassay
    - Methamphetamine Confirmation (LC-MS/MS)
  detection_window: "1-4 days"
  note: "Always test for amphetamine ratio"

methylphenidate:
  brand_names: ["Ritalin", "Concerta"]
  tests:
    - Methylphenidate Specific (LC-MS/MS)
    - Does NOT cross-react with amphetamine screen
  detection_window: "1-2 days"

cocaine:
  tests:
    - Cocaine Immunoassay
    - Benzoylecgonine Confirmation (LC-MS/MS)
  metabolite: "Benzoylecgonine"
  detection_window: "2-4 days"
```

---

### 4. Antidepressants

**Tricyclic Antidepressants (TCAs)**:
```yaml
amitriptyline:
  brand_names: ["Elavil"]
  tests:
    - TCA Immunoassay
    - Amitriptyline Confirmation (LC-MS/MS)
  detection_window: "2-7 days"
  therapeutic_range: "120-250 ng/mL"

nortriptyline:
  brand_names: ["Pamelor"]
  tests:
    - TCA Immunoassay
    - Nortriptyline Confirmation (LC-MS/MS)
  detection_window: "2-7 days"
  note: "Metabolite of amitriptyline"
```

**SSRIs** (Usually not in standard tox screens):
```yaml
sertraline:
  brand_names: ["Zoloft"]
  tests:
    - Sertraline Specific (LC-MS/MS)
  detection_window: "2-3 days"
  note: "Not in standard immunoassay panels"
```

---

### 5. Antipsychotics

```yaml
quetiapine:
  brand_names: ["Seroquel"]
  tests:
    - Quetiapine Specific (LC-MS/MS)
    - Can cause false positive TCA screen
  detection_window: "1-2 days"

olanzapine:
  brand_names: ["Zyprexa"]
  tests:
    - Olanzapine Specific (LC-MS/MS)
  detection_window: "Up to 7 days"
```

---

### 6. Muscle Relaxants

```yaml
carisoprodol:
  brand_names: ["Soma"]
  tests:
    - Carisoprodol/Meprobamate (LC-MS/MS)
  metabolizes_to: "Meprobamate"
  detection_window: "2-4 days"

cyclobenzaprine:
  brand_names: ["Flexeril"]
  tests:
    - Cyclobenzaprine Specific (LC-MS/MS)
    - Can cause false positive TCA screen
  detection_window: "3-8 days"
```

---

### 7. Cannabinoids

```yaml
thc:
  tests:
    - THC Immunoassay (THC-COOH)
    - THC-COOH Confirmation (LC-MS/MS)
  metabolite: "THC-COOH (11-nor-9-carboxy-THC)"
  detection_window:
    occasional_use: "1-3 days"
    regular_use: "Up to 30 days"
    chronic_use: "Up to 90 days"
  cutoff: "50 ng/mL (screening), 15 ng/mL (confirmation)"
```

---

### 8. Barbiturates

```yaml
phenobarbital:
  tests:
    - Barbiturate Immunoassay
    - Phenobarbital Confirmation (LC-MS/MS)
  detection_window: "Up to 14 days (long half-life)"
  therapeutic_range: "15-40 mcg/mL"

butalbital:
  brand_names: ["Fiorinal", "Fioricet"]
  tests:
    - Barbiturate Immunoassay
    - Butalbital Confirmation (LC-MS/MS)
  detection_window: "2-4 days"
```

---

### 9. Non-Opioid Analgesics

```yaml
tramadol:
  brand_names: ["Ultram"]
  tests:
    - Tramadol Specific (LC-MS/MS)
    - Does NOT show on opiate screen
  metabolites: ["O-desmethyltramadol"]
  detection_window: "1-4 days"

gabapentin:
  brand_names: ["Neurontin"]
  tests:
    - Gabapentin Specific (LC-MS/MS)
  detection_window: "1-2 days"
  note: "Increasingly monitored in pain management"

pregabalin:
  brand_names: ["Lyrica"]
  tests:
    - Pregabalin Specific (LC-MS/MS)
  detection_window: "1-2 days"
  controlled_substance: "Schedule V"
```

---

### 10. Sedative-Hypnotics

```yaml
zolpidem:
  brand_names: ["Ambien"]
  tests:
    - Zolpidem Specific (LC-MS/MS)
  detection_window: "24-48 hours"

zaleplon:
  brand_names: ["Sonata"]
  tests:
    - Zaleplon Specific (LC-MS/MS)
  detection_window: "12-24 hours"
```

---

## LCMS Comprehensive Panels

### Pain Management Panel (Typical)

```yaml
pain_management_panel:
  immunoassay_screening:
    - Opiates
    - Oxycodone
    - Benzodiazepines
    - Barbiturates
    - Amphetamines
    - Cocaine
    - THC
    - Methadone
    - Buprenorphine

  lcms_confirmation:
    opioids:
      - Codeine
      - Morphine
      - Hydrocodone
      - Hydromorphone
      - Oxycodone
      - Oxymorphone
      - Fentanyl
      - Norfentanyl
      - Methadone
      - EDDP
      - Buprenorphine
      - Norbuprenorphine
      - Tramadol

    benzodiazepines:
      - Alprazolam
      - Diazepam
      - Nordiazepam
      - Clonazepam
      - 7-aminoclonazepam
      - Lorazepam
      - Oxazepam
      - Temazepam

    other_analgesics:
      - Gabapentin
      - Pregabalin
      - Carisoprodol
      - Meprobamate
      - Cyclobenzaprine

    stimulants:
      - Amphetamine
      - Methamphetamine
      - MDMA
      - Cocaine
      - Benzoylecgonine
```

---

## Database Schema Design

### Entity Relationships

```
┌──────────────┐
│  Medication  │
│  (Reference) │
└──────┬───────┘
       │
       │ (many:many)
       │
       ▼
┌────────────────────────────┐
│ MedicationTestAssociation  │
├────────────────────────────┤
│ medication_uid             │
│ toxicology_test_uid        │
│ association_type           │
│ is_direct_detection        │
│ cross_reactivity_level     │
└──────┬─────────────────────┘
       │
       │ (many:1)
       ▼
┌──────────────────┐
│ ToxicologyTest   │
│ (Lab-Scoped)     │
└──────┬───────────┘
       │
       │ (many:1)
       ▼
┌──────────────────┐
│  TestPanel       │
│  (Lab-Scoped)    │
├──────────────────┤
│ panel_name       │
│ panel_type       │
│ tests[]          │
└──────────────────┘


┌──────────────────────┐
│ PatientMedicalHistory│  (From Phase 1-3)
├──────────────────────┤
│ treatment_history    │  JSONB array
│ [                    │
│   {drug: "Morphine"} ├──┐
│   {drug: "Xanax"}    │  │
│ ]                    │  │
└──────────────────────┘  │
                          │
                          │ (lookup)
                          ▼
                    ┌──────────────┐
                    │  Medication  │
                    └──────────────┘
                          │
                          ▼
              Recommended Tox Tests
```

---

## Use Cases

### 1. Determine Required Tests from Patient Medications

**Scenario**: Patient reports taking Oxycodone, Alprazolam, and Gabapentin

**Workflow**:
```python
# Get patient medications
medications = await PatientMedicalHistoryService().get_active_medications(patient_uid)

# For each medication, find required tests
recommended_tests = []
for med in medications:
    # Lookup medication in reference database
    medication = await MedicationService().get_by_name(med['drug'])

    # Get associated toxicology tests
    tests = await MedicationTestAssociation().get_tests_for_medication(medication.uid)
    recommended_tests.extend(tests)

# Result:
# - Oxycodone Specific (LC-MS/MS) - Does NOT show on opiate screen
# - Benzodiazepine Immunoassay + Alprazolam Confirmation
# - Gabapentin Specific (LC-MS/MS)
```

### 2. Interpret Test Results with Medication Context

**Scenario**: Opiate immunoassay POSITIVE, patient prescribed Tramadol

**Alert**: ⚠️ Tramadol does NOT cause positive opiate screen - investigate discrepancy

### 3. Insurance Pre-Authorization

**Scenario**: Select appropriate CPT codes based on medications

```python
# Pain management panel with 15 drug classes
if len(patient_medications) >= 3:
    cpt_code = "G0483"  # Comprehensive pain panel
else:
    cpt_code = "G0482"  # Limited pain panel
```

---

## Implementation Priority

### Phase 1: Core Medication Database
1. Medication entity with comprehensive fields
2. Pre-populate with common medications (~200-300 drugs)
3. Classification by drug class and therapeutic category

### Phase 2: Toxicology Tests
1. ToxicologyTest entity
2. Define standard immunoassay tests
3. Define LC-MS/MS confirmatory tests
4. Test panels (5-panel, 10-panel, pain management)

### Phase 3: Medication-Test Associations
1. MedicationTestAssociation many-to-many mapping
2. Populate associations for common drugs
3. Cross-reactivity documentation
4. False positive/negative tracking

### Phase 4: Integration
1. Link to PatientMedicalHistory medications
2. Auto-recommend tests based on patient meds
3. Result interpretation with medication context
4. Insurance authorization workflows

---

## Data Sources

**Medication Information**:
- FDA Drug Database
- RxNorm (NLM)
- DrugBank
- PubChem

**Test Information**:
- SAMHSA Guidelines
- CAP/CLIA Requirements
- Manufacturer IFUs
- AACC Toxicology Guidelines

---

**Document Status**: Requirements Complete
**Next**: Implementation of entities, repositories, and services
