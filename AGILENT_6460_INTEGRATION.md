# Agilent 6460 Triple Quad LC/MS Integration Guide

**Instrument System**: Agilent 6460 Triple Quadrupole LC/MS with 1260 Infinity HPLC
**Software**: MassHunter Workstation (Acquisition, Quantitative Analysis, Qualitative Analysis)
**Target LIMS**: Felicity LIMS
**Date**: October 27, 2025

---

## Executive Summary

This document provides comprehensive specifications and integration strategies for connecting the **Agilent 6460 Triple Quadrupole LC/MS system** with **Agilent 1260 Infinity HPLC** to Felicity LIMS. The integration enables:

1. **Bidirectional Worklist Communication** - Send sample sequences from LIMS to instrument
2. **Automated Result Import** - Import quantitative results back into LIMS
3. **Patient-Linked Analysis** - Associate LCMS results with patient medical history
4. **Quality Control** - Track QC samples, calibration curves, and system suitability
5. **Audit Compliance** - Maintain complete audit trails for regulatory compliance

---

## Instrument System Overview

### Agilent 6460 Triple Quadrupole LC/MS

**Model**: G6460C (with Jet Stream Technology)

**Key Specifications:**
- **Mass Range**: m/z 5-3,000
- **Polarity Switching**: 30 ms
- **Mass Resolution**: 0.7 Da (autotune), 0.5 Da (manual tune)
- **Maximum Scan Rate**: 12,500 Da/s
- **Dynamic Range**: > 6.0 × 10⁶
- **MRM Transitions**: 450 per time segment, >13,500 per method
- **Sensitivity (ESI+)**: S/N > 10,000:1 (femtogram barrier)
- **Sensitivity (ESI-)**: S/N > 3,000:1

**Technology:**
- **Jet Stream Thermal Gradient Focusing** - Super-heated nitrogen reduces noise and boosts signals
- **Enhanced Ion Generation** - Improved desolvation and ionization efficiency
- **Triple Quadrupole Architecture** - Q1 (mass filter) → Q2 (collision cell) → Q3 (mass filter)

**Applications:**
- Pharmaceutical quantification (drug development, bioanalysis)
- Environmental contaminants (trace-level analysis)
- Food safety (pesticide residues, veterinary drugs)
- Clinical diagnostics (therapeutic drug monitoring, toxicology)
- Biomarker validation

### Agilent 1260 Infinity HPLC System

**Configuration Options:**
- **Binary LC System** - 2-solvent gradients, up to 600 bar
- **Quaternary LC System** - 4-solvent gradients, up to 600 bar

**Typical Module Stack:**

1. **Pump Module**
   - **Binary**: G7112B Infinity II Binary Pump
   - **Quaternary**: G1311C Quaternary Pump
   - Integrated degasser and automatic purge valve
   - Pressure range: Up to 600 bar (8,700 psi)

2. **Autosampler**
   - **Multisampler**: G7167A (variable injection volume, up to 96 vials + 8 plates)
   - **Vialsampler**: G7129A (simple vial tray configuration)
   - Temperature control: 4-40°C
   - Injection volume: 0.1-100 µL

3. **Column Thermostat**
   - **Multicolumn Thermostat**: G7116A (accommodates up to 4 columns)
   - Temperature range: 5°C below ambient to 99°C
   - Temperature stability: ±0.1°C

4. **Solvent Module**
   - Degasser: G1379B (removes dissolved gases, reduces baseline noise)
   - Solvent selection valve (for quaternary systems)

5. **Optional Detectors** (pre-MS detection)
   - **Diode Array Detector (DAD)**: G7115A (UV-Vis spectral data)
   - **Variable Wavelength Detector (VWD)**: G7114A (single wavelength)
   - **Fluorescence Detector (FLD)**: G7121A (high sensitivity for fluorescent compounds)

**Stack Design:**
- All modules stackable with consistent leak plane outlets
- Compatible with Infinity, Infinity II, and Infinity III modules
- Shared CAN bus communication between modules

---

## MassHunter Workstation Software

### Software Components

**1. MassHunter Acquisition (Data Acquisition)**
- Controls LC and MS hardware
- Runs sample sequences and worklists
- Real-time monitoring and diagnostics
- Auto-tuning and calibration

**2. MassHunter Quantitative Analysis (Quant)**
- Quantitative analysis of MRM data
- Calibration curve generation
- Batch processing
- Report generation

**3. MassHunter Qualitative Analysis (Qual)**
- Unknown identification
- Compound library searching
- Spectral deconvolution
- Formula generation

### Data Storage Architecture

**Primary Data Format**: `.d` folder (proprietary Agilent format)

**`.d` Folder Structure:**
```
Sample_Name.d/
├── AcqData/
│   ├── MSScan.bin      # Raw MS scan data (binary)
│   ├── MSPeak.bin      # Detected peaks (binary)
│   ├── MSTS.xml        # Time segment information
│   └── Contents/
│       └── qualitative.cdb  # Database file
├── AcqMethod.xml       # Acquisition method parameters
├── Worklist.wkl        # Associated worklist
├── sample.xml          # Sample metadata
├── Results/
│   └── *.csv           # Exported results (if configured)
└── Reports/
    └── *.pdf           # Generated reports
```

**Key Files:**
- **MSScan.bin**: Binary file containing raw mass spectrometry data
- **MSPeak.bin**: Detected peak information (m/z, intensity, RT)
- **AcqMethod.xml**: All acquisition parameters (MS source, MRM transitions, LC gradient)
- **sample.xml**: Sample metadata (name, type, position, injection volume, etc.)

### Data Export Capabilities

**Built-in Export Formats:**
- **CSV** - Tabular data (peak areas, concentrations, retention times)
- **XML** - Structured data with metadata
- **PDF** - Formatted reports with chromatograms and results
- **TXT** - Simple text format

**Export Configuration:**
- **Automatic Export After Acquisition**: Check "Tabulate Chart after Sample Acquisition" in Data Options
- **Manual Export**: Right-click chromatogram/spectrum → Export → Select format
- **Batch Export**: MassHunter Quant can export entire batches to CSV

**Third-Party Conversion:**
- **ProteoWizard MSConvert**: Convert `.d` to mzXML, mzML, MGF formats
- **R Package (MassHunteR)**: Read `.d` files directly in R for custom processing

---

## Integration Architecture Options

### Option 1: File-Based Integration (Recommended for Initial Implementation)

**Approach**: Network folder monitoring with CSV/XML export

**Workflow:**

1. **LIMS → Instrument (Worklist Generation)**
   ```
   Felicity LIMS
      ↓ Generate Worklist CSV
   Shared Network Folder (/instrument_input/6460/)
      ↓ Operator imports to MassHunter
   MassHunter Acquisition
      ↓ Run Sequence
   Data Acquisition Complete
   ```

2. **Instrument → LIMS (Result Import)**
   ```
   MassHunter Quantitative Analysis
      ↓ Export Results CSV
   Shared Network Folder (/instrument_output/6460/)
      ↓ File Polling Service (every 30 seconds)
   Felicity LIMS Parser
      ↓ Parse and Validate Results
   Import to Database
      ↓ Link to Patient/Sample
   Results Available for Review
   ```

**Worklist CSV Format (Example):**
```csv
Sample Name,Sample ID,Position,Inj Vol,Data File,Acq Method,Sample Type,Level
QC_Low,QC-001,P1-A1,10,QC_Low_001.d,TDM_Method.m,QC,1
Patient_12345,PAT-12345,P1-A2,10,Patient_12345.d,TDM_Method.m,Sample,0
Calibrator_Level1,CAL-L1,P1-A3,10,Cal_L1_001.d,TDM_Method.m,Calibrator,1
Calibrator_Level2,CAL-L2,P1-A4,10,Cal_L2_001.d,TDM_Method.m,Calibrator,2
Patient_12346,PAT-12346,P1-A5,10,Patient_12346.d,TDM_Method.m,Sample,0
Blank,BLANK-001,P1-A6,10,Blank_001.d,TDM_Method.m,Blank,0
```

**Results CSV Format (MassHunter Quant Export):**
```csv
Sample Name,Compound,RT,Area,Height,Concentration,Units,IS Area,Response Ratio,Accuracy
Patient_12345,Ibuprofen,4.23,125678,45890,15.3,µg/mL,456789,0.275,98.5
Patient_12345,Naproxen,5.67,89456,23456,8.7,µg/mL,456789,0.196,102.1
QC_Low,Ibuprofen,4.24,65432,23456,8.2,µg/mL,456789,0.143,101.2
```

**Advantages:**
- ✅ Simple implementation, no API dependencies
- ✅ Works with existing MassHunter software (no modifications needed)
- ✅ Reliable, well-tested approach in many labs
- ✅ Easy debugging (inspect CSV files manually)
- ✅ No direct database access to instrument PC

**Disadvantages:**
- ❌ Manual import step by operator (worklist to MassHunter)
- ❌ Polling latency (30-60 second delay)
- ❌ File locking issues if timing is poor
- ❌ No real-time status updates

**Implementation Requirements:**
- **Shared Network Folder**: Instrument PC must have read/write access
- **File Polling Service**: Felicity LIMS background task monitoring output folder
- **CSV Parser**: Python service to parse MassHunter export format
- **Error Handling**: Detect malformed files, missing data, duplicate imports

---

### Option 2: MassHunter SDK/API Integration (Advanced)

**Approach**: Direct programmatic control via C# or Python SDK

**MassHunter SDK Capabilities:**
- Create and modify worklists programmatically
- Start/stop acquisitions remotely
- Monitor acquisition status in real-time
- Extract results from `.d` folders using SDK methods
- Control method parameters

**Workflow:**

1. **LIMS → Instrument (Automated Worklist Injection)**
   ```python
   from masshunter_sdk import Acquisition

   # Connect to MassHunter Acquisition
   acq = Acquisition(host='instrument-pc.lab.local')

   # Create worklist from LIMS data
   worklist = acq.create_worklist()
   for sample in lims_samples:
       worklist.add_sample(
           name=sample['sample_name'],
           position=sample['position'],
           data_file=f"{sample['sample_name']}.d",
           method=sample['method_file'],
           sample_type=sample['type']
       )

   # Start sequence
   acq.start_sequence(worklist)
   ```

2. **Real-time Status Monitoring**
   ```python
   # Poll acquisition status
   while acq.is_running():
       status = acq.get_status()
       # Update LIMS with progress
       lims.update_sample_status(
           sample_uid=status.current_sample,
           status="acquiring",
           progress=status.percent_complete
       )
       time.sleep(30)
   ```

3. **Result Extraction**
   ```python
   from masshunter_sdk import QuantAnalysis

   # Load data file
   quant = QuantAnalysis()
   results = quant.load_results("Patient_12345.d")

   # Extract compound results
   for compound in results.compounds:
       lims.create_analysis_result(
           sample_uid=sample_uid,
           analyte=compound.name,
           result=compound.concentration,
           units=compound.units,
           retention_time=compound.rt
       )
   ```

**Advantages:**
- ✅ Fully automated bidirectional communication
- ✅ Real-time status updates
- ✅ No manual operator intervention
- ✅ Direct data extraction (no CSV parsing)
- ✅ Method validation and error checking

**Disadvantages:**
- ❌ Requires MassHunter SDK license from Agilent
- ❌ SDK documentation limited (contact Agilent support)
- ❌ Complex implementation (C# or Python expertise required)
- ❌ Potential compatibility issues with MassHunter updates
- ❌ Instrument PC security concerns (API access)

**Implementation Requirements:**
- **MassHunter SDK**: Obtain from Agilent (may require support contract)
- **API Server**: Flask/FastAPI service on instrument PC or middleware server
- **Authentication**: Secure API keys for LIMS ↔ Instrument communication
- **Error Recovery**: Handle instrument offline, method missing, etc.

---

### Option 3: Database Polling (Hybrid Approach)

**Approach**: LIMS polls MassHunter database for completed acquisitions

**MassHunter Database:**
- MassHunter stores acquisition metadata in SQL Server or SQLite database
- Database location: `C:\MassHunter\Data\database\` (typical)
- Contains sample info, run status, timestamps, file paths

**Workflow:**

1. **Worklist**: Use CSV export (Option 1)
2. **Status Monitoring**: Poll MassHunter database for completion status
3. **Result Import**: Automatically trigger CSV import when `status = 'Complete'`

**SQL Query Example:**
```sql
SELECT
    sample_name,
    data_file_path,
    acquisition_status,
    completion_timestamp,
    method_name
FROM acquisitions
WHERE
    completion_timestamp > @last_poll_time
    AND acquisition_status = 'Complete'
ORDER BY completion_timestamp ASC
```

**Advantages:**
- ✅ Near real-time status updates
- ✅ No SDK required
- ✅ Automated result import trigger
- ✅ Leverages existing database

**Disadvantages:**
- ❌ Direct database access (could void warranty)
- ❌ Schema changes between MassHunter versions
- ❌ No official documentation for database structure
- ❌ Read-only access only (no worklist injection)

---

### Option 4: ChemStation XML Connectivity (If Applicable)

**Applicability**: Only for OpenLab ChemStation Edition, **NOT** OpenLab CDS 2.x

**ChemStation XML Features:**
- XML import of sample data into sequence table
- XML export of results for LIMS consumption
- LIMS-specific columns: `LimsID`, `LimsKField2`, `LimsKField3`

**XML Worklist Schema:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Worklist>
  <WorklistInfo>
    <Name>TDM_Batch_20251027</Name>
    <CreatedDate>2025-10-27T14:30:00</CreatedDate>
  </WorklistInfo>
  <Samples>
    <Sample>
      <SampleName>Patient_12345</SampleName>
      <SampleID>PAT-12345</SampleID>
      <Position>P1-A2</Position>
      <InjVolume>10</InjVolume>
      <DataFile>Patient_12345.d</DataFile>
      <MethodFile>TDM_Method.m</MethodFile>
      <SampleType>Sample</SampleType>
      <LimsID>5a8f9c3e-d2b1-4e7a-8c9d-1f2e3d4c5b6a</LimsID>
      <LimsKField2>Patient Medical History Link</LimsKField2>
    </Sample>
  </Samples>
</Worklist>
```

**XML Results Export:**
- Configured via `Chemstation.ini`
- Parallel output (acquisition + XML export)
- Contains all sequence table data plus custom fields

**Limitation**:
- ⚠️ **OpenLab CDS 2.x does NOT support XML connectivity**
- Must use ChemStation Edition or revert to CSV-based integration

---

## Recommended Integration Strategy for Felicity LIMS

### Phase 1: File-Based Integration (MVP - 2-4 weeks)

**Implementation Steps:**

1. **Create Instrument Driver Module** (`felicity/apps/instrument/drivers/agilent_6460.py`)
   ```python
   class Agilent6460Driver(BaseInstrumentDriver):
       """
       Agilent 6460 Triple Quad LC/MS driver using file-based integration.
       """

       def generate_worklist_csv(self, samples: List[Sample]) -> str:
           """Generate CSV worklist for MassHunter import."""
           pass

       def parse_results_csv(self, file_path: str) -> List[AnalysisResult]:
           """Parse MassHunter Quant export CSV."""
           pass

       def validate_worklist(self, samples: List[Sample]) -> ValidationResult:
           """Validate samples before worklist generation."""
           pass
   ```

2. **File Polling Service** (`felicity/apps/instrument/services/file_poller.py`)
   ```python
   class InstrumentFilePoller:
       """
       Background service monitoring instrument output folders.
       """

       async def poll_folder(self, folder_path: str, interval: int = 30):
           """Monitor folder for new result files."""
           pass

       async def process_result_file(self, file_path: str):
           """Parse and import results to LIMS."""
           pass
   ```

3. **GraphQL API Extensions**
   ```graphql
   type Mutation {
       generateInstrumentWorklist(
           instrumentUid: String!,
           sampleUids: [String!]!,
           methodName: String
       ): WorklistFile!

       importInstrumentResults(
           instrumentUid: String!,
           resultFileUid: String!
       ): ImportSummary!
   }

   type Query {
       instrumentStatus(instrumentUid: String!): InstrumentStatus!
       pendingResultFiles(instrumentUid: String!): [ResultFile!]!
   }
   ```

4. **Frontend Worklist Generator UI**
   - Sample selection interface
   - Position assignment (plate/vial mapping)
   - QC sample insertion
   - Method selection
   - Calibrator sequence configuration
   - Download worklist CSV button

5. **Result Import UI**
   - Pending files dashboard
   - One-click import with preview
   - Conflict resolution (duplicate results)
   - Batch approval workflow

**Network Configuration:**
```yaml
network_shares:
  agilent_6460_input:
    path: "//instrument-pc/lims_input"
    access: "read_write"
    protocol: "SMB"

  agilent_6460_output:
    path: "//instrument-pc/lims_output"
    access: "read_only"
    protocol: "SMB"
    polling_interval: 30  # seconds
```

---

### Phase 2: Enhanced Integration (3-6 months)

**Advanced Features:**

1. **Patient Medical History Integration**
   - Display relevant medications during result review
   - Flag drug interactions
   - Show chronic conditions for clinical context
   - Link diagnoses to test results

2. **Intelligent QC Management**
   - Automatic QC sample insertion (every N samples)
   - Levey-Jennings charts
   - Westgard rules violation alerts
   - Calibration curve tracking

3. **Method Management**
   - Store MassHunter method files in LIMS
   - Version control for methods
   - Method validation tracking
   - Link methods to analysis types

4. **Instrument Performance Monitoring**
   - Track sensitivity over time (IS response)
   - Monitor system suitability metrics
   - Predictive maintenance alerts
   - Uptime/downtime analytics

5. **Electronic Lab Notebook Integration**
   - Embed chromatograms in sample reports
   - Annotate peaks with clinical notes
   - Store raw `.d` files for archival
   - Generate audit-ready reports

---

### Phase 3: Full Automation (Optional, 6-12 months)

**MassHunter SDK Integration:**

1. **Bidirectional API Communication**
   - Automatic worklist injection
   - Real-time acquisition monitoring
   - Remote method selection
   - Instrument status dashboard

2. **Advanced Scheduling**
   - Batch sample prioritization
   - STAT sample interruption
   - Multi-instrument load balancing
   - Predictive run time estimation

3. **Result Verification Automation**
   - Automatic integration review
   - Peak purity assessment
   - Ion ratio validation
   - Auto-approval for routine samples

---

## Data Structures and Schemas

### Instrument Configuration

```python
# felicity/apps/instrument/entities.py

class InstrumentType(BaseEntity):
    __tablename__ = "instrument_type"

    name = Column(String, nullable=False, unique=True)  # "LC/MS/MS"
    category = Column(String, nullable=False)  # "Mass Spectrometry"
    manufacturer = Column(String, nullable=False)  # "Agilent"

class Instrument(LabScopedEntity):
    __tablename__ = "instrument"

    name = Column(String, nullable=False)  # "Agilent 6460 #1"
    instrument_type_uid = Column(String, ForeignKey("instrument_type.uid"))
    instrument_type = relationship("InstrumentType")

    # Agilent 6460 Specific
    model = Column(String)  # "G6460C"
    serial_number = Column(String, unique=True)

    # Software
    software_name = Column(String)  # "MassHunter"
    software_version = Column(String)  # "10.1"

    # Communication
    driver_module = Column(String)  # "agilent_6460"
    communication_method = Column(String)  # "file_share"
    connection_config = Column(JSONB)  # Network paths, credentials

    # Status
    is_active = Column(Boolean, default=True)
    is_online = Column(Boolean, default=False)
    last_communication = Column(DateTime)

    # Maintenance
    last_calibration_date = Column(Date)
    next_maintenance_date = Column(Date)
    preventive_maintenance_interval = Column(Integer)  # days
```

### Worklist Management

```python
class InstrumentWorklist(LabScopedEntity):
    __tablename__ = "instrument_worklist"

    instrument_uid = Column(String, ForeignKey("instrument.uid"))
    instrument = relationship("Instrument")

    worklist_name = Column(String, nullable=False)
    method_name = Column(String)

    # File Management
    csv_file_path = Column(String)  # Path to generated CSV
    csv_file_content = Column(Text)  # Store CSV content

    # Status
    status = Column(String)  # draft, exported, imported, running, complete
    generated_at = Column(DateTime)
    downloaded_at = Column(DateTime)
    imported_to_instrument_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Samples
    sample_count = Column(Integer)
    qc_count = Column(Integer)
    calibrator_count = Column(Integer)
    blank_count = Column(Integer)

class WorklistSample(LabScopedEntity):
    __tablename__ = "worklist_sample"

    worklist_uid = Column(String, ForeignKey("instrument_worklist.uid"))
    worklist = relationship("InstrumentWorklist")

    sample_uid = Column(String, ForeignKey("sample.uid"))
    sample = relationship("Sample")

    # Position
    sequence_number = Column(Integer)  # Order in worklist
    plate_position = Column(String)  # "P1-A2"
    vial_position = Column(String)  # "Rack 1, Position 15"

    # Acquisition Parameters
    injection_volume = Column(Numeric(10, 2))  # µL
    data_file_name = Column(String)  # "Patient_12345.d"
    method_file = Column(String)  # "TDM_Method.m"
    sample_type = Column(String)  # Sample, QC, Calibrator, Blank
    calibrator_level = Column(Integer)  # For calibrators

    # Status
    acquisition_status = Column(String)  # pending, running, complete, error
    acquisition_started_at = Column(DateTime)
    acquisition_completed_at = Column(DateTime)

    # Results
    result_file_imported = Column(Boolean, default=False)
    result_import_timestamp = Column(DateTime)
```

### Result Import Management

```python
class InstrumentResultFile(LabScopedEntity):
    __tablename__ = "instrument_result_file"

    instrument_uid = Column(String, ForeignKey("instrument.uid"))
    instrument = relationship("Instrument")

    worklist_uid = Column(String, ForeignKey("instrument_worklist.uid"))
    worklist = relationship("InstrumentWorklist")

    # File Info
    file_name = Column(String, nullable=False)
    file_path = Column(String)
    file_size = Column(BigInteger)  # bytes
    file_hash = Column(String)  # SHA256 for duplicate detection

    detected_at = Column(DateTime)

    # Import Status
    import_status = Column(String)  # pending, processing, complete, error
    imported_at = Column(DateTime)
    import_error = Column(Text)

    # Statistics
    total_results = Column(Integer)
    imported_results = Column(Integer)
    failed_results = Column(Integer)
    duplicate_results = Column(Integer)

class InstrumentAnalysisResult(LabScopedEntity):
    __tablename__ = "instrument_analysis_result"

    result_file_uid = Column(String, ForeignKey("instrument_result_file.uid"))
    result_file = relationship("InstrumentResultFile")

    sample_uid = Column(String, ForeignKey("sample.uid"))
    sample = relationship("Sample")

    analysis_uid = Column(String, ForeignKey("analysis.uid"))
    analysis = relationship("Analysis")

    # Raw Instrument Data
    compound_name = Column(String)
    retention_time = Column(Numeric(10, 4))  # minutes
    peak_area = Column(Numeric(20, 2))
    peak_height = Column(Numeric(20, 2))

    # Quantitation
    concentration = Column(Numeric(20, 4))
    concentration_units = Column(String)

    # Quality Metrics
    internal_standard_area = Column(Numeric(20, 2))
    response_ratio = Column(Numeric(10, 6))
    accuracy_percent = Column(Numeric(10, 2))
    signal_to_noise = Column(Numeric(10, 2))

    # Integration Quality
    integration_quality = Column(String)  # good, acceptable, poor
    integration_flags = Column(JSONB)  # ["baseline_drift", "peak_split"]

    # Review Status
    review_status = Column(String)  # pending, approved, rejected
    reviewed_by_uid = Column(String, ForeignKey("user.uid"))
    reviewed_at = Column(DateTime)
    review_notes = Column(Text)
```

---

## Quality Control Integration

### Calibration Curve Management

```python
class CalibrationCurve(LabScopedEntity):
    __tablename__ = "calibration_curve"

    instrument_uid = Column(String, ForeignKey("instrument.uid"))
    instrument = relationship("Instrument")

    analysis_uid = Column(String, ForeignKey("analysis.uid"))
    analysis = relationship("Analysis")

    worklist_uid = Column(String, ForeignKey("instrument_worklist.uid"))
    worklist = relationship("InstrumentWorklist")

    # Curve Parameters
    curve_type = Column(String)  # linear, quadratic, cubic, weighted
    weighting_factor = Column(String)  # 1/x, 1/x^2, none

    slope = Column(Numeric(20, 10))
    intercept = Column(Numeric(20, 10))
    r_squared = Column(Numeric(10, 8))

    # Calibrator Levels
    calibrator_count = Column(Integer)
    level_concentrations = Column(JSONB)  # [0.5, 1.0, 5.0, 10.0, 50.0]

    # Validity
    is_valid = Column(Boolean)
    valid_from = Column(DateTime)
    valid_until = Column(DateTime)
    expiration_reason = Column(String)  # expired, qc_failure, instrument_maintenance

class CalibrationPoint(LabScopedEntity):
    __tablename__ = "calibration_point"

    curve_uid = Column(String, ForeignKey("calibration_curve.uid"))
    curve = relationship("CalibrationCurve")

    level = Column(Integer)
    expected_concentration = Column(Numeric(20, 4))
    measured_concentration = Column(Numeric(20, 4))

    peak_area = Column(Numeric(20, 2))
    is_area = Column(Numeric(20, 2))  # Internal Standard area
    response_ratio = Column(Numeric(10, 6))

    accuracy_percent = Column(Numeric(10, 2))
    is_outlier = Column(Boolean, default=False)

    replicate_number = Column(Integer)
```

### QC Sample Tracking

```python
class QCMaterial(LabScopedEntity):
    __tablename__ = "qc_material"

    name = Column(String, nullable=False)
    lot_number = Column(String, nullable=False)

    manufacturer = Column(String)
    catalog_number = Column(String)

    # Concentration Targets
    analyte_targets = Column(JSONB)
    # {
    #   "Ibuprofen": {"target": 15.0, "units": "µg/mL", "lower": 13.5, "upper": 16.5},
    #   "Naproxen": {"target": 10.0, "units": "µg/mL", "lower": 9.0, "upper": 11.0}
    # }

    # Validity
    received_date = Column(Date)
    expiration_date = Column(Date)
    opened_date = Column(Date)
    stability_after_open = Column(Integer)  # days

    is_active = Column(Boolean, default=True)

class QCResult(LabScopedEntity):
    __tablename__ = "qc_result"

    qc_material_uid = Column(String, ForeignKey("qc_material.uid"))
    qc_material = relationship("QCMaterial")

    instrument_uid = Column(String, ForeignKey("instrument.uid"))
    instrument = relationship("Instrument")

    worklist_uid = Column(String, ForeignKey("instrument_worklist.uid"))
    worklist = relationship("InstrumentWorklist")

    analysis_uid = Column(String, ForeignKey("analysis.uid"))
    analysis = relationship("Analysis")

    # Result
    measured_value = Column(Numeric(20, 4))
    target_value = Column(Numeric(20, 4))
    lower_limit = Column(Numeric(20, 4))
    upper_limit = Column(Numeric(20, 4))
    units = Column(String)

    # QC Status
    is_in_range = Column(Boolean)
    deviation_percent = Column(Numeric(10, 2))

    # Westgard Rules
    westgard_violations = Column(JSONB)  # ["1_3s", "2_2s"]
    requires_corrective_action = Column(Boolean, default=False)

    run_date = Column(DateTime)
```

---

## Frontend UI Components

### 1. Instrument Dashboard

**Features:**
- Real-time instrument status (online/offline)
- Current worklist progress
- Recent results summary
- Pending files for import
- QC status indicators
- Maintenance alerts

**UI Elements:**
```vue
<InstrumentDashboard>
  <InstrumentCard
    name="Agilent 6460 #1"
    status="running"
    current-sample="Patient_12345"
    progress="45%"
    samples-remaining="23"
  />

  <QCStatusCard
    last-qc-pass="2 hours ago"
    next-qc-due="In 4 samples"
    violations="None"
  />

  <PendingResultsCard
    pending-files="3"
    oldest-file="15 minutes ago"
  />
</InstrumentDashboard>
```

### 2. Worklist Generator

**Features:**
- Drag-and-drop sample selection
- Plate/vial position assignment
- QC sample auto-insertion
- Calibrator sequence configuration
- Method selection dropdown
- Worklist preview
- Export CSV button

**UI Flow:**
```
1. Select Samples
   └─> Filter by: Patient, Sample Type, Collection Date, Status

2. Configure Worklist
   ├─> Add QC samples (every N samples)
   ├─> Add calibrators (beginning, end, both)
   ├─> Add blanks
   └─> Assign positions (auto or manual)

3. Select Method
   └─> Dropdown of available MassHunter methods

4. Preview Worklist
   └─> Table view with all samples, positions, parameters

5. Generate & Download
   └─> CSV file ready for MassHunter import
```

### 3. Result Import Interface

**Features:**
- Pending files table with timestamps
- One-click import with validation
- Preview results before import
- Conflict resolution (duplicate results)
- Link results to patient medical history
- Batch approval workflow

**UI Flow:**
```
1. View Pending Files
   └─> Table: Filename, Size, Detected, Samples, Status

2. Preview Results
   ├─> Parse CSV
   ├─> Match samples to LIMS records
   ├─> Highlight conflicts (duplicates, missing samples)
   └─> Show patient medical context (medications, diagnoses)

3. Resolve Conflicts
   ├─> Choose which result to keep (duplicate handling)
   ├─> Create new samples for unmatched results
   └─> Skip invalid results

4. Import Results
   └─> Bulk insert to database with audit trail

5. Review Results
   ├─> Display chromatogram thumbnails
   ├─> Show QC status
   ├─> Flag out-of-range results
   └─> Approve or reject batch
```

### 4. Result Review with Patient Context

**Features:**
- Split-pane view: Results + Patient History
- Medication interference alerts
- Chronic condition context
- Reference range adjustment based on patient data
- Clinical interpretation suggestions
- Electronic signature for approval

**UI Layout:**
```
┌─────────────────────────────────────────────────────────┐
│ Sample: Patient_12345 | Analysis: TDM Panel             │
├──────────────────────────────┬──────────────────────────┤
│ RESULTS                      │ PATIENT CONTEXT          │
│                              │                          │
│ Compound      Conc.   Range  │ Active Medications:      │
│ Ibuprofen     15.3    10-20  │ • Metformin (drug inter.)│
│ Naproxen       8.7     5-15  │ • Lisinopril             │
│                              │                          │
│ [Chromatogram Preview]       │ Chronic Conditions:      │
│                              │ • Type 2 Diabetes        │
│ Integration: Good ✓          │ • Hypertension           │
│ QC Status: Pass ✓            │                          │
│                              │ Recent Diagnoses:        │
│ [Approve] [Reject] [Flag]    │ • Elevated BP (E11.9)    │
│                              │                          │
│                              │ Insurance: Active ✓      │
└──────────────────────────────┴──────────────────────────┘
```

---

## Implementation Checklist

### Phase 1: File-Based Integration (4-6 weeks)

**Week 1-2: Backend Development**
- [ ] Create `InstrumentType`, `Instrument`, `InstrumentWorklist` entities
- [ ] Create repositories and services for instrument management
- [ ] Implement Agilent 6460 driver with CSV generation
- [ ] Implement CSV parser for MassHunter Quant export
- [ ] Create file polling background service
- [ ] Add GraphQL mutations for worklist generation
- [ ] Add GraphQL queries for instrument status

**Week 3-4: Frontend Development**
- [ ] Create instrument dashboard page
- [ ] Create worklist generator UI
- [ ] Implement sample selection and position assignment
- [ ] Create CSV download functionality
- [ ] Create result import interface
- [ ] Implement conflict resolution UI
- [ ] Create result review page with patient context

**Week 5-6: Testing & Deployment**
- [ ] Unit tests for CSV generation and parsing
- [ ] Integration tests for file polling service
- [ ] End-to-end test with real instrument (if available)
- [ ] User acceptance testing with lab staff
- [ ] Documentation (user manual, SOPs)
- [ ] Deploy to production
- [ ] Training for laboratory operators

### Phase 2: Enhanced Features (2-3 months)

- [ ] Patient medical history integration in result review
- [ ] QC material and QC result management
- [ ] Calibration curve tracking with Levey-Jennings charts
- [ ] Westgard rules implementation
- [ ] Method management and versioning
- [ ] Instrument performance monitoring dashboards
- [ ] Predictive maintenance alerts
- [ ] Enhanced reporting with embedded chromatograms

### Phase 3: SDK Integration (Optional, 3-6 months)

- [ ] Obtain MassHunter SDK from Agilent
- [ ] Implement C# or Python wrapper for SDK
- [ ] Create API server for bidirectional communication
- [ ] Implement automatic worklist injection
- [ ] Implement real-time status monitoring
- [ ] Add remote method selection
- [ ] Add acquisition control (start/stop/pause)
- [ ] Advanced scheduling and load balancing

---

## Network and Security Configuration

### Network Architecture

```
┌────────────────────────────────────────────────────────────┐
│ Laboratory Network                                         │
│                                                            │
│  ┌──────────────────┐                                     │
│  │ Felicity LIMS    │                                     │
│  │ Server           │                                     │
│  │                  │                                     │
│  │ File Polling     │◄────┐                              │
│  │ Service          │      │                              │
│  └──────────────────┘      │                              │
│                            │                              │
│  ┌──────────────────┐     │   ┌──────────────────┐      │
│  │ Shared NAS/SMB   │◄────┼───┤ Agilent 6460 PC  │      │
│  │ Storage          │     │   │                  │      │
│  │                  │     │   │ MassHunter       │      │
│  │ /lims_input/     │     └───┤ Workstation      │      │
│  │ /lims_output/    │         │                  │      │
│  └──────────────────┘         │ (Windows 10/11)  │      │
│                                └──────────────────┘      │
│                                         │                 │
│                                         │                 │
│                                ┌────────▼────────┐        │
│                                │ Agilent 6460    │        │
│                                │ Instrument      │        │
│                                │ (Ethernet/USB)  │        │
│                                └─────────────────┘        │
└────────────────────────────────────────────────────────────┘
```

### Firewall Rules

**LIMS Server → Instrument PC:**
- SMB (Port 445): File share access
- SSH (Port 22): Remote management (optional)

**Instrument PC → LIMS Server:**
- HTTPS (Port 443): API calls (if SDK integration)
- PostgreSQL (Port 5432): Database polling (if hybrid approach)

### Security Best Practices

1. **File Share Permissions**
   - LIMS service account: Read/Write on both input and output folders
   - Instrument PC: Read-only on input, Read/Write on output
   - No anonymous access

2. **Network Isolation**
   - Instrument network on separate VLAN
   - Firewall rules limiting instrument PC to essential traffic
   - No direct internet access from instrument PC

3. **Audit Trail**
   - Log all file operations (create, read, delete)
   - Track user who generated worklist
   - Record timestamp of result import
   - Maintain file hash for integrity verification

4. **Data Retention**
   - Archive `.d` files to long-term storage (MinIO/S3)
   - Keep CSV files for at least 90 days
   - Retain QC results for 5+ years (regulatory requirement)

---

## Troubleshooting Guide

### Common Issues

**Issue**: Worklist CSV not imported to MassHunter
- **Cause**: Incorrect CSV format or encoding
- **Solution**: Verify column headers match MassHunter requirements, use UTF-8 encoding

**Issue**: Result file not detected by LIMS
- **Cause**: File still locked by MassHunter, polling service not running
- **Solution**: Ensure MassHunter exports to output folder after processing complete, restart polling service

**Issue**: Sample mismatch during import
- **Cause**: Sample name in CSV doesn't match LIMS database
- **Solution**: Implement fuzzy matching, allow manual sample linking in UI

**Issue**: Duplicate results imported
- **Cause**: Same result file processed multiple times
- **Solution**: Check file hash before import, mark files as "processed" in database

**Issue**: Instrument status always shows "offline"
- **Cause**: No recent result files, file polling service error
- **Solution**: Check network connectivity, verify folder permissions, review service logs

---

## References and Resources

### Agilent Documentation
- **6460 Triple Quad User Manual**: G3335-90135_QQQ_Concepts.pdf
- **1260 Infinity II System Guide**: G7111ASystem.pdf
- **MassHunter Workstation Guide**: Available on USB media with software
- **ChemStation XML Connectivity Guide**: G2070-91126_Understanding.pdf

### Integration Resources
- **ProteoWizard**: https://proteowizard.sourceforge.io/ (Convert `.d` files)
- **MassHunteR R Package**: https://github.com/burlab/MasshunteR
- **SiLA 2 Standard**: https://sila-standard.com/ (Laboratory automation protocol)

### Regulatory Compliance
- **FDA 21 CFR Part 11**: Electronic records and signatures
- **CLIA**: Clinical Laboratory Improvement Amendments
- **CAP**: College of American Pathologists accreditation requirements

---

## Next Steps

1. **Review this document** with laboratory staff and IT team
2. **Confirm network architecture** and file share setup
3. **Obtain sample MassHunter export files** for parser development
4. **Begin Phase 1 implementation** with file-based integration
5. **Schedule pilot testing** with small batch of samples
6. **Develop training materials** for laboratory operators
7. **Plan go-live date** with phased rollout strategy

---

**Document Status**: Draft for Implementation
**Last Updated**: 2025-10-27
**Owner**: Mohammad Aijaz
**Project**: Felicity LIMS - Agilent 6460 Integration
**Version**: 1.0
