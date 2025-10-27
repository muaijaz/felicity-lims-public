"""
Reference Data Repositories

Data access layer for medication and toxicology test reference data.
"""
from typing import List, Optional

from sqlalchemy import and_, or_, func
from sqlalchemy.future import select

from felicity.apps.abstract.repository import BaseRepository
from felicity.apps.reference.entities import (
    Medication,
    MedicationTestAssociation,
    ToxicologyTest,
)


class MedicationRepository(BaseRepository[Medication]):
    """Repository for medication reference data."""

    def __init__(self) -> None:
        super().__init__(Medication)

    async def get_by_name(self, name: str) -> Optional[Medication]:
        """Get medication by exact name match."""
        return await self.get(name=name)

    async def search_by_name(self, query: str, limit: int = 20) -> List[Medication]:
        """
        Search medications by name (generic, brand, or synonym).
        Case-insensitive partial match.
        """
        async with self.async_session() as session:
            # Search in name, brand_names, and synonyms
            stmt = (
                select(Medication)
                .where(
                    and_(
                        Medication.is_active == True,
                        or_(
                            func.lower(Medication.name).contains(query.lower()),
                            func.lower(func.cast(Medication.brand_names, String)).contains(query.lower()),
                            func.lower(func.cast(Medication.synonyms, String)).contains(query.lower()),
                        )
                    )
                )
                .limit(limit)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_by_drug_class(self, drug_class: str) -> List[Medication]:
        """Get all medications in a specific drug class."""
        return await self.get_all(drug_class=drug_class, is_active=True)

    async def get_by_therapeutic_category(self, category: str) -> List[Medication]:
        """Get all medications in a therapeutic category."""
        return await self.get_all(therapeutic_category=category, is_active=True)

    async def get_controlled_substances(self, dea_schedule: Optional[str] = None) -> List[Medication]:
        """Get all controlled substances, optionally filtered by DEA schedule."""
        filters = {"is_controlled_substance": True, "is_active": True}
        if dea_schedule:
            filters["dea_schedule"] = dea_schedule
        return await self.get_all(**filters)

    async def get_commonly_screened(self) -> List[Medication]:
        """Get medications commonly included in toxicology screening panels."""
        return await self.get_all(commonly_screened=True, is_active=True)

    async def get_by_atc_code(self, atc_code: str) -> Optional[Medication]:
        """Get medication by ATC code."""
        return await self.get(atc_code=atc_code, is_active=True)

    async def get_by_rxcui(self, rxcui: str) -> Optional[Medication]:
        """Get medication by RxNorm Concept Unique Identifier."""
        return await self.get(rxcui=rxcui, is_active=True)


class ToxicologyTestRepository(BaseRepository[ToxicologyTest]):
    """Repository for toxicology test data."""

    def __init__(self) -> None:
        super().__init__(ToxicologyTest)

    async def get_by_test_code(self, test_code: str, laboratory_uid: str) -> Optional[ToxicologyTest]:
        """Get test by test code within a laboratory."""
        return await self.get(test_code=test_code, laboratory_uid=laboratory_uid, is_active=True)

    async def get_by_category(
        self, test_category: str, laboratory_uid: str
    ) -> List[ToxicologyTest]:
        """Get all tests in a category for a laboratory."""
        return await self.get_all(
            test_category=test_category,
            laboratory_uid=laboratory_uid,
            is_active=True
        )

    async def get_by_specimen_type(
        self, specimen_type: str, laboratory_uid: str
    ) -> List[ToxicologyTest]:
        """Get all tests for a specimen type in a laboratory."""
        return await self.get_all(
            specimen_type=specimen_type,
            laboratory_uid=laboratory_uid,
            is_active=True
        )

    async def get_screening_tests(self, laboratory_uid: str) -> List[ToxicologyTest]:
        """Get all screening tests (immunoassay) for a laboratory."""
        async with self.async_session() as session:
            stmt = (
                select(ToxicologyTest)
                .where(
                    and_(
                        ToxicologyTest.laboratory_uid == laboratory_uid,
                        ToxicologyTest.is_active == True,
                        or_(
                            ToxicologyTest.test_category.ilike("%screen%"),
                            ToxicologyTest.test_type.ilike("%immunoassay%")
                        )
                    )
                )
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_confirmation_tests(self, laboratory_uid: str) -> List[ToxicologyTest]:
        """Get all confirmation tests (LC-MS/MS) for a laboratory."""
        async with self.async_session() as session:
            stmt = (
                select(ToxicologyTest)
                .where(
                    and_(
                        ToxicologyTest.laboratory_uid == laboratory_uid,
                        ToxicologyTest.is_active == True,
                        or_(
                            ToxicologyTest.test_category.ilike("%confirm%"),
                            ToxicologyTest.test_type.ilike("%lcms%"),
                            ToxicologyTest.test_type.ilike("%gcms%")
                        )
                    )
                )
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_by_panel(self, panel_name: str, laboratory_uid: str) -> List[ToxicologyTest]:
        """Get all tests in a specific panel."""
        return await self.get_all(
            panel_name=panel_name,
            laboratory_uid=laboratory_uid,
            is_active=True
        )

    async def get_available_panels(self, laboratory_uid: str) -> List[str]:
        """Get list of available panel names for a laboratory."""
        async with self.async_session() as session:
            stmt = (
                select(ToxicologyTest.panel_name)
                .where(
                    and_(
                        ToxicologyTest.laboratory_uid == laboratory_uid,
                        ToxicologyTest.is_active == True,
                        ToxicologyTest.panel_name.isnot(None)
                    )
                )
                .distinct()
            )
            result = await session.execute(stmt)
            return [row[0] for row in result.all()]

    async def get_stat_tests(self, laboratory_uid: str) -> List[ToxicologyTest]:
        """Get all STAT-available tests."""
        return await self.get_all(
            laboratory_uid=laboratory_uid,
            is_stat_available=True,
            is_active=True
        )


class MedicationTestAssociationRepository(BaseRepository[MedicationTestAssociation]):
    """Repository for medication-test associations."""

    def __init__(self) -> None:
        super().__init__(MedicationTestAssociation)

    async def get_tests_for_medication(
        self, medication_uid: str, active_only: bool = True
    ) -> List[MedicationTestAssociation]:
        """Get all test associations for a medication."""
        filters = {"medication_uid": medication_uid}
        if active_only:
            filters["is_active"] = True
        return await self.get_all(**filters)

    async def get_medications_for_test(
        self, toxicology_test_uid: str, active_only: bool = True
    ) -> List[MedicationTestAssociation]:
        """Get all medication associations for a test."""
        filters = {"toxicology_test_uid": toxicology_test_uid}
        if active_only:
            filters["is_active"] = True
        return await self.get_all(**filters)

    async def get_preferred_tests_for_medication(
        self, medication_uid: str
    ) -> List[MedicationTestAssociation]:
        """Get preferred/recommended tests for a medication."""
        return await self.get_all(
            medication_uid=medication_uid,
            is_preferred_test=True,
            is_active=True
        )

    async def get_by_association_type(
        self, medication_uid: str, association_type: str
    ) -> List[MedicationTestAssociation]:
        """
        Get associations by type.
        Types: 'primary', 'metabolite', 'cross_reactive'
        """
        return await self.get_all(
            medication_uid=medication_uid,
            association_type=association_type,
            is_active=True
        )

    async def get_false_positive_risks(
        self, toxicology_test_uid: str
    ) -> List[MedicationTestAssociation]:
        """Get medications that can cause false positives for a test."""
        return await self.get_all(
            toxicology_test_uid=toxicology_test_uid,
            causes_false_positive=True,
            is_active=True
        )

    async def get_confirmatory_tests_needed(
        self, medication_uid: str
    ) -> List[MedicationTestAssociation]:
        """Get associations that require confirmatory testing."""
        async with self.async_session() as session:
            stmt = (
                select(MedicationTestAssociation)
                .where(
                    and_(
                        MedicationTestAssociation.medication_uid == medication_uid,
                        MedicationTestAssociation.is_active == True,
                        or_(
                            MedicationTestAssociation.requires_additional_testing == True,
                            MedicationTestAssociation.is_confirmatory_test == True
                        )
                    )
                )
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_by_medication_names(
        self, medication_names: List[str]
    ) -> List[MedicationTestAssociation]:
        """
        Get all test associations for a list of medication names.
        Useful for patient medication lists.
        """
        async with self.async_session() as session:
            # First get medication UIDs
            stmt = (
                select(Medication.uid)
                .where(
                    and_(
                        Medication.name.in_(medication_names),
                        Medication.is_active == True
                    )
                )
            )
            result = await session.execute(stmt)
            medication_uids = [row[0] for row in result.all()]

            if not medication_uids:
                return []

            # Then get associations
            stmt = (
                select(MedicationTestAssociation)
                .where(
                    and_(
                        MedicationTestAssociation.medication_uid.in_(medication_uids),
                        MedicationTestAssociation.is_active == True
                    )
                )
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())
