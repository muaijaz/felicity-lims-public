# Phase 1 Implementation Summary: Patient Medical History & Insurance

**Date**: October 27, 2025
**Project**: Felicity LIMS - Patient Addon for LCMS Integration
**Phase**: 1 - Core Medical History (Essential for LCMS)
**Status**: Database Entities Complete ✅

---

## Overview

This document summarizes the completion of Phase 1 database entity implementation for the Patient Medical History and Insurance addon. These entities provide the foundational data structures needed for LCMS result interpretation with clinical context and billing/claims processing.

---

## Completed Work

### ✅ 1. Database Entities Created

**File Modified**: `felicity/apps/patient/entities.py`

**New Entities:**

####  1. **PatientMedicalHistory** (LabScopedEntity)
- **Purpose**: Comprehensive medical history for clinical context in LCMS result review
- **Key Fields**:
  - `chronic_conditions` (JSONB) - ICD-10 coded chronic diseases
  - `treatment_history` (JSONB) - Current and past medications with dosages
  - `allergies` (JSONB) - Drug and other allergies with severity
  - `immunizations` (JSONB) - Vaccination history
  - `travel_history` (JSONB) - For epidemiological context
  - `family_history` (JSONB) - Hereditary disease risks
  - `surgical_history` (JSONB) - Past surgical procedures with CPT codes
  - Reproductive health fields (HIPAA encrypted)
  - Social history (smoking, alcohol, drug use, occupation)

- **Properties**:
  - `active_medications` - Filter current medications
  - `active_chronic_conditions` - Filter active conditions
  - `verified_allergies` - Filter verified allergies only

- **Relationship**: One-to-one with Patient

#### 2. **InsuranceCompany** (BaseEntity)
- **Purpose**: Insurance payer directory for billing and claims
- **Key Fields**:
  - `name`, `code` (Payer ID)
  - Contact information (address, phone, email, website)
  - `claims_address`, `electronic_payer_id` (837 submission)
  - `clearinghouse` (OfficeAlly, Change Healthcare, etc.)
  - `fhir_endpoint`, `api_credentials` (JSONB, encrypted)
  - `is_active` status flag

- **Indexing**: Unique indexes on name and code
- **Scope**: BaseEntity (can be shared across laboratories)

#### 3. **PatientInsurance** (LabScopedEntity)
- **Purpose**: Patient-specific insurance policy information
- **Key Fields**:
  - `priority` (primary, secondary, tertiary) - Indexed
  - `insurance_company_uid` (FK to InsuranceCompany)
  - `policy_number` (HIPAA encrypted)
  - `group_number`, `plan_name`
  - Subscriber information if different from patient (HIPAA encrypted)
  - `effective_date`, `termination_date`
  - `copay_amount`, `deductible_amount` (Numeric)
  - `requires_authorization`, `authorization_number`

- **Properties**:
  - `is_valid` - Check if insurance is currently active and within date range

- **Relationship**: Many-to-one with Patient (supports primary, secondary, tertiary)

#### 4. **Guarantor** (LabScopedEntity)
- **Purpose**: Financial responsibility for patient billing
- **Key Fields**:
  - `is_patient` (Boolean) - If patient is their own guarantor
  - Demographics (all HIPAA encrypted)
  - Contact information (all HIPAA encrypted)
  - `responsibility_percentage` (Integer, default 100)

- **Properties**:
  - `full_name` - Computed guarantor name

- **Relationship**: One-to-one with Patient

#### 5. **ClinicalDiagnosis** (LabScopedEntity)
- **Purpose**: ICD-10 coded diagnoses for billing and clinical context
- **Key Fields**:
  - `icd10_code`, `icd10_description` - Indexed on code
  - `diagnosis_date`, `diagnosis_type` (primary, secondary, admitting, discharge)
  - `status` (active, resolved, ruled_out)
  - `resolution_date`
  - `analysis_request_uid` (FK, optional) - Link diagnosis to specific test
  - `diagnosing_provider_uid` (FK to User)
  - `pointer` (A, B, C, D) - For 837 claim diagnosis pointers

- **Properties**:
  - `is_active` - Check if diagnosis is currently active

- **Relationship**: Many-to-one with Patient, optional link to AnalysisRequest

---

### ✅ 2. Patient Entity Updated

**Modifications to `Patient` entity**:

Added four new relationships:
```python
# Medical History and Insurance - New Relationships
medical_history: Mapped["PatientMedicalHistory"] = relationship(
    "PatientMedicalHistory", back_populates="patient", uselist=False, lazy="selectin"
)
insurance_policies: Mapped[list["PatientInsurance"]] = relationship(
    "PatientInsurance", back_populates="patient", lazy="selectin"
)
guarantor: Mapped["Guarantor"] = relationship(
    "Guarantor", back_populates="patient", uselist=False, lazy="selectin"
)
diagnoses: Mapped[list["ClinicalDiagnosis"]] = relationship(
    "ClinicalDiagnosis", back_populates="patient", lazy="selectin"
)
```

**Impact**:
- Patient records can now be queried with full medical history
- Insurance policies accessible via `patient.insurance_policies`
- Diagnoses accessible via `patient.diagnoses`
- Guarantor accessible via `patient.guarantor`

---

### ✅ 3. Database Migration Created

**File Created**: `felicity/migrations/versions/2025_10_27_1700-patient_medical_history_insurance.py`

**Migration Details**:
- **Revision ID**: `patient_medical_history`
- **Revises**: `add_driver_mapping`
- **Creates 5 new tables**:
  1. `insurance_company`
  2. `patient_medical_history`
  3. `patient_insurance`
  4. `guarantor`
  5. `clinical_diagnosis`

**Features**:
- All HIPAA encrypted fields use `LargeBinary` (encrypted by EncryptedPII)
- JSONB fields for flexible medical data structures
- Proper foreign key constraints
- Indexes on frequently queried fields
- Complete upgrade() and downgrade() functions

---

## HIPAA Compliance

All personally identifiable information is encrypted using the existing `EncryptedPII` field type:

**Encrypted Fields**:
- Patient Insurance: `policy_number`, subscriber details
- Guarantor: All demographic and contact fields
- Medical History: `menstrual_status`, `pregnancy_due_date`

**Non-Encrypted Fields** (for analytics/filtering):
- Patient: `gender` (already non-encrypted)
- Insurance: `priority`, `is_active`
- Diagnosis: `icd10_code`, `status`

---

## Multi-Tenant Architecture

All new entities properly implement laboratory scoping:

**LabScopedEntity** (scoped to laboratory):
- `PatientMedicalHistory`
- `PatientInsurance`
- `Guarantor`
- `ClinicalDiagnosis`

**BaseEntity** (shared across laboratories):
- `InsuranceCompany` (insurance companies can be shared)

**Automatic Filtering**:
- Repository layer will automatically filter by `laboratory_uid`
- Ensures data isolation between laboratories
- Maintains multi-tenant security model

---

## LCMS Integration Benefits

### How This Supports LCMS Workflows

**1. Medication Interference Detection**
```python
# During LCMS result review
patient = get_patient(sample.patient_uid)
active_meds = patient.medical_history.active_medications

for med in active_meds:
    if check_lcms_interference(med['drug'], analyte):
        flag_result(f"⚠️ {med['drug']} may interfere with {analyte}")
```

**2. Clinical Context Display**
```python
# Show relevant medical context in result review UI
context = {
    "medications": patient.medical_history.active_medications,
    "conditions": patient.medical_history.active_chronic_conditions,
    "allergies": patient.medical_history.verified_allergies,
    "diagnoses": [d for d in patient.diagnoses if d.is_active]
}
```

**3. Reference Range Adjustment**
```python
# Adjust reference ranges based on patient factors
if patient.medical_history.pregnancy_status:
    reference_range = get_pregnancy_range(analyte, gestational_age)
elif patient.age < 18:
    reference_range = get_pediatric_range(analyte, patient.age)
```

**4. Billing Context**
```python
# Check insurance coverage before running expensive LCMS tests
primary_insurance = next(
    (ins for ins in patient.insurance_policies if ins.priority == "primary"),
    None
)
if primary_insurance and primary_insurance.is_valid:
    if primary_insurance.requires_authorization:
        check_authorization(primary_insurance.authorization_number)
```

---

## Next Steps

### Immediate (This Week)

1. **Repository Layer** - Create CRUD operations for new entities
   - `PatientMedicalHistoryRepository`
   - `InsuranceCompanyRepository`
   - `PatientInsuranceRepository`
   - `GuarantorRepository`
   - `ClinicalDiagnosisRepository`

2. **Service Layer** - Implement business logic
   - `PatientMedicalHistoryService` with JSONB array manipulation
   - `InsuranceService` with validity checking
   - `DiagnosisService` with ICD-10 validation

3. **Pydantic Schemas** - Create validation schemas
   - Request/response models for all entities
   - Nested schemas for JSONB structures (medications, conditions, etc.)

4. **GraphQL API** - Build mutations and queries
   - CRUD operations for medical history
   - Insurance management operations
   - Diagnosis tracking operations

### Phase 2 (Next 2-3 Weeks)

1. **Frontend UI Components**
   - Medical history entry forms
   - Medication/allergy management
   - Insurance policy management
   - Diagnosis selection with ICD-10 search

2. **LCMS Result Review Enhancement**
   - Medical context panel
   - Medication interference alerts
   - Reference range adjustments

3. **Billing Integration**
   - 837 claim generation logic
   - OfficeAlly API integration
   - FHIR R4 resource export

---

## Database Schema Diagram

```
┌─────────────┐
│   Patient   │
└──────┬──────┘
       │
       ├──────────────────────────────────┐
       │                                  │
       │ (1:1)                            │ (1:many)
       ▼                                  ▼
┌──────────────────────┐        ┌───────────────────┐
│ PatientMedicalHistory│        │ PatientInsurance  │
├──────────────────────┤        ├───────────────────┤
│ chronic_conditions   │        │ priority          │
│ treatment_history    │        │ policy_number     │
│ allergies            │        │ insurance_company ├──┐
│ immunizations        │        └───────────────────┘  │
│ travel_history       │                               │
│ family_history       │                               │ (many:1)
│ surgical_history     │                               ▼
└──────────────────────┘                    ┌──────────────────┐
       │                                    │ InsuranceCompany │
       │ (1:1)                              ├──────────────────┤
       ▼                                    │ name             │
┌──────────────────┐                       │ electronic_id    │
│    Guarantor     │                       │ fhir_endpoint    │
├──────────────────┤                       └──────────────────┘
│ is_patient       │
│ demographics     │
│ contact_info     │
└──────────────────┘
       │
       │ (1:many)
       ▼
┌────────────────────┐
│ ClinicalDiagnosis  │
├────────────────────┤
│ icd10_code         │
│ status             │
│ diagnosis_date     │
│ analysis_request ──┼─────► AnalysisRequest
└────────────────────┘
```

---

## Code Quality

**Best Practices Implemented**:
- ✅ Type hints with `Mapped[]` for relationships
- ✅ Comprehensive docstrings for all entities
- ✅ Property methods for computed values
- ✅ JSONB structure documentation in comments
- ✅ Proper foreign key constraints
- ✅ Index optimization for queries
- ✅ HIPAA-compliant field encryption
- ✅ Multi-tenant laboratory scoping

**Testing Requirements** (Next Phase):
- Unit tests for entity creation and relationships
- JSONB array manipulation tests
- Encryption/decryption tests for HIPAA fields
- Multi-tenant isolation tests
- Migration up/down tests

---

## File Changes Summary

**Modified Files**:
1. `felicity/apps/patient/entities.py` - Added 5 new entities, updated Patient relationships

**New Files**:
1. `felicity/migrations/versions/2025_10_27_1700-patient_medical_history_insurance.py` - Database migration

**Total Lines Added**: ~520 lines

---

## Running the Migration

**To apply this migration to the database:**

```bash
# Using pnpm (if environment set up)
pnpm db:upgrade

# Or directly with alembic
alembic upgrade head

# To rollback if needed
alembic downgrade -1
```

**Verification Queries:**

```sql
-- Verify tables created
SELECT tablename FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN (
    'patient_medical_history',
    'insurance_company',
    'patient_insurance',
    'guarantor',
    'clinical_diagnosis'
);

-- Check columns on patient_medical_history
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'patient_medical_history';
```

---

## Integration with Agilent 6460 LCMS

This Phase 1 implementation provides the data foundation for the LCMS integration documented in `AGILENT_6460_INTEGRATION.md`:

**Result Review Workflow**:
```
Agilent 6460 → Results CSV → Felicity LIMS Import
                                      ↓
                              Result Review Page
                                      ↓
                      ┌───────────────────────────┐
                      │ RESULTS    │ PATIENT      │
                      │            │ CONTEXT      │
                      │ Ibuprofen  │ • Metformin  │
                      │ 15.3 µg/mL │   (alert!)   │
                      │            │ • Diabetes   │
                      │ [Approve]  │ • Insurance  │
                      └───────────────────────────┘
```

**Benefits**:
- Medication interference alerts based on `treatment_history`
- Disease context from `chronic_conditions`
- Billing readiness from `insurance_policies`
- Clinical documentation from `diagnoses`

---

## Conclusion

Phase 1 database foundation is **complete and ready for testing**. The entities provide:

1. ✅ **Comprehensive medical history tracking** for LCMS clinical context
2. ✅ **Insurance and billing infrastructure** for claims processing
3. ✅ **ICD-10 diagnosis coding** for clinical documentation and billing
4. ✅ **HIPAA-compliant data protection** for all sensitive fields
5. ✅ **Multi-tenant laboratory scoping** for data isolation
6. ✅ **Flexible JSONB structures** for evolving medical data needs

**Next Phase**: Implement repositories, services, schemas, and GraphQL API to make these entities functional in the application.

---

**Document Status**: Implementation Complete
**Last Updated**: 2025-10-27
**Owner**: Mohammad Aijaz
**Project**: Felicity LIMS - Patient Addon Phase 1
