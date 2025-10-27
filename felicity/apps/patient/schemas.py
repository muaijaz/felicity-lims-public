from datetime import datetime
from typing import Optional

from pydantic import ConfigDict, EmailStr

from felicity.apps.common.schemas import BaseAuditModel

#
#  Patient Schema
#

# Shared properties


class PatientBase(BaseAuditModel):
    client_patient_id: str | None = None
    client_uid: str | None = None
    patient_id: str | None = None
    first_name: str | None = None
    middle_name: str | None = None
    last_name: str | None = None
    gender: str | None = None
    age: int | None = None
    date_of_birth: datetime | None = None
    age_dob_estimated: bool | None = None
    phone_mobile: str | None = None
    phone_home: str | None = None
    consent_sms: bool | None = None
    email: Optional[EmailStr] = None
    internal_use: bool | None = False
    active: bool | None = None
    district_uid: str | None = None
    province_uid: str | None = None
    country_uid: str | None = None


# Properties to receive via API on creation
class PatientCreate(PatientBase):
    client_patient_id: str
    first_name: str
    last_name: str
    client_uid: str
    active: bool = True


# Properties to receive via API on update
class PatientUpdate(PatientBase):
    pass


class PatientInDBBase(PatientBase):
    uid: str | None = None

    model_config = ConfigDict(from_attributes=True)


# Additional properties to return via API
class Patient(PatientInDBBase):
    pass


# Additional properties stored in DB
class PatientInDB(PatientInDBBase):
    pass


#
#  Identification Schema
#

# Shared properties


class IdentificationBase(BaseAuditModel):
    name: str


# Properties to receive via API on creation
class IdentificationCreate(IdentificationBase):
    pass


# Properties to receive via API on update
class IdentificationUpdate(IdentificationBase):
    pass


class IdentificationInDBBase(IdentificationBase):
    uid: str | None = None

    model_config = ConfigDict(from_attributes=True)


# Additional properties to return via API
class Identification(IdentificationInDBBase):
    pass


# Additional properties stored in DB
class IdentificationInDB(IdentificationInDBBase):
    pass


#
#  PatientIdentification Schema
#

# Shared properties


class PatientIdentificationBase(BaseAuditModel):
    patient_uid: str
    identification_uid: str
    value: str


# Properties to receive via API on creation
class PatientIdentificationCreate(PatientIdentificationBase):
    pass


# Properties to receive via API on update
class PatientIdentificationUpdate(PatientIdentificationBase):
    pass


class PatientIdentificationInDBBase(PatientIdentificationBase):
    uid: str | None = None

    model_config = ConfigDict(from_attributes=True)


# Additional properties to return via API
class PatientIdentification(PatientIdentificationInDBBase):
    pass


# Additional properties stored in DB
class PatientIdentificationInDB(PatientIdentificationInDBBase):
    pass

#
# Medical History Nested Schemas
#

from datetime import date
from decimal import Decimal


class ChronicConditionSchema(BaseAuditModel):
    """Schema for a chronic condition entry."""
    icd10_code: str
    title: str
    description: str | None = None
    onset_date: str | None = None  # YYYY-MM-DD format
    end_date: str | None = None
    status: str = "active"  # active, resolved, managed


class MedicationSchema(BaseAuditModel):
    """Schema for a medication/treatment entry."""
    drug: str
    dosage: str | None = None
    frequency: str | None = None  # BID, TID, QD, etc.
    route: str | None = None  # oral, IV, IM, etc.
    start_date: str | None = None
    end_date: str | None = None
    treatment_type: str | None = None  # maintenance, acute, prophylactic
    prescribing_provider: str | None = None
    status: str = "active"


class AllergySchema(BaseAuditModel):
    """Schema for an allergy entry."""
    allergen: str
    allergen_type: str | None = None  # drug, food, environmental
    severity: str | None = None  # mild, moderate, severe
    reaction: str | None = None
    onset_date: str | None = None
    verified: bool = False
    notes: str | None = None


class ImmunizationSchema(BaseAuditModel):
    """Schema for an immunization entry."""
    vaccine: str
    epi_number: str | None = None
    date: str | None = None
    facility: str | None = None
    lot_number: str | None = None
    dose_number: int | None = None
    route: str | None = None  # intramuscular, subcutaneous, oral


class TravelHistorySchema(BaseAuditModel):
    """Schema for a travel history entry."""
    destination_country: str
    destination_city: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    purpose: str | None = None
    exposures: str | None = None
    prophylaxis: str | None = None


class FamilyHistorySchema(BaseAuditModel):
    """Schema for a family history entry."""
    relationship: str  # mother, father, sibling, etc.
    condition: str
    icd10_code: str | None = None
    age_at_diagnosis: int | None = None
    status: str | None = None  # living, deceased
    notes: str | None = None


class SurgicalHistorySchema(BaseAuditModel):
    """Schema for a surgical history entry."""
    procedure: str
    cpt_code: str | None = None
    date: str | None = None
    facility: str | None = None
    surgeon: str | None = None
    complications: str | None = None
    notes: str | None = None


#
# PatientMedicalHistory Schema
#

class PatientMedicalHistoryBase(BaseAuditModel):
    patient_uid: str | None = None
    chronic_conditions: list[dict] | None = None
    treatment_history: list[dict] | None = None
    allergies: list[dict] | None = None
    immunizations: list[dict] | None = None
    travel_history: list[dict] | None = None
    menstrual_status: str | None = None
    pregnancy_status: bool | None = None
    pregnancy_due_date: str | None = None
    gravida: int | None = None
    para: int | None = None
    family_history: list[dict] | None = None
    surgical_history: list[dict] | None = None
    smoking_status: str | None = None
    alcohol_use: str | None = None
    drug_use: str | None = None
    occupation: str | None = None
    notes: str | None = None


class PatientMedicalHistoryCreate(PatientMedicalHistoryBase):
    patient_uid: str


class PatientMedicalHistoryUpdate(PatientMedicalHistoryBase):
    pass


class PatientMedicalHistoryInDBBase(PatientMedicalHistoryBase):
    uid: str | None = None
    laboratory_uid: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PatientMedicalHistory(PatientMedicalHistoryInDBBase):
    pass


class PatientMedicalHistoryInDB(PatientMedicalHistoryInDBBase):
    pass


#
# InsuranceCompany Schema
#

class InsuranceCompanyBase(BaseAuditModel):
    name: str | None = None
    code: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    country: str | None = None
    phone: str | None = None
    fax: str | None = None
    email: str | None = None
    website: str | None = None
    claims_address: str | None = None
    electronic_payer_id: str | None = None
    clearinghouse: str | None = None
    fhir_endpoint: str | None = None
    api_credentials: dict | None = None
    is_active: bool | None = True
    notes: str | None = None


class InsuranceCompanyCreate(InsuranceCompanyBase):
    name: str
    code: str | None = None


class InsuranceCompanyUpdate(InsuranceCompanyBase):
    pass


class InsuranceCompanyInDBBase(InsuranceCompanyBase):
    uid: str | None = None

    model_config = ConfigDict(from_attributes=True)


class InsuranceCompany(InsuranceCompanyInDBBase):
    pass


class InsuranceCompanyInDB(InsuranceCompanyInDBBase):
    pass


#
# PatientInsurance Schema
#

class PatientInsuranceBase(BaseAuditModel):
    patient_uid: str | None = None
    priority: str | None = None  # primary, secondary, tertiary
    is_active: bool | None = True
    insurance_company_uid: str | None = None
    policy_number: str | None = None
    group_number: str | None = None
    plan_name: str | None = None
    subscriber_is_patient: bool | None = True
    subscriber_first_name: str | None = None
    subscriber_last_name: str | None = None
    subscriber_dob: str | None = None
    subscriber_gender: str | None = None
    subscriber_id: str | None = None
    relationship_to_patient: str | None = None
    effective_date: date | None = None
    termination_date: date | None = None
    copay_amount: Decimal | None = None
    deductible_amount: Decimal | None = None
    invoice_to_insurance: bool | None = True
    requires_authorization: bool | None = False
    authorization_number: str | None = None
    notes: str | None = None


class PatientInsuranceCreate(PatientInsuranceBase):
    patient_uid: str
    priority: str
    insurance_company_uid: str
    policy_number: str


class PatientInsuranceUpdate(PatientInsuranceBase):
    pass


class PatientInsuranceInDBBase(PatientInsuranceBase):
    uid: str | None = None
    laboratory_uid: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PatientInsurance(PatientInsuranceInDBBase):
    pass


class PatientInsuranceInDB(PatientInsuranceInDBBase):
    pass


#
# Guarantor Schema
#

class GuarantorBase(BaseAuditModel):
    patient_uid: str | None = None
    is_patient: bool | None = True
    guarantor_id: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: str | None = None
    gender: str | None = None
    relationship_to_patient: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    country: str | None = None
    phone_home: str | None = None
    phone_business: str | None = None
    phone_mobile: str | None = None
    email: str | None = None
    responsibility_percentage: int | None = 100
    notes: str | None = None


class GuarantorCreate(GuarantorBase):
    patient_uid: str


class GuarantorUpdate(GuarantorBase):
    pass


class GuarantorInDBBase(GuarantorBase):
    uid: str | None = None
    laboratory_uid: str | None = None

    model_config = ConfigDict(from_attributes=True)


class Guarantor(GuarantorInDBBase):
    pass


class GuarantorInDB(GuarantorInDBBase):
    pass


#
# ClinicalDiagnosis Schema
#

class ClinicalDiagnosisBase(BaseAuditModel):
    patient_uid: str | None = None
    analysis_request_uid: str | None = None
    icd10_code: str | None = None
    icd10_description: str | None = None
    diagnosis_date: date | None = None
    diagnosis_type: str | None = None  # primary, secondary, admitting, discharge
    status: str | None = "active"  # active, resolved, ruled_out
    resolution_date: date | None = None
    diagnosing_provider_uid: str | None = None
    notes: str | None = None
    pointer: str | None = None  # A, B, C, D for 837 claims


class ClinicalDiagnosisCreate(ClinicalDiagnosisBase):
    patient_uid: str
    icd10_code: str
    icd10_description: str
    diagnosis_date: date
    diagnosis_type: str


class ClinicalDiagnosisUpdate(ClinicalDiagnosisBase):
    pass


class ClinicalDiagnosisInDBBase(ClinicalDiagnosisBase):
    uid: str | None = None
    laboratory_uid: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ClinicalDiagnosis(ClinicalDiagnosisInDBBase):
    pass


class ClinicalDiagnosisInDB(ClinicalDiagnosisInDBBase):
    pass
