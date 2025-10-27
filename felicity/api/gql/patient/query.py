from typing import List, Optional

import strawberry  # noqa
from strawberry.permission import PermissionExtension

from felicity.api.gql.patient.types import (
    AllergyType,
    ClinicalDiagnosisType,
    GuarantorType,
    IdentificationType,
    InsuranceCompanyType,
    InsuranceValidationType,
    MedicationType,
    PatientCursorPage,
    PatientEdge,
    PatientInsuranceType,
    PatientMedicalHistoryType,
    PatientType,
)
from felicity.api.gql.permissions import IsAuthenticated, HasPermission
from felicity.api.gql.types import PageInfo
from felicity.apps.guard import FAction, FObject
from felicity.apps.patient.services import (
    ClinicalDiagnosisService,
    GuarantorService,
    IdentificationService,
    InsuranceCompanyService,
    PatientInsuranceService,
    PatientMedicalHistoryService,
    PatientService,
)


@strawberry.type
class PatientQuery:
    @strawberry.field(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.READ, FObject.PATIENT)]
        )]
    )
    async def patient_all(
            self,
            info,
            page_size: int | None = None,
            after_cursor: str | None = None,
            before_cursor: str | None = None,
            text: str | None = None,
            sort_by: list[str] | None = None,
    ) -> PatientCursorPage:
        # Use PatientService.paging_filter with HIPAA-compliant search

        page = await PatientService().paging_filter(
            page_size=page_size,
            after_cursor=after_cursor,
            before_cursor=before_cursor,
            filters={},
            sort_by=sort_by,
            text=text  # Pass text as kwarg for HIPAA search
        )

        # Convert PageCursor to PatientCursorPage
        edges = []
        if page.edges:
            for edge in page.edges:
                edges.append(PatientEdge(cursor=edge.cursor, node=edge.node))

        # Convert PageInfo from database to GraphQL PageInfo
        page_info = PageInfo(
            start_cursor=page.page_info.start_cursor,
            end_cursor=page.page_info.end_cursor,
            has_next_page=page.page_info.has_next_page,
            has_previous_page=page.page_info.has_previous_page,
        )

        return PatientCursorPage(
            total_count=page.total_count,
            edges=edges,
            items=page.items,
            page_info=page_info
        )

    @strawberry.field(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.READ, FObject.PATIENT)]
        )]
    )
    async def patient_by_uid(self, info, uid: str) -> Optional[PatientType]:
        return await PatientService().get(uid=uid)

    @strawberry.field(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.READ, FObject.PATIENT)]
        )]
    )
    async def patient_by_patient_id(
            self, info, patient_id: str
    ) -> Optional[PatientType]:
        return await PatientService().get(patient_id=patient_id)

    @strawberry.field(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.READ, FObject.PATIENT)]
        )]
    )
    async def patient_search(self, info, query_string: str) -> List[PatientType]:
        return await PatientService().high_performance_search(
            first_name=query_string,
            last_name=query_string,
            email=query_string,
            phone_mobile=query_string,
            patient_id=query_string,
            client_patient_id=query_string,
            fuzzy_match=True
        )

    @strawberry.field(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.READ, FObject.PATIENT)]
        )]
    )
    async def identification_all(self, info) -> List[IdentificationType]:
        return await IdentificationService().all()

    @strawberry.field(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.READ, FObject.PATIENT)]
        )]
    )
    async def identification_by_uid(self, info, uid: str) -> IdentificationType:
        return await IdentificationService().get(uid=uid)

    # Medical History Queries

    @strawberry.field(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.READ, FObject.PATIENT)]
        )]
    )
    async def patient_medical_history(
        self, info, patient_uid: str
    ) -> Optional[PatientMedicalHistoryType]:
        return await PatientMedicalHistoryService().get_by_patient(patient_uid)

    @strawberry.field(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.READ, FObject.PATIENT)]
        )]
    )
    async def active_medications(self, info, patient_uid: str) -> List[MedicationType]:
        medications = await PatientMedicalHistoryService().get_active_medications(patient_uid)
        return [MedicationType(**med) for med in medications] if medications else []

    @strawberry.field(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.READ, FObject.PATIENT)]
        )]
    )
    async def verified_allergies(self, info, patient_uid: str) -> List[AllergyType]:
        allergies = await PatientMedicalHistoryService().get_verified_allergies(patient_uid)
        return [AllergyType(**allergy) for allergy in allergies] if allergies else []

    # Insurance Queries

    @strawberry.field(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.READ, FObject.PATIENT)]
        )]
    )
    async def patient_insurance(
        self, info, patient_uid: str, active_only: bool = True
    ) -> List[PatientInsuranceType]:
        return await PatientInsuranceService().get_by_patient(patient_uid, active_only)

    @strawberry.field(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.READ, FObject.PATIENT)]
        )]
    )
    async def primary_insurance(
        self, info, patient_uid: str
    ) -> Optional[PatientInsuranceType]:
        return await PatientInsuranceService().get_primary_insurance(patient_uid)

    @strawberry.field(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.READ, FObject.PATIENT)]
        )]
    )
    async def validate_insurance(
        self, info, insurance_uid: str
    ) -> InsuranceValidationType:
        validation = await PatientInsuranceService().validate_insurance(insurance_uid)
        return InsuranceValidationType(**validation)

    @strawberry.field(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.READ, FObject.PATIENT)]
        )]
    )
    async def insurance_companies(
        self, info, active_only: bool = True
    ) -> List[InsuranceCompanyType]:
        if active_only:
            return await InsuranceCompanyService().get_active_companies()
        return await InsuranceCompanyService().all()

    # Guarantor Query

    @strawberry.field(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.READ, FObject.PATIENT)]
        )]
    )
    async def patient_guarantor(
        self, info, patient_uid: str
    ) -> Optional[GuarantorType]:
        return await GuarantorService().get_by_patient(patient_uid)

    # Diagnosis Queries

    @strawberry.field(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.READ, FObject.PATIENT)]
        )]
    )
    async def patient_diagnoses(
        self, info, patient_uid: str, active_only: bool = True
    ) -> List[ClinicalDiagnosisType]:
        return await ClinicalDiagnosisService().get_by_patient(patient_uid, active_only)

    @strawberry.field(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.READ, FObject.PATIENT)]
        )]
    )
    async def primary_diagnosis(
        self, info, patient_uid: str
    ) -> Optional[ClinicalDiagnosisType]:
        return await ClinicalDiagnosisService().get_primary_diagnosis(patient_uid)

    @strawberry.field(
        extensions=[PermissionExtension(
            permissions=[IsAuthenticated(), HasPermission(FAction.READ, FObject.PATIENT)]
        )]
    )
    async def diagnosis_for_analysis_request(
        self, info, analysis_request_uid: str
    ) -> List[ClinicalDiagnosisType]:
        return await ClinicalDiagnosisService().get_by_analysis_request(
            analysis_request_uid
        )
