# Patient Addon Requirements for Felicity LIMS

**Date**: October 27, 2025
**Purpose**: Define comprehensive patient addon with medical history for LCMS integration and billing compliance

---

## Executive Summary

This document outlines requirements for extending Felicity LIMS patient management to support:
1. **Medical History Tracking** - Essential for LCMS result analysis and clinical interpretation
2. **Billing/Coding Compliance** - Support for 837 claims with CPT/ICD-10/HCPCS codes
3. **Insurance Integration** - OfficeAlly/FHIR API compatibility for claims processing
4. **LCMS Clinical Context** - Link patient medical data to mass spectrometry results

---

## Current Felicity Patient Implementation

### Existing Fields (entities.py:35-96)

**Identity & Demographics:**
- `client_patient_id` - Client-assigned identifier (unique, required)
- `patient_id` - System-generated identifier (unique)
- `first_name`, `middle_name`, `last_name` - HIPAA encrypted
- `gender` - Unencrypted for analytics
- `age`, `date_of_birth` - DOB is HIPAA encrypted
- `age_dob_estimated` - Boolean flag

**Contact Information (HIPAA Encrypted):**
- `phone_mobile`, `phone_home`
- `email`
- `consent_sms` - SMS consent flag

**Geographic:**
- `district_uid`, `province_uid`, `country_uid` - Location hierarchy

**System Fields:**
- `client_uid` - Laboratory/client association
- `internal_use` - Test patient flag
- `active` - Status flag
- `metadata_snapshot` - JSONB for flexible data

**Relationships:**
- `identifications` - Multiple ID types (SSN, passport, etc.) with HIPAA encryption

### Strengths
✅ HIPAA-compliant field-level encryption
✅ Multi-tenant laboratory scoping
✅ Flexible identification system
✅ Geographic hierarchy support
✅ Comprehensive audit trails (LabScopedEntity)

### Gaps for LCMS & Billing
❌ No medical history tracking
❌ No insurance information
❌ No clinical conditions/diagnoses
❌ No medication/allergy tracking
❌ No treatment history
❌ No billing codes (CPT/ICD-10)
❌ No guarantor information

---

## SENAITE.Patient/Bika.Health Analysis

### Key Medical History Features

**Treatment & Medications:**
```python
TreatmentHistory = RecordsField([
    Drug,           # Medication name
    StartDate,      # Treatment start
    EndDate,        # Treatment end (optional)
    TreatmentType   # Type of treatment
])

Allergies = RecordsField([
    DrugProhibition,  # Severity/type
    Drug,             # Allergen
    Remarks           # Clinical notes
])
```

**Immunization History:**
```python
ImmunizationHistory = RecordsField([
    EPINumber,          # Immunization program ID
    Immunization,       # Vaccine name
    VaccinationCenter,  # Administration location
    Date,               # Vaccination date
    Remarks             # Clinical notes
])
```

**Chronic Conditions:**
```python
ChronicConditions = RecordsField([
    Code,         # ICD-10 code
    Title,        # Condition name
    Description,  # Clinical details
    OnsetDate,    # Diagnosis date
    EndDate       # Resolution date (optional)
])
```

**Travel History:**
```python
TravelHistory = RecordsField([
    TripStartDate,
    TripEndDate,
    Country,
    Location,
    Remarks  # Epidemiological significance
])
```

**Insurance & Billing:**
```python
# Insurance Company reference
InsuranceCompany = ReferenceField
InsuranceNumber = TextField
InvoiceToInsuranceCompany = BooleanField

# Guarantor (if patient != guarantor)
PatientAsGuarantor = BooleanField(default=True)
GuarantorID, GuarantorSurname, GuarantorFirstname
GuarantorPostalAddress
GuarantorBusinessPhone, GuarantorHomePhone, GuarantorMobilePhone
```

**Clinical Analytics:**
- Computed sample counts (total, cancelled, ongoing, published)
- Sample ratios for operational analytics
- Batch (clinical case) associations

---

## Healthcare Billing Requirements (837 Format)

### Required Patient Fields for Claims

**Patient Demographics (Loop 2010CA):**
- Patient Last Name, First Name, Middle Initial
- Patient Address (Street, City, State, ZIP)
- Date of Birth (format: YYYYMMDD)
- Gender Code (M/F/U)
- Patient ID (Member ID from insurance card)

**Subscriber Information (Loop 2010BA):**
- Subscriber Name (if different from patient)
- Subscriber ID
- Subscriber Date of Birth
- Subscriber Gender
- Relationship to Patient

**Insurance Information:**
- Insurance Company Name
- Insurance Policy Number
- Group Number
- Authorization Number (if required)
- Primary/Secondary/Tertiary Payer indicators

**Diagnosis Codes (Loop 2300):**
- ICD-10-CM codes (up to 12 per claim)
- Diagnosis pointers (ABCD, max 4 per service line)
- Must use highest level of specificity

**Service Lines (Loop 2400):**
- CPT/HCPCS codes for procedures
- Modifiers (if applicable)
- Service Date
- Units
- Charges
- Place of Service (2-digit code)
- Diagnosis Pointers

**Provider Information:**
- NPI (National Provider Identifier) - 10 digits
- Rendering Provider NPI
- Referring Provider NPI (if applicable)
- Facility NPI

**Claim Header Data:**
- Claim Filing Indicator Code
- Patient Control Number
- Total Claim Charge Amount

---

## OfficeAlly/FHIR API Integration

### FHIR Patient Resource (R4)

**Core Demographics:**
```json
{
  "resourceType": "Patient",
  "identifier": [
    {
      "system": "http://hospital.org/patients",
      "value": "12345"
    }
  ],
  "name": [{
    "use": "official",
    "family": "Doe",
    "given": ["John", "Michael"]
  }],
  "gender": "male",
  "birthDate": "1980-01-15",
  "address": [{
    "line": ["123 Main St"],
    "city": "Springfield",
    "state": "IL",
    "postalCode": "62701",
    "country": "US"
  }],
  "telecom": [
    {
      "system": "phone",
      "value": "(555) 123-4567",
      "use": "mobile"
    },
    {
      "system": "email",
      "value": "john.doe@example.com"
    }
  ]
}
```

### FHIR Coverage Resource (Insurance)

```json
{
  "resourceType": "Coverage",
  "identifier": [{
    "system": "http://insurance.com/memberId",
    "value": "ABC123456"
  }],
  "status": "active",
  "type": {
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
      "code": "HIP",
      "display": "health insurance plan policy"
    }]
  },
  "subscriber": {
    "reference": "Patient/12345"
  },
  "beneficiary": {
    "reference": "Patient/12345"
  },
  "relationship": {
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/subscriber-relationship",
      "code": "self"
    }]
  },
  "payor": [{
    "reference": "Organization/insurance-co-123"
  }],
  "class": [{
    "type": {
      "coding": [{
        "system": "http://terminology.hl7.org/CodeSystem/coverage-class",
        "code": "group"
      }]
    },
    "value": "GRP-12345"
  }]
}
```

---

## Proposed Patient Addon Schema

### New Entities

#### 1. PatientMedicalHistory (LabScopedEntity)

```python
class PatientMedicalHistory(LabScopedEntity):
    __tablename__ = "patient_medical_history"

    patient_uid = Column(String, ForeignKey("patient.uid"), nullable=False)
    patient = relationship("Patient", back_populates="medical_history")

    # Chronic Conditions - JSONB array
    chronic_conditions = Column(JSONB, nullable=True)
    # [{
    #   "icd10_code": "E11.9",
    #   "title": "Type 2 Diabetes Mellitus",
    #   "description": "Controlled with medication",
    #   "onset_date": "2020-01-15",
    #   "end_date": null,
    #   "status": "active"
    # }]

    # Treatment History - JSONB array
    treatment_history = Column(JSONB, nullable=True)
    # [{
    #   "drug": "Metformin",
    #   "dosage": "500mg",
    #   "frequency": "BID",
    #   "start_date": "2020-01-20",
    #   "end_date": null,
    #   "treatment_type": "maintenance"
    # }]

    # Allergies - JSONB array
    allergies = Column(JSONB, nullable=True)
    # [{
    #   "allergen": "Penicillin",
    #   "severity": "severe",
    #   "reaction": "Anaphylaxis",
    #   "onset_date": "2015-06-10",
    #   "verified": true
    # }]

    # Immunization History - JSONB array
    immunizations = Column(JSONB, nullable=True)
    # [{
    #   "vaccine": "COVID-19 mRNA",
    #   "epi_number": "CV-2021-12345",
    #   "date": "2021-03-15",
    #   "facility": "County Health Dept",
    #   "lot_number": "123ABC"
    # }]

    # Travel History - JSONB array
    travel_history = Column(JSONB, nullable=True)
    # [{
    #   "destination_country": "Brazil",
    #   "destination_city": "Rio de Janeiro",
    #   "start_date": "2024-01-10",
    #   "end_date": "2024-01-20",
    #   "purpose": "vacation",
    #   "exposures": "mosquito bites"
    # }]

    # Reproductive Health (HIPAA encrypted)
    menstrual_status = Column(EncryptedPII(500), nullable=True)
    pregnancy_status = Column(Boolean, nullable=True)
    pregnancy_due_date = Column(EncryptedPII(500), nullable=True)

    # Family History - JSONB array
    family_history = Column(JSONB, nullable=True)
    # [{
    #   "relationship": "mother",
    #   "condition": "breast cancer",
    #   "icd10_code": "C50.9",
    #   "age_at_diagnosis": 55
    # }]

    # Surgical History - JSONB array
    surgical_history = Column(JSONB, nullable=True)
    # [{
    #   "procedure": "Appendectomy",
    #   "cpt_code": "44950",
    #   "date": "2018-05-10",
    #   "facility": "City Hospital",
    #   "complications": "none"
    # }]
```

#### 2. PatientInsurance (LabScopedEntity)

```python
class PatientInsurance(LabScopedEntity):
    __tablename__ = "patient_insurance"

    patient_uid = Column(String, ForeignKey("patient.uid"), nullable=False)
    patient = relationship("Patient", back_populates="insurance_policies")

    # Insurance Priority
    priority = Column(String, nullable=False)  # primary, secondary, tertiary
    is_active = Column(Boolean, default=True)

    # Insurance Company
    insurance_company_uid = Column(String, ForeignKey("insurance_company.uid"))
    insurance_company = relationship("InsuranceCompany")

    # Policy Information (HIPAA encrypted where needed)
    policy_number = Column(EncryptedPII(500), nullable=False)
    group_number = Column(String, nullable=True)
    plan_name = Column(String, nullable=True)

    # Subscriber Information (if different from patient)
    subscriber_is_patient = Column(Boolean, default=True)
    subscriber_first_name = Column(EncryptedPII(500), nullable=True)
    subscriber_last_name = Column(EncryptedPII(500), nullable=True)
    subscriber_dob = Column(EncryptedPII(500), nullable=True)
    subscriber_gender = Column(String, nullable=True)
    subscriber_id = Column(EncryptedPII(500), nullable=True)
    relationship_to_patient = Column(String, nullable=True)  # self, spouse, child, other

    # Coverage Details
    effective_date = Column(Date, nullable=True)
    termination_date = Column(Date, nullable=True)
    copay_amount = Column(Numeric(10, 2), nullable=True)
    deductible_amount = Column(Numeric(10, 2), nullable=True)

    # Billing Flags
    invoice_to_insurance = Column(Boolean, default=True)
    requires_authorization = Column(Boolean, default=False)
    authorization_number = Column(String, nullable=True)
```

#### 3. InsuranceCompany (BaseEntity)

```python
class InsuranceCompany(BaseEntity):
    __tablename__ = "insurance_company"

    name = Column(String, nullable=False, unique=True)
    code = Column(String, nullable=True, unique=True)  # Payer ID

    # Contact Information
    address_line1 = Column(String, nullable=True)
    address_line2 = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    zip_code = Column(String, nullable=True)
    country = Column(String, nullable=True)

    phone = Column(String, nullable=True)
    fax = Column(String, nullable=True)
    email = Column(String, nullable=True)
    website = Column(String, nullable=True)

    # Claims Submission
    claims_address = Column(String, nullable=True)
    electronic_payer_id = Column(String, nullable=True)  # For 837 submission
    clearinghouse = Column(String, nullable=True)  # OfficeAlly, etc.

    # Integration
    fhir_endpoint = Column(String, nullable=True)
    api_credentials = Column(JSONB, nullable=True)  # Encrypted

    is_active = Column(Boolean, default=True)
```

#### 4. Guarantor (LabScopedEntity)

```python
class Guarantor(LabScopedEntity):
    __tablename__ = "guarantor"

    patient_uid = Column(String, ForeignKey("patient.uid"), nullable=False)
    patient = relationship("Patient", back_populates="guarantor")

    # Guarantor is Patient flag
    is_patient = Column(Boolean, default=True)

    # Guarantor Demographics (HIPAA encrypted)
    guarantor_id = Column(String, nullable=True)
    first_name = Column(EncryptedPII(500), nullable=True)
    last_name = Column(EncryptedPII(500), nullable=True)
    date_of_birth = Column(EncryptedPII(500), nullable=True)
    gender = Column(String, nullable=True)
    relationship_to_patient = Column(String, nullable=True)

    # Contact (HIPAA encrypted)
    address_line1 = Column(EncryptedPII(500), nullable=True)
    address_line2 = Column(EncryptedPII(500), nullable=True)
    city = Column(EncryptedPII(500), nullable=True)
    state = Column(String, nullable=True)
    zip_code = Column(String, nullable=True)

    phone_home = Column(EncryptedPII(500), nullable=True)
    phone_business = Column(EncryptedPII(500), nullable=True)
    phone_mobile = Column(EncryptedPII(500), nullable=True)
    email = Column(EncryptedPII(500), nullable=True)

    # Financial Responsibility
    responsibility_percentage = Column(Integer, default=100)
```

#### 5. ClinicalDiagnosis (LabScopedEntity)

```python
class ClinicalDiagnosis(LabScopedEntity):
    __tablename__ = "clinical_diagnosis"

    patient_uid = Column(String, ForeignKey("patient.uid"), nullable=False)
    patient = relationship("Patient", back_populates="diagnoses")

    # Can be linked to specific analysis request
    analysis_request_uid = Column(String, ForeignKey("analysis_request.uid"), nullable=True)
    analysis_request = relationship("AnalysisRequest")

    # ICD-10 Coding
    icd10_code = Column(String, nullable=False, index=True)
    icd10_description = Column(String, nullable=False)

    # Clinical Details
    diagnosis_date = Column(Date, nullable=False)
    diagnosis_type = Column(String, nullable=False)  # primary, secondary, admitting, etc.
    status = Column(String, nullable=False)  # active, resolved, ruled_out
    resolution_date = Column(Date, nullable=True)

    # Provider
    diagnosing_provider_uid = Column(String, ForeignKey("user.uid"), nullable=True)
    diagnosing_provider = relationship("User")

    # Clinical Notes
    notes = Column(Text, nullable=True)

    # Diagnosis Pointer for 837 claims
    pointer = Column(String, nullable=True)  # A, B, C, D
```

---

## LCMS Integration Requirements

### Why Medical History Matters for LCMS

**Mass Spectrometry Clinical Context:**
1. **Medication Interference** - Current medications can affect metabolite profiles
2. **Disease State** - Chronic conditions influence biomarker interpretation
3. **Reference Ranges** - Age, gender, pregnancy status affect normal ranges
4. **Drug Interactions** - Multi-drug regimens create complex metabolic patterns
5. **Therapeutic Monitoring** - Treatment history essential for TDM interpretation

### Required Links

**Sample → Patient → Medical History:**
```python
# Existing Sample entity already has:
patient_uid = Column(String, ForeignKey("patient.uid"))
patient = relationship("Patient")

# Patient entity needs new relationship:
medical_history = relationship("PatientMedicalHistory", uselist=False)
insurance_policies = relationship("PatientInsurance")
diagnoses = relationship("ClinicalDiagnosis")
guarantor = relationship("Guarantor", uselist=False)
```

### LCMS Result Interpretation Workflow

1. **Sample Received** → Link to Patient
2. **LCMS Analysis** → Results generated
3. **Result Review** → System displays:
   - Current medications (check for interference)
   - Chronic conditions (disease context)
   - Recent diagnoses (clinical relevance)
   - Insurance coverage (billing context)
4. **Result Approval** → Include clinical context in report
5. **Billing** → Generate 837 claim with:
   - Patient demographics
   - Insurance information
   - ICD-10 diagnosis codes
   - CPT procedure codes

---

## Implementation Priority

### Phase 1: Core Medical History (Essential for LCMS)
1. ✅ PatientMedicalHistory entity
2. ✅ Chronic conditions tracking
3. ✅ Current medications/allergies
4. ✅ GraphQL API for medical history CRUD
5. ✅ Frontend UI for medical history entry

### Phase 2: Insurance & Billing (Required for Claims)
1. ✅ InsuranceCompany entity
2. ✅ PatientInsurance entity
3. ✅ Guarantor entity
4. ✅ ClinicalDiagnosis entity (ICD-10)
5. ✅ GraphQL API for insurance management
6. ✅ Frontend UI for insurance entry

### Phase 3: Integration
1. ✅ Link medical history to LCMS result review
2. ✅ 837 claim generation from patient data
3. ✅ OfficeAlly API integration
4. ✅ FHIR R4 Patient/Coverage resource export

---

## Database Migration Strategy

### Migration Steps

1. **Create new tables:**
   ```bash
   felicity-lims revision "Add patient medical history and insurance"
   ```

2. **Add relationship columns to existing Patient table:**
   - No breaking changes to current schema
   - All new fields are nullable or have defaults

3. **Data migration:**
   - Existing patients remain functional
   - New fields populated on update
   - No data loss risk

4. **Rollback plan:**
   - Keep migration reversible
   - Preserve existing patient functionality

---

## GraphQL Schema Extensions

### Queries

```graphql
type Query {
  # Existing patient query
  patient(uid: String!): Patient

  # Medical history
  patientMedicalHistory(patientUid: String!): PatientMedicalHistory

  # Insurance
  patientInsurance(patientUid: String!, priority: String): [PatientInsurance!]!
  insuranceCompanies(isActive: Boolean): [InsuranceCompany!]!

  # Diagnoses
  patientDiagnoses(patientUid: String!, status: String): [ClinicalDiagnosis!]!

  # Search ICD-10 codes
  searchICD10(query: String!, limit: Int): [ICD10Code!]!
}
```

### Mutations

```graphql
type Mutation {
  # Medical History
  createPatientMedicalHistory(input: PatientMedicalHistoryInput!): PatientMedicalHistory!
  updatePatientMedicalHistory(uid: String!, input: PatientMedicalHistoryInput!): PatientMedicalHistory!

  # Chronic Condition
  addChronicCondition(patientUid: String!, input: ChronicConditionInput!): PatientMedicalHistory!
  removeChronicCondition(patientUid: String!, index: Int!): PatientMedicalHistory!

  # Medications
  addMedication(patientUid: String!, input: MedicationInput!): PatientMedicalHistory!
  removeMedication(patientUid: String!, index: Int!): PatientMedicalHistory!

  # Allergies
  addAllergy(patientUid: String!, input: AllergyInput!): PatientMedicalHistory!
  removeAllergy(patientUid: String!, index: Int!): PatientMedicalHistory!

  # Insurance
  createPatientInsurance(input: PatientInsuranceInput!): PatientInsurance!
  updatePatientInsurance(uid: String!, input: PatientInsuranceInput!): PatientInsurance!
  deletePatientInsurance(uid: String!): Boolean!

  # Insurance Company
  createInsuranceCompany(input: InsuranceCompanyInput!): InsuranceCompany!
  updateInsuranceCompany(uid: String!, input: InsuranceCompanyInput!): InsuranceCompany!

  # Diagnosis
  createClinicalDiagnosis(input: ClinicalDiagnosisInput!): ClinicalDiagnosis!
  updateClinicalDiagnosis(uid: String!, input: ClinicalDiagnosisInput!): ClinicalDiagnosis!
  deleteClinicalDiagnosis(uid: String!): Boolean!
}
```

---

## Frontend UI Requirements

### Patient Detail Page Enhancements

**New Tabs:**
1. **Medical History**
   - Chronic conditions list with ICD-10 codes
   - Current medications table
   - Allergy alerts (prominent display)
   - Immunization timeline
   - Travel history

2. **Insurance**
   - Primary insurance card
   - Secondary/tertiary insurance cards
   - Coverage status indicators
   - Guarantor information

3. **Diagnoses**
   - Active diagnoses list
   - Historical diagnoses
   - ICD-10 code search widget
   - Link to related analysis requests

### LCMS Result Review Page Integration

**Medical Context Panel:**
- Display during result review
- Show relevant medications
- Display active chronic conditions
- Highlight allergies
- One-click to full medical history

---

## Security & Compliance

### HIPAA Compliance

**Encrypted Fields:**
- All PII in medical history (names, dates, addresses)
- Insurance subscriber information
- Guarantor personal information
- Policy numbers and identifiers

**Audit Requirements:**
- All medical history changes logged
- Insurance updates tracked
- Diagnosis modifications audited
- Access to medical history logged

### Multi-Tenancy

**Laboratory Scoping:**
- All new entities inherit `LabScopedEntity`
- Medical history scoped to laboratory
- Insurance companies can be shared (BaseEntity) or lab-specific
- Diagnoses scoped to laboratory

---

## Testing Strategy

### Unit Tests
- HIPAA encryption/decryption for new fields
- JSONB array operations (add/remove conditions, meds, etc.)
- Insurance priority validation
- ICD-10 code validation

### Integration Tests
- Patient with full medical history creation
- Insurance policy management workflow
- Diagnosis linking to analysis requests
- 837 claim generation from patient data

### E2E Tests
- Complete patient registration with insurance
- Medical history entry and update
- LCMS result review with medical context
- Billing claim submission

---

## Next Steps

1. **Review & Approve** this requirements document
2. **Create Database Migrations** for new entities
3. **Implement Repository/Service Layers** for new entities
4. **Build GraphQL API** with mutations and queries
5. **Design Frontend Components** for medical history UI
6. **Integrate with LCMS** result review workflow
7. **Build 837 Claim Generator** using patient/insurance data
8. **Test OfficeAlly Integration** (if API access available)

---

## References

- SENAITE.Patient: https://github.com/senaite/senaite.patient
- Bika.Health: https://github.com/senaite/senaite.health
- FHIR Patient Resource: https://www.hl7.org/fhir/patient.html
- FHIR Coverage Resource: https://build.fhir.org/coverage.html
- 837P Claim Format: ANSI ASC X12N 837 Professional
- ICD-10-CM: https://www.cms.gov/medicare/coding-billing/icd-10-codes
- CPT Codes: AMA Current Procedural Terminology

---

**Document Status**: Draft for Review
**Last Updated**: 2025-10-27
**Owner**: Mohammad Aijaz
**Project**: Felicity LIMS - Patient Addon
