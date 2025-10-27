import logging
from dataclasses import field
from datetime import datetime
from typing import List, Optional

import strawberry  # noqa
from strawberry.permission import PermissionExtension

from felicity.api.gql.auth import auth_from_info
from felicity.api.gql.patient.types import (
    ClinicalDiagnosisType,
    GuarantorType,
    IdentificationType,
    InsuranceCompanyType,
    PatientInsuranceType,
    PatientMedicalHistoryType,
    PatientType,
)
from felicity.api.gql.permissions import IsAuthenticated, HasPermission
from felicity.api.gql.types import OperationError, JSONScalar
from felicity.api.gql.types.generic import StrawberryMapper
from felicity.apps.client.services import ClientService
from felicity.apps.guard import FAction, FObject
from felicity.apps.patient import schemas
from felicity.apps.patient.services import (
    ClinicalDiagnosisService,
    GuarantorService,
    IdentificationService,
    InsuranceCompanyService,
    PatientIdentificationService,
    PatientInsuranceService,
    PatientMedicalHistoryService,
    PatientService,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PatientResponse = strawberry.union(
    "PatientResponse",
    (PatientType, OperationError),
    description="",  # noqa
)


@strawberry.input
class PatientidentificationInput:
    value: str
    identification_uid: str


@strawberry.input
class PatientInputType:
    client_patient_id: str
    first_name: str
    last_name: str
    client_uid: str
    gender: str
    middle_name: str | None = None
    age: int | None = None
    date_of_birth: datetime | None = None
    age_dob_estimated: bool | None = False
    phone_mobile: str | None = None
    phone_home: str | None = None
    consent_sms: bool | None = False
    internal_use: bool | None = False
    country_uid: str | None = None
    province_uid: str | None = None
    district_uid: str | None = None
    identifications: Optional[List[PatientidentificationInput]] = field(
        default_factory=list
    )


IdentificationResponse = strawberry.union(
    "IdentificationResponse",
    (IdentificationType, OperationError),  # noqa
    description="",
)


# Medical History Input Types

@strawberry.input
class ChronicConditionInput:
    icd10_code: str
    title: str
    description: str | None = None
    onset_date: str | None = None
    end_date: str | None = None
    status: str = "active"


@strawberry.input
class MedicationInput:
    drug: str
    dosage: str | None = None
    frequency: str | None = None
    route: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    treatment_type: str | None = None
    prescribing_provider: str | None = None
    status: str = "active"


@strawberry.input
class AllergyInput:
    allergen: str
    allergen_type: str | None = None
    severity: str | None = None
    reaction: str | None = None
    onset_date: str | None = None
    verified: bool = False
    notes: str | None = None


@strawberry.input
class PatientMedicalHistoryInput:
    patient_uid: str
    menstrual_status: str | None = None
    pregnancy_status: bool | None = None
    pregnancy_due_date: str | None = None
    smoking_status: str | None = None
    alcohol_use: str | None = None
    drug_use: str | None = None
    occupation: str | None = None
    notes: str | None = None


PatientMedicalHistoryResponse = strawberry.union(
    "PatientMedicalHistoryResponse",
    (PatientMedicalHistoryType, OperationError),
    description="",
)


# Insurance Input Types

@strawberry.input
class InsuranceCompanyInput:
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
    is_active: bool = True


InsuranceCompanyResponse = strawberry.union(
    "InsuranceCompanyResponse",
    (InsuranceCompanyType, OperationError),
    description="",
)


@strawberry.input
class PatientInsuranceInput:
    patient_uid: str
    priority: str
    insurance_company_uid: str
    policy_number: str
    group_number: str | None = None
    plan_name: str | None = None
    subscriber_is_patient: bool = True
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
    invoice_to_insurance: bool = True
    requires_authorization: bool = False
    authorization_number: str | None = None
    is_active: bool = True


PatientInsuranceResponse = strawberry.union(
    "PatientInsuranceResponse",
    (PatientInsuranceType, OperationError),
    description="",
)


@strawberry.input
class GuarantorInput:
    patient_uid: str
    is_patient: bool = True
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
    responsibility_percentage: int = 100


GuarantorResponse = strawberry.union(
    "GuarantorResponse",
    (GuarantorType, OperationError),
    description="",
)


@strawberry.input
class ClinicalDiagnosisInput:
    patient_uid: str
    icd10_code: str
    icd10_description: str
    diagnosis_date: datetime
    diagnosis_type: str
    status: str = "active"
    analysis_request_uid: str | None = None
    resolution_date: datetime | None = None
    diagnosing_provider_uid: str | None = None
    notes: str | None = None
    pointer: str | None = None


ClinicalDiagnosisResponse = strawberry.union(
    "ClinicalDiagnosisResponse",
    (ClinicalDiagnosisType, OperationError),
    description="",
)


@strawberry.type
class PatientMutations:
    @strawberry.mutation(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.CREATE, FObject.PATIENT)]
        )]
    )
    async def create_identification(info, name: str) -> IdentificationResponse:
        felicity_user = await auth_from_info(info)

        if not name:
            return OperationError(error="name is mandatory")

        exists = await IdentificationService().get(name=name)
        if exists:
            return OperationError(
                error=f"The Identfication name -> {name} <- already exists"
            )

        incoming = {
            "name": name,
            "created_by_uid": felicity_user.uid,
            "updated_by_uid": felicity_user.uid,
        }

        obj_in = schemas.IdentificationCreate(**incoming)
        identification = await IdentificationService().create(obj_in)
        return IdentificationType(**identification.marshal_simple())

    @strawberry.mutation(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.UPDATE, FObject.PATIENT)]
        )]
    )
    async def update_identification(
            info, uid: str, name: str
    ) -> IdentificationResponse:
        await auth_from_info(info)

        identification = await IdentificationService().get(uid=uid)
        if not identification:
            return OperationError(error=f"identification with uid {uid} does not exist")

        try:
            setattr(identification, "name", name)
        except AttributeError as e:
            logger.warning(e)

        id_in = schemas.IdentificationUpdate(**identification.to_dict())
        identification = await IdentificationService().update(identification.uid, id_in)
        return IdentificationType(**identification.marshal_simple())

    @strawberry.mutation(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.READ, FObject.PATIENT)]
        )]
    )
    async def create_patient(self, info, payload: PatientInputType) -> PatientResponse:
        felicity_user = await auth_from_info(info)

        if (
                not payload.client_patient_id
                or not payload.first_name
                or not payload.last_name
                or not payload.client_uid
        ):
            return OperationError(
                error="Client Patient Id, First Name and Last Name , gender etc are required"
            )

        async with PatientService().repository.async_session() as tr_session:
            exists = await PatientService().get(
                client_patient_id=payload.client_patient_id, session=tr_session
            )
            if exists:
                return OperationError(error="Client Patient Id already in use")

            client = await ClientService().get(
                related=["province", "district"], uid=payload.client_uid, session=tr_session
            )
            if not client:
                return OperationError(
                    error=f"Client with uid {payload.client_uid} does not exist"
                )

            incoming: dict = {
                "created_by_uid": felicity_user.uid,
                "updated_by_uid": felicity_user.uid,
            }
            for k, v in payload.__dict__.items():
                incoming[k] = v

            obj_in = schemas.PatientCreate(**incoming)
            patient = await PatientService().create(obj_in, session=tr_session)

            # create identifications
            for p_id in payload.identifications:
                pid_in = schemas.PatientIdentificationCreate(
                    patient_uid=patient.uid,
                    identification_uid=p_id.identification_uid,
                    value=p_id.value,
                )
                await PatientIdentificationService().create(pid_in, commit=False, session=tr_session)

            # save transactions
            await PatientService().repository.save_transaction(tr_session)

        metadata = {"client": client.snapshot()}
        metadata["client"]["province"] = client.province.snapshot() if client.province else {}
        metadata["client"]["district"] = client.district.snapshot() if client.district else {}
        patient = await PatientService().snapshot(patient, metadata)
        return StrawberryMapper[PatientType]().map(**patient.marshal_simple())

    @strawberry.mutation(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.UPDATE, FObject.PATIENT)]
        )]
    )
    async def update_patient(
            self, info, uid: str, payload: PatientInputType
    ) -> PatientResponse:
        felicity_user = await auth_from_info(info)

        if not uid:
            return OperationError(error="No uid provided to idenity update obj")

        patient = await PatientService().get(uid=uid)
        if not patient:
            return OperationError(
                error=f"patient with uid {uid} not found. Cannot update obj ..."
            )

        obj_data = patient.to_dict()
        for _field in obj_data:
            if _field in payload.__dict__:
                try:
                    setattr(patient, _field, payload.__dict__[_field])
                except Exception as e:  # noqa
                    pass

        setattr(patient, "updated_by_uid", felicity_user.uid)

        obj_in = schemas.PatientUpdate(**patient.to_dict())
        patient = await PatientService().update(patient.uid, obj_in)

        # update identifications
        update_identification_uids = [
            id.identification_uid for id in payload.identifications
        ]
        identifications = await PatientIdentificationService().get_all(
            patient_uid=patient.uid
        )
        identifications_uids = [id.uid for id in identifications]

        for identification in identifications:
            # deleted
            if identification.uid not in update_identification_uids:
                await PatientIdentificationService().delete(identification.uid)
            else:  # update
                update_identification = list(
                    filter(
                        lambda x: x.identification_uid == identification.uid,
                        payload.identifications,
                    )
                )[0]
                id_update_in = schemas.PatientIdentificationUpdate(
                    patient_uid=patient.uid, **update_identification.to_dict()
                )
                identification = await PatientIdentificationService().update(
                    identification.uid, id_update_in
                )

        # new
        for _pid in payload.identifications:
            if _pid.identification_uid not in identifications_uids:
                pid_in = schemas.PatientIdentificationCreate(
                    patient_uid=patient.uid,
                    identification_uid=_pid.identification_uid,
                    value=_pid.value,
                )
                await PatientIdentificationService().create(pid_in)

        patient = await PatientService().get(uid=patient.uid)
        return PatientType(**patient.marshal_simple())

    # Medical History Mutations

    @strawberry.mutation(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.CREATE, FObject.PATIENT)]
        )]
    )
    async def create_or_update_medical_history(
        self, info, payload: PatientMedicalHistoryInput
    ) -> PatientMedicalHistoryResponse:
        felicity_user = await auth_from_info(info)

        incoming = payload.__dict__.copy()
        incoming["created_by_uid"] = felicity_user.uid
        incoming["updated_by_uid"] = felicity_user.uid

        obj_in = schemas.PatientMedicalHistoryCreate(**incoming)
        medical_history = await PatientMedicalHistoryService().create_or_update(
            payload.patient_uid, obj_in
        )
        return PatientMedicalHistoryType(**medical_history.marshal_simple())

    @strawberry.mutation(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.UPDATE, FObject.PATIENT)]
        )]
    )
    async def add_chronic_condition(
        self, info, patient_uid: str, condition: ChronicConditionInput
    ) -> PatientMedicalHistoryResponse:
        await auth_from_info(info)
        medical_history = await PatientMedicalHistoryService().add_chronic_condition(
            patient_uid, condition.__dict__
        )
        return PatientMedicalHistoryType(**medical_history.marshal_simple())

    @strawberry.mutation(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.UPDATE, FObject.PATIENT)]
        )]
    )
    async def remove_chronic_condition(
        self, info, patient_uid: str, index: int
    ) -> PatientMedicalHistoryResponse:
        await auth_from_info(info)
        medical_history = await PatientMedicalHistoryService().remove_chronic_condition(
            patient_uid, index
        )
        return PatientMedicalHistoryType(**medical_history.marshal_simple())

    @strawberry.mutation(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.UPDATE, FObject.PATIENT)]
        )]
    )
    async def add_medication(
        self, info, patient_uid: str, medication: MedicationInput
    ) -> PatientMedicalHistoryResponse:
        await auth_from_info(info)
        medical_history = await PatientMedicalHistoryService().add_medication(
            patient_uid, medication.__dict__
        )
        return PatientMedicalHistoryType(**medical_history.marshal_simple())

    @strawberry.mutation(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.UPDATE, FObject.PATIENT)]
        )]
    )
    async def remove_medication(
        self, info, patient_uid: str, index: int
    ) -> PatientMedicalHistoryResponse:
        await auth_from_info(info)
        medical_history = await PatientMedicalHistoryService().remove_medication(
            patient_uid, index
        )
        return PatientMedicalHistoryType(**medical_history.marshal_simple())

    @strawberry.mutation(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.UPDATE, FObject.PATIENT)]
        )]
    )
    async def add_allergy(
        self, info, patient_uid: str, allergy: AllergyInput
    ) -> PatientMedicalHistoryResponse:
        await auth_from_info(info)
        medical_history = await PatientMedicalHistoryService().add_allergy(
            patient_uid, allergy.__dict__
        )
        return PatientMedicalHistoryType(**medical_history.marshal_simple())

    @strawberry.mutation(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.UPDATE, FObject.PATIENT)]
        )]
    )
    async def remove_allergy(
        self, info, patient_uid: str, index: int
    ) -> PatientMedicalHistoryResponse:
        await auth_from_info(info)
        medical_history = await PatientMedicalHistoryService().remove_allergy(
            patient_uid, index
        )
        return PatientMedicalHistoryType(**medical_history.marshal_simple())

    # Insurance Mutations

    @strawberry.mutation(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.CREATE, FObject.PATIENT)]
        )]
    )
    async def create_insurance_company(
        self, info, payload: InsuranceCompanyInput
    ) -> InsuranceCompanyResponse:
        felicity_user = await auth_from_info(info)

        exists = await InsuranceCompanyService().get(name=payload.name)
        if exists:
            return OperationError(error=f"Insurance company {payload.name} already exists")

        incoming = payload.__dict__.copy()
        incoming["created_by_uid"] = felicity_user.uid
        incoming["updated_by_uid"] = felicity_user.uid

        obj_in = schemas.InsuranceCompanyCreate(**incoming)
        insurance_company = await InsuranceCompanyService().create(obj_in)
        return InsuranceCompanyType(**insurance_company.marshal_simple())

    @strawberry.mutation(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.UPDATE, FObject.PATIENT)]
        )]
    )
    async def update_insurance_company(
        self, info, uid: str, payload: InsuranceCompanyInput
    ) -> InsuranceCompanyResponse:
        felicity_user = await auth_from_info(info)

        insurance_company = await InsuranceCompanyService().get(uid=uid)
        if not insurance_company:
            return OperationError(error=f"Insurance company with uid {uid} not found")

        incoming = payload.__dict__.copy()
        incoming["updated_by_uid"] = felicity_user.uid

        obj_in = schemas.InsuranceCompanyUpdate(**incoming)
        insurance_company = await InsuranceCompanyService().update(uid, obj_in)
        return InsuranceCompanyType(**insurance_company.marshal_simple())

    @strawberry.mutation(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.CREATE, FObject.PATIENT)]
        )]
    )
    async def create_patient_insurance(
        self, info, payload: PatientInsuranceInput
    ) -> PatientInsuranceResponse:
        felicity_user = await auth_from_info(info)

        incoming = payload.__dict__.copy()
        incoming["created_by_uid"] = felicity_user.uid
        incoming["updated_by_uid"] = felicity_user.uid

        obj_in = schemas.PatientInsuranceCreate(**incoming)
        patient_insurance = await PatientInsuranceService().create(obj_in)
        return PatientInsuranceType(**patient_insurance.marshal_simple())

    @strawberry.mutation(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.UPDATE, FObject.PATIENT)]
        )]
    )
    async def update_patient_insurance(
        self, info, uid: str, payload: PatientInsuranceInput
    ) -> PatientInsuranceResponse:
        felicity_user = await auth_from_info(info)

        patient_insurance = await PatientInsuranceService().get(uid=uid)
        if not patient_insurance:
            return OperationError(error=f"Patient insurance with uid {uid} not found")

        incoming = payload.__dict__.copy()
        incoming["updated_by_uid"] = felicity_user.uid

        obj_in = schemas.PatientInsuranceUpdate(**incoming)
        patient_insurance = await PatientInsuranceService().update(uid, obj_in)
        return PatientInsuranceType(**patient_insurance.marshal_simple())

    @strawberry.mutation(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.DELETE, FObject.PATIENT)]
        )]
    )
    async def delete_patient_insurance(self, info, uid: str) -> bool:
        await auth_from_info(info)
        await PatientInsuranceService().delete(uid)
        return True

    # Guarantor Mutations

    @strawberry.mutation(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.CREATE, FObject.PATIENT)]
        )]
    )
    async def create_or_update_guarantor(
        self, info, payload: GuarantorInput
    ) -> GuarantorResponse:
        felicity_user = await auth_from_info(info)

        incoming = payload.__dict__.copy()
        incoming["created_by_uid"] = felicity_user.uid
        incoming["updated_by_uid"] = felicity_user.uid

        obj_in = schemas.GuarantorCreate(**incoming)
        guarantor = await GuarantorService().create_or_update(
            payload.patient_uid, obj_in
        )
        return GuarantorType(**guarantor.marshal_simple())

    # Diagnosis Mutations

    @strawberry.mutation(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.CREATE, FObject.PATIENT)]
        )]
    )
    async def create_clinical_diagnosis(
        self, info, payload: ClinicalDiagnosisInput
    ) -> ClinicalDiagnosisResponse:
        felicity_user = await auth_from_info(info)

        incoming = payload.__dict__.copy()
        incoming["created_by_uid"] = felicity_user.uid
        incoming["updated_by_uid"] = felicity_user.uid

        obj_in = schemas.ClinicalDiagnosisCreate(**incoming)
        diagnosis = await ClinicalDiagnosisService().create(obj_in)
        return ClinicalDiagnosisType(**diagnosis.marshal_simple())

    @strawberry.mutation(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.UPDATE, FObject.PATIENT)]
        )]
    )
    async def update_clinical_diagnosis(
        self, info, uid: str, payload: ClinicalDiagnosisInput
    ) -> ClinicalDiagnosisResponse:
        felicity_user = await auth_from_info(info)

        diagnosis = await ClinicalDiagnosisService().get(uid=uid)
        if not diagnosis:
            return OperationError(error=f"Clinical diagnosis with uid {uid} not found")

        incoming = payload.__dict__.copy()
        incoming["updated_by_uid"] = felicity_user.uid

        obj_in = schemas.ClinicalDiagnosisUpdate(**incoming)
        diagnosis = await ClinicalDiagnosisService().update(uid, obj_in)
        return ClinicalDiagnosisType(**diagnosis.marshal_simple())

    @strawberry.mutation(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.DELETE, FObject.PATIENT)]
        )]
    )
    async def delete_clinical_diagnosis(self, info, uid: str) -> bool:
        await auth_from_info(info)
        await ClinicalDiagnosisService().delete(uid)
        return True

    @strawberry.mutation(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.UPDATE, FObject.PATIENT)]
        )]
    )
    async def assign_diagnosis_pointers(
        self, info, patient_uid: str
    ) -> List[ClinicalDiagnosisType]:
        await auth_from_info(info)
        diagnoses = await ClinicalDiagnosisService().assign_diagnosis_pointers(patient_uid)
        return [ClinicalDiagnosisType(**d.marshal_simple()) for d in diagnoses]
