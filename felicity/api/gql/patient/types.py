from datetime import datetime
from typing import List, Optional

import strawberry  # noqa

from felicity.api.gql.client.types import ClientType
from felicity.api.gql.setup.types import CountryType, DistrictType, ProvinceType, LaboratoryType
from felicity.api.gql.types import PageInfo, JSONScalar
from felicity.api.gql.types.generic import StrawberryMapper
from felicity.api.gql.user.types import UserType


@strawberry.type
class IdentificationType:
    uid: str
    name: str
    #
    created_by_uid: str | None = None
    created_by: UserType | None = None
    created_at: str | None = None
    updated_by_uid: str | None = None
    updated_by: UserType | None = None
    updated_at: str | None = None


@strawberry.type
class PatientIdentificationType:
    uid: str
    patient_uid: str
    identification_uid: str
    identification: Optional[IdentificationType] = None
    value: str
    laboratory_uid: str | None = None
    laboratory: LaboratoryType | None = None
    #
    created_by_uid: str | None = None
    created_by: UserType | None = None
    created_at: str | None = None
    updated_by_uid: str | None = None
    updated_by: UserType | None = None
    updated_at: str | None = None


@strawberry.type
class PatientType:
    uid: str
    client_patient_id: str
    patient_id: str
    client_uid: str
    first_name: str | None = None
    middle_name: str | None = None
    last_name: str | None = None
    gender: str | None = None
    age: int | None = None
    date_of_birth: datetime | None = None
    age_dob_estimated: bool
    phone_mobile: str | None = None
    phone_home: str | None = None
    consent_sms: bool
    email: str | None = None
    internal_use: bool
    active: bool
    district_uid: str | None = None
    province_uid: str | None = None
    country_uid: str | None = None
    identifications: Optional[List[PatientIdentificationType]] = None
    metadata_snapshot: JSONScalar | None = None
    laboratory_uid: str | None = None
    laboratory: LaboratoryType | None = None
    #
    created_by_uid: str | None = None
    created_by: UserType | None = None
    created_at: str | None = None
    updated_by_uid: str | None = None
    updated_by: UserType | None = None
    updated_at: str | None = None

    @strawberry.field
    async def client(self, info) -> ClientType | None:
        _client = self.metadata_snapshot.get("client")
        if not _client: return None
        _district = _client.get("district", None)
        _province = _client.get("province", None)
        _client["district"] = StrawberryMapper[DistrictType]().map(**_district) if _district else None
        _client["province"] = StrawberryMapper[ProvinceType]().map(**_province) if _province else None
        return StrawberryMapper[ClientType]().map(exclude=["contacts"], **_client)

    @strawberry.field
    async def district(self, info) -> DistrictType | None:
        _district = self.metadata_snapshot.get("district", None)
        if not _district: return None
        return StrawberryMapper[DistrictType]().map(**_district)

    @strawberry.field
    async def province(self, info) -> ProvinceType | None:
        _province = self.metadata_snapshot.get("province", None)
        if not _province: return None
        return StrawberryMapper[ProvinceType]().map(**_province)

    @strawberry.field
    async def country(self, info) -> CountryType | None:
        _country = self.metadata_snapshot.get("district", None)
        if not _country: return None
        return StrawberryMapper[CountryType]().map(**_country)


#  relay paginations
@strawberry.type
class PatientEdge:
    cursor: str
    node: PatientType


@strawberry.type
class PatientCursorPage:
    page_info: PageInfo
    edges: Optional[List[PatientEdge]] = None
    items: Optional[List[PatientType]] = None
    total_count: int


# Medical History Types

@strawberry.type
class ChronicConditionType:
    icd10_code: str
    title: str
    description: str | None = None
    onset_date: str | None = None
    end_date: str | None = None
    status: str = "active"


@strawberry.type
class MedicationType:
    drug: str
    dosage: str | None = None
    frequency: str | None = None
    route: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    treatment_type: str | None = None
    prescribing_provider: str | None = None
    status: str = "active"


@strawberry.type
class AllergyType:
    allergen: str
    allergen_type: str | None = None
    severity: str | None = None
    reaction: str | None = None
    onset_date: str | None = None
    verified: bool = False
    notes: str | None = None


@strawberry.type
class ImmunizationType:
    vaccine: str
    epi_number: str | None = None
    date: str | None = None
    facility: str | None = None
    lot_number: str | None = None
    notes: str | None = None


@strawberry.type
class TravelHistoryType:
    destination_country: str
    destination_city: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    purpose: str | None = None
    exposures: str | None = None


@strawberry.type
class FamilyHistoryType:
    relationship: str
    condition: str
    icd10_code: str | None = None
    age_at_diagnosis: int | None = None


@strawberry.type
class SurgicalHistoryType:
    procedure: str
    cpt_code: str | None = None
    date: str | None = None
    facility: str | None = None
    complications: str | None = None


@strawberry.type
class PatientMedicalHistoryType:
    uid: str
    patient_uid: str
    chronic_conditions: Optional[List[ChronicConditionType]] = None
    treatment_history: Optional[List[MedicationType]] = None
    allergies: Optional[List[AllergyType]] = None
    immunizations: Optional[List[ImmunizationType]] = None
    travel_history: Optional[List[TravelHistoryType]] = None
    family_history: Optional[List[FamilyHistoryType]] = None
    surgical_history: Optional[List[SurgicalHistoryType]] = None
    menstrual_status: str | None = None
    pregnancy_status: bool | None = None
    pregnancy_due_date: str | None = None
    smoking_status: str | None = None
    alcohol_use: str | None = None
    drug_use: str | None = None
    occupation: str | None = None
    notes: str | None = None
    laboratory_uid: str | None = None
    laboratory: LaboratoryType | None = None
    #
    created_by_uid: str | None = None
    created_by: UserType | None = None
    created_at: str | None = None
    updated_by_uid: str | None = None
    updated_by: UserType | None = None
    updated_at: str | None = None


# Insurance Types

@strawberry.type
class InsuranceCompanyType:
    uid: str
    name: str
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
    api_credentials: JSONScalar | None = None
    is_active: bool
    #
    created_by_uid: str | None = None
    created_by: UserType | None = None
    created_at: str | None = None
    updated_by_uid: str | None = None
    updated_by: UserType | None = None
    updated_at: str | None = None


@strawberry.type
class PatientInsuranceType:
    uid: str
    patient_uid: str
    priority: str
    is_active: bool
    insurance_company_uid: str | None = None
    insurance_company: Optional[InsuranceCompanyType] = None
    policy_number: str | None = None
    group_number: str | None = None
    plan_name: str | None = None
    subscriber_is_patient: bool
    subscriber_first_name: str | None = None
    subscriber_last_name: str | None = None
    subscriber_dob: str | None = None
    subscriber_gender: str | None = None
    subscriber_id: str | None = None
    relationship_to_patient: str | None = None
    effective_date: datetime | None = None
    termination_date: datetime | None = None
    copay_amount: float | None = None
    deductible_amount: float | None = None
    invoice_to_insurance: bool
    requires_authorization: bool
    authorization_number: str | None = None
    laboratory_uid: str | None = None
    laboratory: LaboratoryType | None = None
    #
    created_by_uid: str | None = None
    created_by: UserType | None = None
    created_at: str | None = None
    updated_by_uid: str | None = None
    updated_by: UserType | None = None
    updated_at: str | None = None


@strawberry.type
class GuarantorType:
    uid: str
    patient_uid: str
    is_patient: bool
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
    phone_home: str | None = None
    phone_business: str | None = None
    phone_mobile: str | None = None
    email: str | None = None
    responsibility_percentage: int
    laboratory_uid: str | None = None
    laboratory: LaboratoryType | None = None
    #
    created_by_uid: str | None = None
    created_by: UserType | None = None
    created_at: str | None = None
    updated_by_uid: str | None = None
    updated_by: UserType | None = None
    updated_at: str | None = None


@strawberry.type
class ClinicalDiagnosisType:
    uid: str
    patient_uid: str
    analysis_request_uid: str | None = None
    icd10_code: str
    icd10_description: str
    diagnosis_date: datetime
    diagnosis_type: str
    status: str
    resolution_date: datetime | None = None
    diagnosing_provider_uid: str | None = None
    diagnosing_provider: Optional[UserType] = None
    notes: str | None = None
    pointer: str | None = None
    laboratory_uid: str | None = None
    laboratory: LaboratoryType | None = None
    #
    created_by_uid: str | None = None
    created_by: UserType | None = None
    created_at: str | None = None
    updated_by_uid: str | None = None
    updated_by: UserType | None = None
    updated_at: str | None = None


@strawberry.type
class InsuranceValidationType:
    is_valid: bool
    reason: str
    coverage_active: bool
