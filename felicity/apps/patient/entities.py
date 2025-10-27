from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, relationship

from felicity.apps.abstract import LabScopedEntity, BaseEntity
from felicity.apps.client.entities import Client
from felicity.utils.hipaa_fields import EncryptedPII


class Identification(BaseEntity):
    __tablename__ = "identification"

    name = Column(String, index=True, unique=True, nullable=True)


class PatientIdentification(LabScopedEntity):
    __tablename__ = "patient_identification"

    identification_uid = Column(String, ForeignKey("identification.uid"), nullable=True)
    identification: Mapped["Identification"] = relationship(
        "Identification", lazy="selectin"
    )
    patient_uid = Column(String, ForeignKey("patient.uid"), nullable=True)
    patient: Mapped["Patient"] = relationship(
        "Patient", back_populates="identifications", lazy="selectin"
    )
    # HIPAA: Encrypt identification values (SSN, ID numbers, etc.)
    value = Column(EncryptedPII(500), index=False, nullable=False)

    @property
    def sms_metadata(self) -> dict:
        return {self.identification.name: self.value}


class Patient(LabScopedEntity):
    __tablename__ = "patient"

    # Identification
    client_patient_id = Column(String, index=True, unique=True, nullable=False)
    patient_id = Column(String, index=True, unique=True, nullable=True)
    client_uid = Column(String, ForeignKey("client.uid"), nullable=True)
    client = relationship(Client, backref="patients", lazy="selectin")
    # Details - HIPAA: Encrypt personally identifiable information
    first_name = Column(EncryptedPII(500), nullable=False)
    middle_name = Column(EncryptedPII(500), nullable=True)
    last_name = Column(EncryptedPII(500), nullable=False)
    gender = Column(String, nullable=False)  # Keep unencrypted for analytics
    age = Column(Integer, nullable=True)
    # HIPAA: Encrypt date of birth as it's PII that can identify individuals
    date_of_birth = Column(EncryptedPII(500), nullable=True)
    age_dob_estimated = Column(Boolean(), default=False)
    # Contact - HIPAA: Encrypt contact information
    phone_mobile = Column(EncryptedPII(500), nullable=True)
    phone_home = Column(EncryptedPII(500), nullable=True)
    consent_sms = Column(Boolean(), default=False)
    email = Column(EncryptedPII(500), nullable=True)
    identifications: Mapped[list["PatientIdentification"]] = relationship(
        PatientIdentification, back_populates="patient", lazy="selectin"
    )
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
    # status
    internal_use = Column(Boolean(), default=False)  # e.g Test Patient
    active = Column(Boolean(), default=True)
    # belonging
    district_uid = Column(String, ForeignKey("district.uid"), nullable=True)
    district = relationship("District", backref="patients", lazy="selectin")
    province_uid = Column(String, ForeignKey("province.uid"), nullable=True)
    province = relationship("Province", backref="patients", lazy="selectin")
    country_uid = Column(String, ForeignKey("country.uid"), nullable=True)
    country = relationship("Country", backref="patients", lazy="selectin")
    # Metadata snapshot
    metadata_snapshot = Column(JSONB, nullable=False)

    @property
    def full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        else:
            return f"{self.first_name} {self.last_name}"

    @property
    def sms_metadata(self) -> dict:
        result = {
            "patient_name": self.full_name,
            "patient_id": self.patient_id,
            "gender": self.gender,
            "client_patient_id": self.client_patient_id,
            "age": self.age,
        }

        # Safely process identifications
        if self.identifications:
            for identification in self.identifications:
                if hasattr(identification, 'sms_metadata') and identification.sms_metadata:
                    result.update(identification.sms_metadata)
        return result


class PatientMedicalHistory(LabScopedEntity):
    """
    Comprehensive medical history for patient including chronic conditions,
    medications, allergies, immunizations, and other clinical data essential
    for LCMS result interpretation and clinical context.
    """
    __tablename__ = "patient_medical_history"

    patient_uid = Column(String, ForeignKey("patient.uid"), nullable=False, unique=True)
    patient: Mapped["Patient"] = relationship(
        "Patient", back_populates="medical_history", lazy="selectin"
    )

    # Chronic Conditions - JSONB array
    # [{
    #   "icd10_code": "E11.9",
    #   "title": "Type 2 Diabetes Mellitus",
    #   "description": "Controlled with medication",
    #   "onset_date": "2020-01-15",
    #   "end_date": null,
    #   "status": "active"
    # }]
    chronic_conditions = Column(JSONB, nullable=True, default=list)

    # Treatment History / Current Medications - JSONB array
    # [{
    #   "drug": "Metformin",
    #   "dosage": "500mg",
    #   "frequency": "BID",
    #   "route": "oral",
    #   "start_date": "2020-01-20",
    #   "end_date": null,
    #   "treatment_type": "maintenance",
    #   "prescribing_provider": "Dr. Smith"
    # }]
    treatment_history = Column(JSONB, nullable=True, default=list)

    # Allergies - JSONB array
    # [{
    #   "allergen": "Penicillin",
    #   "allergen_type": "drug",
    #   "severity": "severe",
    #   "reaction": "Anaphylaxis",
    #   "onset_date": "2015-06-10",
    #   "verified": true,
    #   "notes": "Confirmed by allergist"
    # }]
    allergies = Column(JSONB, nullable=True, default=list)

    # Immunization History - JSONB array
    # [{
    #   "vaccine": "COVID-19 mRNA",
    #   "epi_number": "CV-2021-12345",
    #   "date": "2021-03-15",
    #   "facility": "County Health Dept",
    #   "lot_number": "123ABC",
    #   "dose_number": 1,
    #   "route": "intramuscular"
    # }]
    immunizations = Column(JSONB, nullable=True, default=list)

    # Travel History - JSONB array
    # [{
    #   "destination_country": "Brazil",
    #   "destination_city": "Rio de Janeiro",
    #   "start_date": "2024-01-10",
    #   "end_date": "2024-01-20",
    #   "purpose": "vacation",
    #   "exposures": "mosquito bites",
    #   "prophylaxis": "none"
    # }]
    travel_history = Column(JSONB, nullable=True, default=list)

    # Reproductive Health (HIPAA encrypted)
    menstrual_status = Column(EncryptedPII(500), nullable=True)
    pregnancy_status = Column(Boolean, nullable=True)
    pregnancy_due_date = Column(EncryptedPII(500), nullable=True)
    gravida = Column(Integer, nullable=True)  # Number of pregnancies
    para = Column(Integer, nullable=True)  # Number of births

    # Family History - JSONB array
    # [{
    #   "relationship": "mother",
    #   "condition": "breast cancer",
    #   "icd10_code": "C50.9",
    #   "age_at_diagnosis": 55,
    #   "status": "deceased",
    #   "notes": "Diagnosed 2010"
    # }]
    family_history = Column(JSONB, nullable=True, default=list)

    # Surgical History - JSONB array
    # [{
    #   "procedure": "Appendectomy",
    #   "cpt_code": "44950",
    #   "date": "2018-05-10",
    #   "facility": "City Hospital",
    #   "surgeon": "Dr. Johnson",
    #   "complications": "none",
    #   "notes": "Laparoscopic, uneventful recovery"
    # }]
    surgical_history = Column(JSONB, nullable=True, default=list)

    # Social History
    smoking_status = Column(String, nullable=True)  # never, former, current
    alcohol_use = Column(String, nullable=True)  # none, occasional, moderate, heavy
    drug_use = Column(String, nullable=True)  # none, former, current
    occupation = Column(String, nullable=True)

    # Clinical Notes
    notes = Column(Text, nullable=True)

    @property
    def active_medications(self) -> list:
        """Get list of currently active medications."""
        if not self.treatment_history:
            return []
        return [
            med for med in self.treatment_history
            if med.get('end_date') is None or med.get('status') == 'active'
        ]

    @property
    def active_chronic_conditions(self) -> list:
        """Get list of active chronic conditions."""
        if not self.chronic_conditions:
            return []
        return [
            condition for condition in self.chronic_conditions
            if condition.get('status') == 'active'
        ]

    @property
    def verified_allergies(self) -> list:
        """Get list of verified allergies."""
        if not self.allergies:
            return []
        return [
            allergy for allergy in self.allergies
            if allergy.get('verified', False)
        ]


class InsuranceCompany(BaseEntity):
    """
    Insurance company/payer information for billing and claims processing.
    Can be shared across laboratories or laboratory-specific.
    """
    __tablename__ = "insurance_company"

    name = Column(String, nullable=False, unique=True, index=True)
    code = Column(String, nullable=True, unique=True, index=True)  # Payer ID

    # Contact Information
    address_line1 = Column(String, nullable=True)
    address_line2 = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    zip_code = Column(String, nullable=True)
    country = Column(String, nullable=True, default="US")

    phone = Column(String, nullable=True)
    fax = Column(String, nullable=True)
    email = Column(String, nullable=True)
    website = Column(String, nullable=True)

    # Claims Submission
    claims_address = Column(String, nullable=True)
    electronic_payer_id = Column(String, nullable=True)  # For 837 submission
    clearinghouse = Column(String, nullable=True)  # OfficeAlly, Change Healthcare, etc.

    # Integration
    fhir_endpoint = Column(String, nullable=True)
    api_credentials = Column(JSONB, nullable=True)  # Encrypted credentials

    # Status
    is_active = Column(Boolean, default=True)

    # Notes
    notes = Column(Text, nullable=True)


class PatientInsurance(LabScopedEntity):
    """
    Patient insurance policy information for billing and claims.
    Supports primary, secondary, and tertiary insurance.
    """
    __tablename__ = "patient_insurance"

    patient_uid = Column(String, ForeignKey("patient.uid"), nullable=False)
    patient: Mapped["Patient"] = relationship(
        "Patient", back_populates="insurance_policies", lazy="selectin"
    )

    # Insurance Priority
    priority = Column(String, nullable=False, index=True)  # primary, secondary, tertiary
    is_active = Column(Boolean, default=True)

    # Insurance Company
    insurance_company_uid = Column(String, ForeignKey("insurance_company.uid"), nullable=False)
    insurance_company: Mapped["InsuranceCompany"] = relationship(
        "InsuranceCompany", lazy="selectin"
    )

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

    # Notes
    notes = Column(Text, nullable=True)

    @property
    def is_valid(self) -> bool:
        """Check if insurance is currently valid."""
        today = date.today()
        if self.effective_date and self.effective_date > today:
            return False
        if self.termination_date and self.termination_date < today:
            return False
        return self.is_active


class Guarantor(LabScopedEntity):
    """
    Financial guarantor for patient (may be patient themselves or another person).
    """
    __tablename__ = "guarantor"

    patient_uid = Column(String, ForeignKey("patient.uid"), nullable=False, unique=True)
    patient: Mapped["Patient"] = relationship(
        "Patient", back_populates="guarantor", lazy="selectin"
    )

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
    country = Column(String, nullable=True, default="US")

    phone_home = Column(EncryptedPII(500), nullable=True)
    phone_business = Column(EncryptedPII(500), nullable=True)
    phone_mobile = Column(EncryptedPII(500), nullable=True)
    email = Column(EncryptedPII(500), nullable=True)

    # Financial Responsibility
    responsibility_percentage = Column(Integer, default=100)

    # Notes
    notes = Column(Text, nullable=True)

    @property
    def full_name(self) -> str:
        """Get guarantor full name."""
        if self.is_patient:
            return "Patient is Guarantor"
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return "Unknown"


class ClinicalDiagnosis(LabScopedEntity):
    """
    ICD-10 coded diagnoses for patient, can be linked to specific analysis requests
    for billing and clinical context.
    """
    __tablename__ = "clinical_diagnosis"

    patient_uid = Column(String, ForeignKey("patient.uid"), nullable=False, index=True)
    patient: Mapped["Patient"] = relationship(
        "Patient", back_populates="diagnoses", lazy="selectin"
    )

    # Can be linked to specific analysis request
    analysis_request_uid = Column(String, ForeignKey("analysis_request.uid"), nullable=True)
    # analysis_request relationship will be added in analysis entities

    # ICD-10 Coding
    icd10_code = Column(String, nullable=False, index=True)
    icd10_description = Column(String, nullable=False)

    # Clinical Details
    diagnosis_date = Column(Date, nullable=False)
    diagnosis_type = Column(String, nullable=False)  # primary, secondary, admitting, discharge
    status = Column(String, nullable=False, default="active")  # active, resolved, ruled_out
    resolution_date = Column(Date, nullable=True)

    # Provider
    diagnosing_provider_uid = Column(String, ForeignKey("user.uid"), nullable=True)
    # diagnosing_provider relationship will use User entity

    # Clinical Notes
    notes = Column(Text, nullable=True)

    # Diagnosis Pointer for 837 claims (A, B, C, D)
    pointer = Column(String, nullable=True, index=True)

    @property
    def is_active(self) -> bool:
        """Check if diagnosis is currently active."""
        return self.status == "active" and (
            self.resolution_date is None or self.resolution_date > date.today()
        )
