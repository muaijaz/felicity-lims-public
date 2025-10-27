import base64
import json
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from felicity.apps.abstract.service import BaseService
from felicity.apps.client.services import ClientService
from felicity.apps.common.utils.serializer import marshaller
from felicity.apps.idsequencer.service import IdSequenceService
from felicity.apps.patient.entities import (
    ClinicalDiagnosis,
    Guarantor,
    Identification,
    InsuranceCompany,
    Patient,
    PatientIdentification,
    PatientInsurance,
    PatientMedicalHistory,
)
from felicity.apps.patient.repository import (
    IdentificationRepository,
    PatientIdentificationRepository,
    PatientRepository,
)
from felicity.apps.patient.schemas import (
    ClinicalDiagnosisCreate,
    ClinicalDiagnosisUpdate,
    GuarantorCreate,
    GuarantorUpdate,
    IdentificationCreate,
    IdentificationUpdate,
    InsuranceCompanyCreate,
    InsuranceCompanyUpdate,
    PatientCreate,
    PatientIdentificationCreate,
    PatientIdentificationUpdate,
    PatientInsuranceCreate,
    PatientInsuranceUpdate,
    PatientMedicalHistoryCreate,
    PatientMedicalHistoryUpdate,
    PatientUpdate,
)
from felicity.database.paging import PageCursor, PageInfo, EdgeNode


class IdentificationService(
    BaseService[Identification, IdentificationCreate, IdentificationUpdate]
):
    def __init__(self):
        super().__init__(IdentificationRepository())


class PatientIdentificationService(
    BaseService[
        PatientIdentification, PatientIdentificationCreate, PatientIdentificationUpdate
    ]
):
    def __init__(self):
        super().__init__(PatientIdentificationRepository())

    async def find_by_identification_value(
            self,
            value: str,
            identification_uid: Optional[str] = None,
            session: Optional[AsyncSession] = None
    ) -> Optional[PatientIdentification]:
        """
        HIPAA-compliant search for patient identification by encrypted value.
        
        Args:
            value: The identification value to search for
            identification_uid: Optional specific identification type
            session: Optional database session
            
        Returns:
            Matching patient identification or None
        """
        return await self.repository.find_by_encrypted_value(
            value=value,
            identification_uid=identification_uid,
            session=session
        )


class PatientService(BaseService[Patient, PatientCreate, PatientUpdate]):
    def __init__(self):
        self.id_sequence_service = IdSequenceService()
        super().__init__(PatientRepository())

    async def search(self, query_string: str | None = None) -> list[Patient]:
        """
        HIPAA-compliant patient search.
        
        For encrypted fields (first_name, last_name, phone_mobile, etc.),
        uses specialized repository methods that decrypt data for searching.
        For non-encrypted fields, uses standard database search.
        
        Args:
            query_string: Search term to match across patient fields
            
        Returns:
            List of matching patients
        """
        if not query_string:
            return []

        # Search non-encrypted fields using standard database queries
        non_encrypted_results = []
        non_encrypted_filters = {
            "patient_id": query_string,
            "client_patient_id": query_string,
        }
        for field, value in non_encrypted_filters.items():
            results = await super().search(**{field: value})
            non_encrypted_results.extend(results)

        # Search encrypted fields using specialized repository method
        encrypted_results = await self.repository.search_by_encrypted_fields(
            first_name=query_string,
            last_name=query_string,
            email=query_string,
            phone_mobile=query_string,
            date_of_birth=query_string
        )

        # Combine and deduplicate results
        all_results = non_encrypted_results + encrypted_results
        unique_results = []
        seen_uids = set()

        for patient in all_results:
            if patient.uid not in seen_uids:
                unique_results.append(patient)
                seen_uids.add(patient.uid)

        return unique_results

    async def hipaa_compliant_search(
            self,
            first_name: Optional[str] = None,
            last_name: Optional[str] = None,
            email: Optional[str] = None,
            phone_mobile: Optional[str] = None,
            date_of_birth: Optional[str] = None,
            patient_id: Optional[str] = None,
            client_patient_id: Optional[str] = None,
            session: Optional[AsyncSession] = None
    ) -> List[Patient]:
        """
        Perform HIPAA-compliant search across patient fields.
        
        Args:
            first_name: Patient first name to search
            last_name: Patient last name to search
            email: Patient email to search
            phone_mobile: Patient mobile phone to search
            date_of_birth: Patient date of birth to search (format: YYYY-MM-DD)
            patient_id: Patient ID to search (non-encrypted)
            client_patient_id: Client patient ID to search (non-encrypted)
            session: Optional database session
            
        Returns:
            List of matching patients
        """
        all_results = []

        # Search encrypted fields
        if any([first_name, last_name, email, phone_mobile, date_of_birth]):
            encrypted_results = await self.repository.search_by_encrypted_fields(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_mobile=phone_mobile,
                date_of_birth=date_of_birth,
                session=session
            )
            all_results.extend(encrypted_results)

        # Search non-encrypted fields
        if patient_id:
            result = await self.get(patient_id=patient_id, session=session)
            if result:
                all_results.append(result)

        if client_patient_id:
            result = await self.get(client_patient_id=client_patient_id, session=session)
            if result:
                all_results.append(result)

        # Deduplicate results
        unique_results = []
        seen_uids = set()

        for patient in all_results:
            if patient.uid not in seen_uids:
                unique_results.append(patient)
                seen_uids.add(patient.uid)

        return unique_results

    async def high_performance_search(
            self,
            first_name: Optional[str] = None,
            last_name: Optional[str] = None,
            email: Optional[str] = None,
            phone_mobile: Optional[str] = None,
            date_of_birth: Optional[str] = None,
            patient_id: Optional[str] = None,
            client_patient_id: Optional[str] = None,
            fuzzy_match: bool = False,
            session: Optional[AsyncSession] = None,
            return_uids: bool = False
    ) -> List[Patient | str]:
        """
        High-performance HIPAA-compliant search using searchable encryption indices.
        
        This method provides much better performance than the standard search methods
        by using pre-computed cryptographic indices instead of loading all patients
        into memory for filtering.
        
        Args:
            first_name: Patient first name to search
            last_name: Patient last name to search
            email: Patient email to search
            phone_mobile: Patient mobile phone to search
            date_of_birth: Patient date of birth to search (format: YYYY-MM-DD)
            patient_id: Patient ID to search (non-encrypted)
            client_patient_id: Client patient ID to search (non-encrypted)
            fuzzy_match: Enable phonetic/fuzzy matching for names
            session: Optional database session
            
        Returns:
            List of matching patients
            
        Note:
            This method requires searchable encryption indices to be maintained.
            Indices are automatically created/updated when patients are created/updated.
        """
        all_results = []

        # Search using high-performance indices for encrypted fields
        if any([first_name, last_name, email, phone_mobile, date_of_birth]):
            encrypted_results = await self.repository.search_by_encrypted_indices(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_mobile=phone_mobile,
                date_of_birth=date_of_birth,
                fuzzy_match=fuzzy_match,
                session=session,
                return_uids=return_uids
            )
            all_results.extend(encrypted_results)

        # Search non-encrypted fields using standard database queries
        if patient_id:
            result = await self.get(patient_id=patient_id, session=session)
            if result:
                all_results.append(result.uid if return_uids else result)

        if client_patient_id:
            result = await self.get(client_patient_id=client_patient_id, session=session)
            if result:
                all_results.append(result.uid if return_uids else result)

        # Deduplicate results
        unique_results = []
        seen_uids = set()

        if return_uids:
            unique_results = set(all_results)
        else:
            for patient in all_results:
                if patient.uid not in seen_uids:
                    unique_results.append(patient)
                    seen_uids.add(patient.uid)

        return unique_results

    def _encode_cursor(self, uid: str, position: int) -> str:
        """Encode cursor with patient UID and position."""
        cursor_data = {"uid": uid, "position": position}
        return base64.b64encode(json.dumps(cursor_data).encode()).decode()

    def _decode_cursor(self, cursor: str) -> dict:
        """Decode cursor to get patient UID and position."""
        try:
            cursor_data = json.loads(base64.b64decode(cursor.encode()).decode())
            return cursor_data
        except (ValueError, TypeError, json.JSONDecodeError):
            return {"uid": None, "position": 0}

    async def paging_filter(
            self,
            page_size: int | None = None,
            after_cursor: str | None = None,
            before_cursor: str | None = None,
            filters: list[dict] | dict | None = None,
            sort_by: list[str] | None = None,
            **kwargs,
    ) -> PageCursor:
        """
        HIPAA-compliant paginated filtering of patients.
        
        Overrides BaseService.paging_filter to use high-performance search
        when text search is detected in filters.
        
        Args:
            page_size: Number of items per page
            after_cursor: Cursor for fetching next page
            before_cursor: Cursor for fetching previous page
            filters: Filtering criteria
            sort_by: Sorting criteria
            **kwargs: Additional arguments including 'text' for search

        Returns:
            PageCursor with paginated results
        """
        # Check if this is a text search request
        search_text = kwargs.get('text')
        if search_text and search_text.strip():
            # Use HIPAA-compliant search for text queries
            search_results = await self.high_performance_search(
                first_name=search_text,
                last_name=search_text,
                email=search_text,
                phone_mobile=search_text,
                patient_id=search_text,
                client_patient_id=search_text,
                fuzzy_match=True
            )
            print(f"search results from hps: {search_results}")

            # Apply sorting
            if sort_by:
                for sort_field in reversed(sort_by):
                    reverse = sort_field.startswith('-')
                    field_name = sort_field.lstrip('-')
                    if hasattr(Patient, field_name):
                        search_results.sort(key=lambda x: getattr(x, field_name, ''), reverse=reverse)
            else:
                # Default sort by patient_id
                search_results.sort(key=lambda x: x.patient_id or '')

            total_count = len(search_results)

            # Apply cursor-based pagination
            paginated_results, start_idx, end_idx = self._apply_cursor_pagination(
                search_results, page_size, after_cursor, before_cursor
            )

            # Create edges with proper cursors
            edges = []
            for i, patient in enumerate(paginated_results):
                cursor = self._encode_cursor(patient.uid, start_idx + i)
                edges.append(EdgeNode(cursor=cursor, node=patient))

            # Create page info
            page_info = PageInfo(
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
                has_next_page=end_idx < total_count,
                has_previous_page=start_idx > 0,
            )

            return PageCursor(
                total_count=total_count,
                edges=edges,
                items=paginated_results,
                page_info=page_info
            )
        else:
            # For non-text queries, use the standard repository pagination
            return await super().paging_filter(
                page_size=page_size,
                after_cursor=after_cursor,
                before_cursor=before_cursor,
                filters=filters,
                sort_by=sort_by,
                **kwargs
            )

    def _apply_cursor_pagination(self, results: List[Patient], page_size: int | None,
                                 after_cursor: str | None, before_cursor: str | None) -> tuple:
        """Apply cursor-based pagination to search results."""
        if not results:
            return [], 0, 0

        # Find start position based on cursors
        start_idx = 0
        if after_cursor:
            cursor_data = self._decode_cursor(after_cursor)
            cursor_uid = cursor_data.get("uid")
            if cursor_uid:
                # Find position of the cursor UID in results
                for i, patient in enumerate(results):
                    if patient.uid == cursor_uid:
                        start_idx = i + 1  # Start after the cursor
                        break

        if before_cursor:
            cursor_data = self._decode_cursor(before_cursor)
            cursor_uid = cursor_data.get("uid")
            if cursor_uid:
                # Find position of the cursor UID in results
                for i, patient in enumerate(results):
                    if patient.uid == cursor_uid:
                        results = results[:i]  # Take items before cursor
                        break

        # Apply page size limit
        end_idx = len(results)
        if page_size:
            end_idx = min(start_idx + page_size, len(results))

        paginated_results = results[start_idx:end_idx]

        return paginated_results, start_idx, end_idx

    async def create(
            self, obj_in: dict | PatientCreate, related: list[str] | None = None,
            commit: bool = True, session: AsyncSession | None = None
    ) -> Patient:
        data = self._import(obj_in)
        data["patient_id"] = (
            await self.id_sequence_service.get_next_number(prefix="P", generic=True, commit=commit, session=session)
        )[1]

        # Create the patient
        patient = await super().create(data, related, commit=commit, session=session)

        # Create searchable encryption indices for high-performance searching
        await self.repository.create_search_indices(patient, session=session)

        return patient

    async def update(
            self, uid: str, update: PatientUpdate | dict, related: list[str] | None = None,
            commit: bool = True, session: AsyncSession | None = None
    ) -> Patient:
        """
        Update a patient and maintain searchable encryption indices.
        
        Args:
            uid: Patient UID to update
            update: Update data
            related: Related entities to fetch
            commit: Whether to commit the transaction
            session: Optional database session
            
        Returns:
            Updated patient entity
        """
        # Update the patient
        patient = await super().update(uid, update, related, commit=commit, session=session)

        # Update searchable encryption indices for high-performance searching
        await self.repository.update_search_indices(patient, session=session)

        return patient

    async def snapshot(self, pt: Patient, metadata: dict = {}):
        fields = ["client", "province", "district", "country"]
        patient = await self.get(related=["province", "district", "country"], uid=pt.uid)
        for _field in fields:
            if _field not in metadata:
                if _field == "client":
                    client = await ClientService().get(related=["province", "district"], uid=pt.client_uid)
                    metadata[_field] = client.snapshot()
                    metadata[_field]["province"] = client.province.snapshot() if client.province else None
                    metadata[_field]["district"] = client.district.snapshot() if client.district else None
                if _field == "province":
                    metadata[_field] = patient.province.snapshot() if patient.province else None
                if _field == "district":
                    metadata[_field] = patient.district.snapshot() if patient.district else None
                if _field == "country":
                    metadata[_field] = patient.country.snapshot() if patient.country else None
        return await self.update(pt.uid, {"metadata_snapshot": marshaller(metadata, depth=3)})


class PatientMedicalHistoryService(
    BaseService[PatientMedicalHistory, PatientMedicalHistoryCreate, PatientMedicalHistoryUpdate]
):
    """Service for managing patient medical history."""
    
    def __init__(self):
        from felicity.apps.patient.repository import PatientMedicalHistoryRepository
        super().__init__(PatientMedicalHistoryRepository())
    
    async def get_by_patient(
        self,
        patient_uid: str,
        session: Optional[AsyncSession] = None
    ) -> Optional[PatientMedicalHistory]:
        """Get medical history for a patient."""
        return await self.repository.get_by_patient_uid(patient_uid, session=session)
    
    async def create_or_update(
        self,
        patient_uid: str,
        data: dict,
        session: Optional[AsyncSession] = None
    ) -> PatientMedicalHistory:
        """Create medical history if it doesn't exist, otherwise update."""
        existing = await self.get_by_patient(patient_uid, session=session)
        if existing:
            return await self.update(existing.uid, data, session=session)
        data['patient_uid'] = patient_uid
        return await self.create(data, session=session)
    
    async def add_chronic_condition(
        self,
        patient_uid: str,
        condition: dict,
        session: Optional[AsyncSession] = None
    ) -> PatientMedicalHistory:
        """Add a chronic condition to patient's medical history."""
        history = await self.get_by_patient(patient_uid, session=session)
        if not history:
            # Create medical history if it doesn't exist
            history = await self.create({'patient_uid': patient_uid}, session=session)
        
        return await self.repository.add_chronic_condition(history.uid, condition, session=session)
    
    async def remove_chronic_condition(
        self,
        patient_uid: str,
        index: int,
        session: Optional[AsyncSession] = None
    ) -> PatientMedicalHistory:
        """Remove a chronic condition by index."""
        history = await self.get_by_patient(patient_uid, session=session)
        if not history:
            raise ValueError("Medical history not found for patient")
        
        return await self.repository.remove_chronic_condition(history.uid, index, session=session)
    
    async def add_medication(
        self,
        patient_uid: str,
        medication: dict,
        session: Optional[AsyncSession] = None
    ) -> PatientMedicalHistory:
        """Add a medication to patient's treatment history."""
        history = await self.get_by_patient(patient_uid, session=session)
        if not history:
            history = await self.create({'patient_uid': patient_uid}, session=session)
        
        return await self.repository.add_medication(history.uid, medication, session=session)
    
    async def remove_medication(
        self,
        patient_uid: str,
        index: int,
        session: Optional[AsyncSession] = None
    ) -> PatientMedicalHistory:
        """Remove a medication by index."""
        history = await self.get_by_patient(patient_uid, session=session)
        if not history:
            raise ValueError("Medical history not found for patient")
        
        return await self.repository.remove_medication(history.uid, index, session=session)
    
    async def add_allergy(
        self,
        patient_uid: str,
        allergy: dict,
        session: Optional[AsyncSession] = None
    ) -> PatientMedicalHistory:
        """Add an allergy to patient's medical history."""
        history = await self.get_by_patient(patient_uid, session=session)
        if not history:
            history = await self.create({'patient_uid': patient_uid}, session=session)
        
        return await self.repository.add_allergy(history.uid, allergy, session=session)
    
    async def remove_allergy(
        self,
        patient_uid: str,
        index: int,
        session: Optional[AsyncSession] = None
    ) -> PatientMedicalHistory:
        """Remove an allergy by index."""
        history = await self.get_by_patient(patient_uid, session=session)
        if not history:
            raise ValueError("Medical history not found for patient")
        
        return await self.repository.remove_allergy(history.uid, index, session=session)
    
    async def get_active_medications(
        self,
        patient_uid: str,
        session: Optional[AsyncSession] = None
    ) -> list:
        """Get patient's active medications."""
        history = await self.get_by_patient(patient_uid, session=session)
        if not history:
            return []
        return history.active_medications
    
    async def get_verified_allergies(
        self,
        patient_uid: str,
        session: Optional[AsyncSession] = None
    ) -> list:
        """Get patient's verified allergies."""
        history = await self.get_by_patient(patient_uid, session=session)
        if not history:
            return []
        return history.verified_allergies


class InsuranceCompanyService(
    BaseService[InsuranceCompany, InsuranceCompanyCreate, InsuranceCompanyUpdate]
):
    """Service for managing insurance companies."""
    
    def __init__(self):
        from felicity.apps.patient.repository import InsuranceCompanyRepository
        super().__init__(InsuranceCompanyRepository())
    
    async def get_active_companies(
        self,
        session: Optional[AsyncSession] = None
    ) -> List[InsuranceCompany]:
        """Get all active insurance companies."""
        return await self.repository.get_active_companies(session=session)
    
    async def find_by_code(
        self,
        code: str,
        session: Optional[AsyncSession] = None
    ) -> Optional[InsuranceCompany]:
        """Find insurance company by payer code."""
        return await self.repository.find_by_code(code, session=session)
    
    async def find_by_name(
        self,
        name: str,
        session: Optional[AsyncSession] = None
    ) -> Optional[InsuranceCompany]:
        """Find insurance company by name."""
        return await self.repository.find_by_name(name, session=session)


class PatientInsuranceService(
    BaseService[PatientInsurance, PatientInsuranceCreate, PatientInsuranceUpdate]
):
    """Service for managing patient insurance policies."""
    
    def __init__(self):
        from felicity.apps.patient.repository import PatientInsuranceRepository
        super().__init__(PatientInsuranceRepository())
    
    async def get_by_patient(
        self,
        patient_uid: str,
        active_only: bool = True,
        session: Optional[AsyncSession] = None
    ) -> List[PatientInsurance]:
        """Get all insurance policies for a patient."""
        return await self.repository.get_by_patient_uid(patient_uid, active_only, session=session)
    
    async def get_primary_insurance(
        self,
        patient_uid: str,
        session: Optional[AsyncSession] = None
    ) -> Optional[PatientInsurance]:
        """Get patient's primary insurance."""
        return await self.repository.get_primary_insurance(patient_uid, session=session)
    
    async def get_by_priority(
        self,
        patient_uid: str,
        priority: str,
        session: Optional[AsyncSession] = None
    ) -> Optional[PatientInsurance]:
        """Get insurance by priority (primary, secondary, tertiary)."""
        return await self.repository.get_by_priority(patient_uid, priority, session=session)
    
    async def validate_insurance(
        self,
        insurance_uid: str,
        session: Optional[AsyncSession] = None
    ) -> dict:
        """
        Validate insurance policy and return status.
        
        Returns:
            Dict with keys: is_valid, reason, coverage_active
        """
        insurance = await self.get(uid=insurance_uid, session=session)
        if not insurance:
            return {"is_valid": False, "reason": "Insurance not found", "coverage_active": False}
        
        if not insurance.is_active:
            return {"is_valid": False, "reason": "Insurance policy is inactive", "coverage_active": False}
        
        if not insurance.is_valid:
            return {"is_valid": False, "reason": "Insurance policy is expired or not yet effective", "coverage_active": False}
        
        return {"is_valid": True, "reason": "Insurance policy is valid", "coverage_active": True}


class GuarantorService(
    BaseService[Guarantor, GuarantorCreate, GuarantorUpdate]
):
    """Service for managing patient guarantors."""
    
    def __init__(self):
        from felicity.apps.patient.repository import GuarantorRepository
        super().__init__(GuarantorRepository())
    
    async def get_by_patient(
        self,
        patient_uid: str,
        session: Optional[AsyncSession] = None
    ) -> Optional[Guarantor]:
        """Get guarantor for a patient."""
        return await self.repository.get_by_patient_uid(patient_uid, session=session)
    
    async def create_or_update(
        self,
        patient_uid: str,
        data: dict,
        session: Optional[AsyncSession] = None
    ) -> Guarantor:
        """Create guarantor if it doesn't exist, otherwise update."""
        existing = await self.get_by_patient(patient_uid, session=session)
        if existing:
            return await self.update(existing.uid, data, session=session)
        data['patient_uid'] = patient_uid
        return await self.create(data, session=session)


class ClinicalDiagnosisService(
    BaseService[ClinicalDiagnosis, ClinicalDiagnosisCreate, ClinicalDiagnosisUpdate]
):
    """Service for managing clinical diagnoses."""
    
    def __init__(self):
        from felicity.apps.patient.repository import ClinicalDiagnosisRepository
        super().__init__(ClinicalDiagnosisRepository())
    
    async def get_by_patient(
        self,
        patient_uid: str,
        active_only: bool = True,
        session: Optional[AsyncSession] = None
    ) -> List[ClinicalDiagnosis]:
        """Get all diagnoses for a patient."""
        return await self.repository.get_by_patient_uid(patient_uid, active_only, session=session)
    
    async def get_by_icd10_code(
        self,
        patient_uid: str,
        icd10_code: str,
        session: Optional[AsyncSession] = None
    ) -> Optional[ClinicalDiagnosis]:
        """Find diagnosis by ICD-10 code for a patient."""
        return await self.repository.get_by_icd10_code(patient_uid, icd10_code, session=session)
    
    async def get_by_analysis_request(
        self,
        analysis_request_uid: str,
        session: Optional[AsyncSession] = None
    ) -> List[ClinicalDiagnosis]:
        """Get diagnoses linked to a specific analysis request."""
        return await self.repository.get_by_analysis_request(analysis_request_uid, session=session)
    
    async def get_primary_diagnosis(
        self,
        patient_uid: str,
        session: Optional[AsyncSession] = None
    ) -> Optional[ClinicalDiagnosis]:
        """Get patient's primary diagnosis."""
        return await self.repository.get_primary_diagnosis(patient_uid, session=session)
    
    async def assign_diagnosis_pointers(
        self,
        patient_uid: str,
        session: Optional[AsyncSession] = None
    ) -> List[ClinicalDiagnosis]:
        """
        Assign diagnosis pointers (A, B, C, D) for 837 claims.
        Primary diagnosis gets 'A', others get B, C, D in order.
        """
        diagnoses = await self.get_by_patient(patient_uid, active_only=True, session=session)
        
        pointers = ['A', 'B', 'C', 'D']
        
        # Sort by diagnosis_type (primary first) and diagnosis_date
        sorted_diagnoses = sorted(
            diagnoses,
            key=lambda d: (
                0 if d.diagnosis_type == 'primary' else 1,
                d.diagnosis_date
            )
        )
        
        # Assign pointers
        for i, diagnosis in enumerate(sorted_diagnoses[:4]):  # Max 4 diagnosis pointers
            if diagnosis.pointer != pointers[i]:
                await self.update(diagnosis.uid, {"pointer": pointers[i]}, session=session)
        
        return await self.get_by_patient(patient_uid, active_only=True, session=session)
