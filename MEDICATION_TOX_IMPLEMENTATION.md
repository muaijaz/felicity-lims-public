# Medication & Toxicology Test Reference System Implementation

**Date**: October 27, 2025
**Status**: Core Infrastructure Complete ✅
**Module**: `felicity/apps/reference/`

---

## Overview

Comprehensive medication and toxicology test reference database for LCMS workflows, therapeutic drug monitoring, and toxicology screening panel selection.

---

## ✅ Completed Components

### 1. Database Entities (`entities.py` - 388 lines)

#### Medication Entity (BaseEntity - Shared Reference)
```python
class Medication(BaseEntity):
    """
    Comprehensive medication reference with:
    - Drug identification (generic, brand names, chemical properties)
    - Classification codes (ATC, NDC, RxCUI)
    - Clinical information (indications, contraindications, dosing)
    - Metabolism & pharmacokinetics
    - Toxicology testing requirements
    """
```

**Key Fields**:
- **Identification**: name, brand_names, chemical_name, molecular_formula, CAS number
- **Classification**: atc_code, ndc_codes, rxcui, drug_class, therapeutic_category
- **Clinical**: mechanism_of_action, indications, contraindications, half_life
- **Dosing**: typical_dose_range, dosage_forms, routes_of_administration
- **Metabolism**: primary_metabolism, active_metabolites, excretion_route
- **Toxicology**: is_controlled_substance, dea_schedule, therapeutic_window, toxic_level
- **Testing**: commonly_screened, requires_confirmation, detection_windows (urine/blood/oral fluid)
- **Regulatory**: fda_approved, approval_date, black_box_warning, pregnancy_category

**Properties**:
- `all_names`: Returns generic + brand + synonym names
- `requires_specific_test`: Calculates if specific testing needed

#### ToxicologyTest Entity (LabScopedEntity)
```python
class ToxicologyTest(LabScopedEntity):
    """
    Laboratory-specific toxicology test definitions:
    - Screening tests (immunoassay)
    - Confirmation tests (LC-MS/MS, GC-MS)
    - Test panels (5-panel, 10-panel, pain management)
    """
```

**Key Fields**:
- **Identification**: test_name, test_code, cpt_code, loinc_code
- **Classification**: test_category, test_type, specimen_type
- **Analytical**: method, instrument_type, analytical_range, LOD, LOQ
- **Performance**: cutoff_value, confirmation_cutoff, turnaround_time
- **Clinical**: clinical_utility, interpretation_notes
- **Panel**: panel_name, is_part_of_panel, panel_components
- **Regulatory**: clia_complexity, requires_medical_necessity
- **Business**: test_price, is_stat_available, is_send_out

**Properties**:
- `is_screening_test`: Identifies immunoassay screens
- `is_confirmation_test`: Identifies LC-MS/MS confirmatory tests

#### MedicationTestAssociation Entity (BaseEntity - Shared Reference)
```python
class MedicationTestAssociation(BaseEntity):
    """
    Many-to-many mapping between medications and toxicology tests:
    - Direct detection vs metabolite detection
    - Cross-reactivity information
    - False positive/negative tracking
    - Test recommendations
    """
```

**Key Fields**:
- **Association**: medication_uid, toxicology_test_uid, association_type
- **Detection**: is_direct_detection, detected_as, detection_sensitivity, cross_reactivity_level
- **Clinical**: clinical_significance, interpretation_guidance
- **Interference**: causes_false_positive, causes_false_negative, interference_notes
- **Priority**: is_preferred_test, is_confirmatory_test, requires_additional_testing
- **Quantitative**: expected_concentration_range, therapeutic_concentration

**Properties**:
- `requires_confirmation`: Calculates if confirmatory testing needed

**Indexes Created**:
- Performance-optimized indexes on key query fields
- Composite indexes for common query patterns

---

### 2. Repository Layer (`repository.py` - 226 lines)

#### MedicationRepository
```python
class MedicationRepository(BaseRepository[Medication]):
    """Data access for medication reference."""
```

**Key Methods**:
- `get_by_name(name)` - Exact match lookup
- `search_by_name(query, limit)` - Fuzzy search across name, brands, synonyms
- `get_by_drug_class(drug_class)` - Filter by therapeutic class
- `get_by_therapeutic_category(category)` - Filter by category
- `get_controlled_substances(dea_schedule)` - Get controlled substances
- `get_commonly_screened()` - Medications in standard tox panels
- `get_by_atc_code(atc_code)` - Lookup by ATC code
- `get_by_rxcui(rxcui)` - Lookup by RxNorm identifier

#### ToxicologyTestRepository
```python
class ToxicologyTestRepository(BaseRepository[ToxicologyTest]):
    """Data access for toxicology tests (laboratory-scoped)."""
```

**Key Methods**:
- `get_by_test_code(test_code, laboratory_uid)` - Lookup by code
- `get_by_category(test_category, laboratory_uid)` - Filter by category
- `get_by_specimen_type(specimen_type, laboratory_uid)` - Filter by specimen
- `get_screening_tests(laboratory_uid)` - Get immunoassay screens
- `get_confirmation_tests(laboratory_uid)` - Get LC-MS/MS confirmations
- `get_by_panel(panel_name, laboratory_uid)` - Get panel tests
- `get_available_panels(laboratory_uid)` - List available panels
- `get_stat_tests(laboratory_uid)` - Get STAT-eligible tests

#### MedicationTestAssociationRepository
```python
class MedicationTestAssociationRepository(BaseRepository[MedicationTestAssociation]):
    """Data access for medication-test mappings."""
```

**Key Methods**:
- `get_tests_for_medication(medication_uid)` - Tests that detect medication
- `get_medications_for_test(test_uid)` - Medications detected by test
- `get_preferred_tests_for_medication(medication_uid)` - Recommended tests
- `get_by_association_type(medication_uid, type)` - Filter by type (primary/metabolite/cross-reactive)
- `get_false_positive_risks(test_uid)` - Medications causing false positives
- `get_confirmatory_tests_needed(medication_uid)` - Tests requiring confirmation
- `get_by_medication_names(names)` - Bulk lookup for patient med lists

---

## 🔄 Integration with Patient Medical History

### Use Case 1: Recommend Tests Based on Patient Medications

**Scenario**: Patient reports taking Oxycodone, Alprazolam, and Gabapentin

**Workflow**:
```python
from felicity.apps.reference.services import MedicationService, MedicationTestAssociationService
from felicity.apps.patient.services import PatientMedicalHistoryService

# Get patient's active medications
patient_meds = await PatientMedicalHistoryService().get_active_medications(patient_uid)
# Returns: [{"drug": "Oxycodone"}, {"drug": "Alprazolam"}, {"drug": "Gabapentin"}]

# Get medication names
med_names = [med['drug'] for med in patient_meds]

# Get recommended tests
associations = await MedicationTestAssociationService().get_tests_for_medications(med_names)

# Result includes:
# - Oxycodone Specific (LC-MS/MS) - DOES NOT show on opiate screen
# - Benzodiazepine Screen + Alprazolam Confirmation (short-acting benzo)
# - Gabapentin Specific (LC-MS/MS) - Increasingly monitored in pain management
```

### Use Case 2: Detect Test-Medication Discrepancies

**Scenario**: Opiate immunoassay POSITIVE, but patient only prescribed Tramadol

**Alert Logic**:
```python
# Check if patient's medications explain positive result
tramadol = await MedicationService().get_by_name("Tramadol")
opiate_assoc = await MedicationTestAssociationService().get_for_medication_and_test(
    tramadol.uid, opiate_immunoassay_uid
)

if not opiate_assoc or not opiate_assoc.is_direct_detection:
    # ALERT: Tramadol does NOT cause positive opiate screen
    # Investigate for undisclosed opioid use
    create_alert(patient_uid, "Opiate positive but Tramadol does not cross-react")
```

### Use Case 3: Select Appropriate Test Panel

**Scenario**: Pain management patient with multiple medications

**Panel Selection Logic**:
```python
# Get patient medications
patient_meds = await PatientMedicalHistoryService().get_active_medications(patient_uid)

# Determine panel complexity
if len(patient_meds) >= 5:
    # Comprehensive pain management panel
    panel = await ToxicologyTestService().get_by_panel_name(
        "Comprehensive Pain Management", laboratory_uid
    )
elif len(patient_meds) >= 3:
    # Standard pain management panel
    panel = await ToxicologyTestService().get_by_panel_name(
        "Standard Pain Management", laboratory_uid
    )
else:
    # Individual test selection
    tests = await get_individual_tests(patient_meds, laboratory_uid)
```

---

## 📊 Common Drug Categories & Test Mappings

### Opioids

**Natural Opiates**:
- Morphine → Opiate Screen + Morphine Confirmation
- Codeine → Opiate Screen + Codeine Confirmation (metabolizes to morphine)

**Semi-Synthetic**:
- Hydrocodone → Hydrocodone Specific (may cross-react with opiate screen)
- Oxycodone → Oxycodone Specific (does NOT cross-react, requires specific test)
- Hydromorphone → Hydromorphone Specific

**Synthetic**:
- Fentanyl → Fentanyl Specific (does NOT cross-react with opiate screen)
- Methadone → Methadone Screen + Confirmation (EDDP metabolite)
- Buprenorphine → Buprenorphine Screen + Confirmation (MAT programs)
- Tramadol → Tramadol Specific (does NOT cross-react with opiate screen)

### Benzodiazepines

- Diazepam → Benzo Screen + Confirmation (long half-life, 30 day detection)
- Alprazolam → Benzo Screen (may not detect well) + Alprazolam Specific recommended
- Clonazepam → 7-aminoclonazepam Specific (limited benzo screen detection)
- Lorazepam → Benzo Screen + Lorazepam Confirmation

### Stimulants

- Amphetamine → Amphetamine Screen + Confirmation
- Methamphetamine → Amphetamine Screen + Methamphetamine Confirmation (check amp/meth ratio)
- Methylphenidate → Methylphenidate Specific (does NOT cross-react with amphetamine)
- Cocaine → Cocaine Screen (benzoylecgonine metabolite) + Confirmation

### Non-Opioid Analgesics

- Gabapentin → Gabapentin Specific (not in standard panels)
- Pregabalin → Pregabalin Specific (not in standard panels)
- Carisoprodol → Carisoprodol/Meprobamate (metabolizes to meprobamate)
- Cyclobenzaprine → Cyclobenzaprine Specific (can cause false positive TCA)

---

## 🔬 Standard Test Panels

### DOT/Workplace 5-Panel (80305)
- Amphetamines
- Cocaine Metabolites
- Marijuana Metabolites (THC)
- Opiates
- Phencyclidine (PCP)

### Standard 10-Panel (80307)
- 5-Panel tests +
- Benzodiazepines
- Barbiturates
- Methadone
- Methaqualone
- Propoxyphene

### Comprehensive Pain Management (G0483)
**Immunoassay Screening**:
- Opiates, Oxycodone, Benzodiazepines, Barbiturates, Amphetamines
- Cocaine, THC, Methadone, Buprenorphine

**LC-MS/MS Confirmation** (15-22 drug classes):
- Opioids: Codeine, Morphine, Hydrocodone, Hydromorphone, Oxycodone, Oxymorphone, Fentanyl, Methadone, Buprenorphine, Tramadol
- Benzodiazepines: Alprazolam, Diazepam, Clonazepam, Lorazepam, Oxazepam, Temazepam
- Other: Gabapentin, Pregabalin, Carisoprodol, Cyclobenzaprine

---

## 🎯 Next Steps

### Immediate (Complete Core System)

1. **Service Layer** - Create `services.py` with:
   - `MedicationService`
   - `ToxicologyTestService`
   - `MedicationTestAssociationService`
   - Business logic for recommendations

2. **Pydantic Schemas** - Create `schemas.py` with:
   - Request/response models
   - Nested schemas for JSONB

3. **GraphQL API** - Create API layer:
   - Types, queries, mutations
   - Integration with patient module

4. **Database Migration** - Create Alembic migration:
   - Three new tables
   - Indexes for performance

5. **Seed Data** - Create seeding script:
   - ~200-300 common medications
   - Standard toxicology test panels
   - Medication-test associations

### Phase 2: Data Population

1. **Medication Database** (~200-300 drugs):
   - All opioids (natural, semi-synthetic, synthetic)
   - All benzodiazepines
   - Stimulants (amphetamines, methylphenidate, cocaine)
   - Antidepressants (TCAs, SSRIs, SNRIs)
   - Antipsychotics
   - Muscle relaxants
   - Barbiturates
   - Cannabinoids
   - Non-opioid analgesics

2. **Toxicology Tests** (per laboratory):
   - Immunoassay screening tests (8-12 tests)
   - LC-MS/MS confirmation tests (20-30 analytes)
   - Standard panels (5-panel, 10-panel, pain management)

3. **Associations** (~500-1000 mappings):
   - Primary detection relationships
   - Metabolite detection
   - Cross-reactivity patterns
   - False positive/negative documentation

### Phase 3: Frontend Integration

1. **Medication Lookup**:
   - Search medications by name
   - Display drug class and properties
   - Show recommended tests

2. **Test Selection Assistant**:
   - Based on patient medications
   - Panel recommendations
   - Cost optimization

3. **Result Interpretation**:
   - Display expected vs actual results
   - Medication context for interpretation
   - Alert for discrepancies

4. **Ordering Workflow**:
   - Auto-suggest tests based on patient meds
   - Validate medical necessity
   - Generate appropriate CPT codes

---

## 📈 Benefits

### For LCMS Workflows
✅ **Intelligent Test Selection**: Recommend appropriate tests based on patient medications
✅ **Method Selection**: Know which analytes require LC-MS/MS vs immunoassay
✅ **Result Interpretation**: Understand expected findings based on medication history
✅ **Interference Detection**: Alert for medications causing false positives

### For Therapeutic Drug Monitoring
✅ **Therapeutic Ranges**: Reference therapeutic and toxic levels
✅ **Monitoring Schedules**: Know detection windows for compliance testing
✅ **Metabolite Tracking**: Understand parent drug vs metabolite relationships

### For Billing & Compliance
✅ **CPT Code Selection**: Appropriate codes based on test complexity
✅ **Medical Necessity**: Documentation for insurance authorization
✅ **Panel Optimization**: Cost-effective test panel selection

### For Clinical Decision Support
✅ **Drug Interactions**: Identify potential interactions affecting test results
✅ **Cross-Reactivity**: Know which drugs affect which tests
✅ **Confirmatory Testing**: Automatically recommend confirmatory tests when needed

---

## 📁 File Structure

```
felicity/apps/reference/
├── __init__.py              (✅ Complete - 3 lines)
├── entities.py              (✅ Complete - 388 lines)
│   ├── Medication
│   ├── ToxicologyTest
│   └── MedicationTestAssociation
├── repository.py            (✅ Complete - 226 lines)
│   ├── MedicationRepository
│   ├── ToxicologyTestRepository
│   └── MedicationTestAssociationRepository
├── services.py              (⏭️ Next - ~250 lines)
│   ├── MedicationService
│   ├── ToxicologyTestService
│   └── MedicationTestAssociationService
├── schemas.py               (⏭️ Next - ~200 lines)
│   └── Pydantic models
└── seed_data.py             (⏭️ Next - ~500 lines)
    └── Common medications & tests

felicity/api/gql/reference/
├── types.py                 (⏭️ Next - ~150 lines)
├── query.py                 (⏭️ Next - ~100 lines)
└── mutations.py             (⏭️ Next - ~100 lines)

felicity/migrations/versions/
└── YYYY_MM_DD_HHMM-medication_toxicology_reference.py  (⏭️ Next)
```

---

## 📊 Database Schema

```
┌──────────────┐
│  Medication  │  (BaseEntity - Shared Reference)
│  (Reference) │
└──────┬───────┘
       │
       │ (many:many)
       │
       ▼
┌────────────────────────────┐
│ MedicationTestAssociation  │  (BaseEntity - Shared Reference)
├────────────────────────────┤
│ medication_uid             │
│ toxicology_test_uid        │
│ association_type           │
│ is_direct_detection        │
│ cross_reactivity_level     │
│ causes_false_positive      │
│ is_preferred_test          │
└──────┬─────────────────────┘
       │
       │ (many:1)
       ▼
┌──────────────────┐
│ ToxicologyTest   │  (LabScopedEntity)
│ (Lab-Scoped)     │
├──────────────────┤
│ test_name        │
│ test_code        │
│ test_category    │
│ specimen_type    │
│ method           │
│ panel_name       │
└──────────────────┘


Integration with Patient Module:
┌──────────────────────┐
│ PatientMedicalHistory│  (Existing from Phase 1-3)
├──────────────────────┤
│ treatment_history    │  JSONB array
│ [                    │
│   {drug: "Morphine"} ├──┐
│   {drug: "Xanax"}    │  │
│ ]                    │  │
└──────────────────────┘  │
                          │
                          │ (lookup by name)
                          ▼
                    ┌──────────────┐
                    │  Medication  │
                    └──────┬───────┘
                           │
                           │ (associations)
                           ▼
                    ┌──────────────────┐
                    │ ToxicologyTest   │
                    │                  │
                    │ Recommended      │
                    │ Tests            │
                    └──────────────────┘
```

---

**Document Status**: Core Infrastructure Complete
**Lines Implemented**: 617 lines (entities + repositories)
**Next**: Services, schemas, GraphQL API, migration, seed data
**Estimated Remaining**: ~1,200 lines
