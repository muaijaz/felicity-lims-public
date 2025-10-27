"""
Reference Data Entities

Medication and toxicology test reference database for LCMS workflows.
"""
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Date, Float, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, relationship

from felicity.apps.abstract.entity import BaseEntity, LabScopedEntity

if TYPE_CHECKING:
    from felicity.apps.user.entities import User


class Medication(BaseEntity):
    """
    Comprehensive medication reference database.

    Provides detailed medication information including:
    - Drug identification (generic name, brand names, chemical properties)
    - Classification codes (ATC, NDC, RxCUI)
    - Clinical information (indications, contraindications, dosing)
    - Metabolism and pharmacokinetics
    - Toxicology testing requirements

    This is a reference entity (BaseEntity) shared across all laboratories.
    """
    __tablename__ = "medication"

    # Drug Identification
    name = Column(String, nullable=False, unique=True, index=True)  # Generic name
    brand_names = Column(JSONB, nullable=True)  # ["Glucophage", "Fortamet"]
    drug_class = Column(String, nullable=True, index=True)  # "Antidiabetic - Biguanide"
    therapeutic_category = Column(String, nullable=True, index=True)  # "Diabetes Management"

    # Chemical Properties
    chemical_name = Column(String, nullable=True)  # IUPAC name
    molecular_formula = Column(String, nullable=True)  # C4H11N5
    molecular_weight = Column(Float, nullable=True)  # 129.16 g/mol
    cas_number = Column(String, nullable=True)  # 657-24-9

    # Classification Codes
    atc_code = Column(String, nullable=True, index=True)  # A10BA02 (Anatomical Therapeutic Chemical)
    ndc_codes = Column(JSONB, nullable=True)  # National Drug Codes
    rxcui = Column(String, nullable=True, index=True)  # RxNorm Concept Unique Identifier

    # Clinical Information
    mechanism_of_action = Column(Text, nullable=True)
    indications = Column(JSONB, nullable=True)  # ["Type 2 Diabetes", "PCOS"]
    contraindications = Column(JSONB, nullable=True)
    half_life = Column(String, nullable=True)  # "4-8 hours"

    # Dosing Information
    typical_dose_range = Column(String, nullable=True)  # "500-2000 mg/day"
    dosage_forms = Column(JSONB, nullable=True)  # ["Tablet", "Liquid", "ER"]
    routes_of_administration = Column(JSONB, nullable=True)  # ["Oral", "IV"]

    # Metabolism & Excretion
    primary_metabolism = Column(String, nullable=True)  # "Hepatic CYP2D6"
    active_metabolites = Column(JSONB, nullable=True)  # List of metabolites
    excretion_route = Column(String, nullable=True)  # "Renal 90%, Fecal 10%"

    # Toxicology Relevance
    is_controlled_substance = Column(Boolean, default=False, index=True)
    dea_schedule = Column(String, nullable=True)  # I, II, III, IV, V
    therapeutic_window = Column(String, nullable=True)  # "5-20 mcg/mL"
    toxic_level = Column(String, nullable=True)  # ">30 mcg/mL"

    # Testing Information
    commonly_screened = Column(Boolean, default=False, index=True)  # Include in standard tox panels
    requires_confirmation = Column(Boolean, default=False)  # Needs confirmatory testing
    detection_window_urine = Column(String, nullable=True)  # "2-4 days"
    detection_window_blood = Column(String, nullable=True)  # "4-6 hours"
    detection_window_oral_fluid = Column(String, nullable=True)  # "1-2 days"

    # Reference Data
    fda_approved = Column(Boolean, default=True)
    approval_date = Column(Date, nullable=True)
    black_box_warning = Column(Boolean, default=False)
    pregnancy_category = Column(String, nullable=True)  # A, B, C, D, X (legacy)
    pregnancy_risk = Column(String, nullable=True)  # Modern PLLR categories

    # System Fields
    is_active = Column(Boolean, default=True, index=True)
    synonyms = Column(JSONB, nullable=True)  # Alternative names
    notes = Column(Text, nullable=True)

    # Relationships
    test_associations: Mapped[list["MedicationTestAssociation"]] = relationship(
        "MedicationTestAssociation", back_populates="medication", lazy="selectin"
    )

    @property
    def all_names(self) -> list[str]:
        """Get all names including generic and brand names."""
        names = [self.name]
        if self.brand_names:
            names.extend(self.brand_names)
        if self.synonyms:
            names.extend(self.synonyms)
        return names

    @property
    def requires_specific_test(self) -> bool:
        """
        Determine if medication requires specific testing.
        Some drugs don't cross-react with immunoassay screens.
        """
        # This would be calculated based on test associations
        return self.requires_confirmation or not self.commonly_screened

    def __repr__(self):
        return f"<Medication(name='{self.name}', class='{self.drug_class}')>"


class ToxicologyTest(LabScopedEntity):
    """
    Toxicology test definition.

    Defines specific toxicology tests/assays available in the laboratory.
    Can be immunoassay screens or LC-MS/MS confirmation tests.

    Laboratory-scoped to allow different labs to have different test menus.
    """
    __tablename__ = "toxicology_test"

    # Test Identification
    test_name = Column(String, nullable=False, index=True)  # "Benzodiazepine Screen"
    test_code = Column(String, nullable=False, index=True)  # "BENZO-SCRN"
    cpt_code = Column(String, nullable=True)  # 80307 for billing
    loinc_code = Column(String, nullable=True, index=True)  # Standard test identifier

    # Test Classification
    test_category = Column(String, nullable=False, index=True)  # "Drug Screen", "Therapeutic Monitoring", "Confirmation"
    test_type = Column(String, nullable=False)  # "Immunoassay", "LCMS", "GCMS"
    specimen_type = Column(String, nullable=False, index=True)  # "Urine", "Blood", "Oral Fluid"

    # Analytical Information
    method = Column(String, nullable=True)  # "LC-MS/MS", "EMIT", "ELISA"
    instrument_type = Column(String, nullable=True)  # "Agilent 6460", "Roche Cobas"
    analytical_range = Column(String, nullable=True)  # "5-1000 ng/mL"
    limit_of_detection = Column(String, nullable=True)  # "2 ng/mL"
    limit_of_quantitation = Column(String, nullable=True)  # "5 ng/mL"

    # Test Performance
    cutoff_value = Column(Float, nullable=True)  # Screening cutoff
    cutoff_units = Column(String, nullable=True)  # "ng/mL"
    confirmation_cutoff = Column(Float, nullable=True)  # Lower cutoff for confirmation
    turnaround_time = Column(String, nullable=True)  # "Same day", "24 hours"

    # Clinical Context
    clinical_utility = Column(Text, nullable=True)
    interpretation_notes = Column(Text, nullable=True)

    # Panel Information
    panel_name = Column(String, nullable=True, index=True)  # "Pain Management Panel", "5-Panel DOT"
    is_part_of_panel = Column(Boolean, default=False)
    panel_components = Column(JSONB, nullable=True)  # List of component test UIDs for panels

    # Regulatory
    clia_complexity = Column(String, nullable=True)  # "Waived", "Moderate", "High"
    requires_medical_necessity = Column(Boolean, default=False)

    # Pricing (optional)
    test_price = Column(Numeric(10, 2), nullable=True)

    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_stat_available = Column(Boolean, default=False)
    is_send_out = Column(Boolean, default=False)  # Sent to reference lab

    # Relationships
    medication_associations: Mapped[list["MedicationTestAssociation"]] = relationship(
        "MedicationTestAssociation", back_populates="toxicology_test", lazy="selectin"
    )

    @property
    def is_screening_test(self) -> bool:
        """Check if this is a screening test (immunoassay)."""
        return self.test_category.lower() in ["drug screen", "screening"]

    @property
    def is_confirmation_test(self) -> bool:
        """Check if this is a confirmation test (LC-MS/MS)."""
        return self.test_category.lower() in ["confirmation", "confirmatory"]

    def __repr__(self):
        return f"<ToxicologyTest(name='{self.test_name}', code='{self.test_code}')>"


class MedicationTestAssociation(BaseEntity):
    """
    Many-to-many association between medications and toxicology tests.

    Maps which tests detect which medications, including information about:
    - Direct detection vs metabolite detection
    - Cross-reactivity
    - False positives/negatives
    - Test recommendations

    Shared reference data (BaseEntity) used across all laboratories.
    """
    __tablename__ = "medication_test_association"

    medication_uid = Column(String, ForeignKey("medication.uid"), nullable=False, index=True)
    toxicology_test_uid = Column(String, ForeignKey("toxicology_test.uid"), nullable=False, index=True)

    # Association Details
    association_type = Column(String, nullable=False, index=True)  # "primary", "metabolite", "cross_reactive"

    # Detection Information
    is_direct_detection = Column(Boolean, default=True)  # True if drug itself is detected
    detected_as = Column(String, nullable=True)  # "Parent drug" or "Metabolite name"
    detection_sensitivity = Column(String, nullable=True)  # "High", "Moderate", "Low"
    cross_reactivity_level = Column(String, nullable=True)  # "High", "Moderate", "Low", "None"

    # Clinical Relevance
    clinical_significance = Column(Text, nullable=True)
    interpretation_guidance = Column(Text, nullable=True)

    # Interference Information
    causes_false_positive = Column(Boolean, default=False, index=True)
    causes_false_negative = Column(Boolean, default=False)
    interference_notes = Column(Text, nullable=True)

    # Priority & Recommendations
    is_preferred_test = Column(Boolean, default=False, index=True)  # Recommended test for this medication
    is_confirmatory_test = Column(Boolean, default=False)
    requires_additional_testing = Column(Boolean, default=False)
    recommended_followup_test_uid = Column(String, ForeignKey("toxicology_test.uid"), nullable=True)

    # Quantitative Information
    expected_concentration_range = Column(String, nullable=True)  # "50-200 ng/mL"
    therapeutic_concentration = Column(String, nullable=True)  # "10-50 ng/mL"

    # Status
    is_active = Column(Boolean, default=True, index=True)
    notes = Column(Text, nullable=True)

    # Relationships
    medication: Mapped["Medication"] = relationship(
        "Medication", back_populates="test_associations", foreign_keys=[medication_uid]
    )
    toxicology_test: Mapped["ToxicologyTest"] = relationship(
        "ToxicologyTest", back_populates="medication_associations", foreign_keys=[toxicology_test_uid]
    )
    recommended_followup_test: Mapped["ToxicologyTest"] = relationship(
        "ToxicologyTest", foreign_keys=[recommended_followup_test_uid]
    )

    @property
    def requires_confirmation(self) -> bool:
        """Determine if this association requires confirmatory testing."""
        return (
            self.requires_additional_testing or
            self.cross_reactivity_level in ["High", "Moderate"] or
            self.causes_false_positive
        )

    def __repr__(self):
        return f"<MedicationTestAssociation(medication='{self.medication.name if self.medication else 'N/A'}', test='{self.toxicology_test.test_name if self.toxicology_test else 'N/A'}')>"


# Indexes for performance
Index('idx_medication_name_active', Medication.name, Medication.is_active)
Index('idx_medication_class_active', Medication.drug_class, Medication.is_active)
Index('idx_medication_controlled', Medication.is_controlled_substance, Medication.is_active)

Index('idx_tox_test_category_specimen', ToxicologyTest.test_category, ToxicologyTest.specimen_type)
Index('idx_tox_test_panel', ToxicologyTest.panel_name, ToxicologyTest.is_active)
Index('idx_tox_test_lab', ToxicologyTest.laboratory_uid, ToxicologyTest.is_active)

Index('idx_med_test_assoc_medication', MedicationTestAssociation.medication_uid, MedicationTestAssociation.is_active)
Index('idx_med_test_assoc_test', MedicationTestAssociation.toxicology_test_uid, MedicationTestAssociation.is_active)
Index('idx_med_test_assoc_type', MedicationTestAssociation.association_type, MedicationTestAssociation.is_active)
Index('idx_med_test_assoc_preferred', MedicationTestAssociation.is_preferred_test, MedicationTestAssociation.is_active)
