# Agilent MassHunter Integration Plan - Space City Labs

**Date**: 2025-10-27
**Status**: Design Phase
**Priority**: 🔥 HIGHEST
**Timeline**: 1-2 weeks

---

## Current Situation

**Instrument**: Agilent LCMS with MassHunter Quantitative Analysis software
**Current Workflow**: Manual - Results exported to Word/Excel for report generation
**Pain Points**:
- Manual data entry prone to errors
- Time-consuming report generation
- No automated QC checks
- Limited data traceability
- Difficult to track sample status

---

## Proposed Solution: Automated File-Based Integration

### Overview
```
┌──────────────────────────────────────────────────────────────┐
│  MassHunter Quantitative Analysis                            │
│  - Run samples                                               │
│  - Generate batch table                                      │
│  - Export to CSV/Excel                                       │
└────────────────┬─────────────────────────────────────────────┘
                 │ (Automated Export)
                 ↓
┌────────────────▼─────────────────────────────────────────────┐
│  Shared Network Location / Export Folder                     │
│  - C:\MassHunterData\Exports\                               │
│  - Files: BatchResults_YYYYMMDD_HHMMSS.csv                  │
└────────────────┬─────────────────────────────────────────────┘
                 │ (File Monitor - every 60 seconds)
                 ↓
┌────────────────▼─────────────────────────────────────────────┐
│  Felicity LIMS - MassHunter Integration Service             │
│  - Detect new export files                                   │
│  - Parse CSV/Excel                                           │
│  - Validate data                                             │
│  - Match to existing samples                                 │
└────────────────┬─────────────────────────────────────────────┘
                 │ (Import Results)
                 ↓
┌────────────────▼─────────────────────────────────────────────┐
│  Felicity LIMS Database                                      │
│  - Sample results imported                                   │
│  - QC flags applied                                          │
│  - Reports auto-generated                                    │
│  - Ready for review and approval                             │
└──────────────────────────────────────────────────────────────┘
```

---

## MassHunter Export Configuration

### Step 1: Configure Batch Table Columns

**Recommended Columns to Include**:
```
Sample Information (Left Side):
- Sample Name (REQUIRED)
- Sample Type (e.g., Unknown, Standard, QC, Blank)
- Acquisition Date/Time
- Rack Number
- Vial Position
- Dilution Factor
- Sample Comment

Compound Information (Right Side):
- Compound Name (REQUIRED)
- Calculated Concentration (REQUIRED)
- Conc. Units (REQUIRED)
- Accuracy (%)
- Response
- Expected RT
- RT (Retention Time - actual)
- Area
- Height
- Signal/Noise
- ISTD Response
- Qualifier Ion Ratio (%)
- Quantifier Ion (m/z)
```

**Columns to REMOVE Before Export** (These cause Excel formatting issues):
- ❌ Quantitation Message Summary
- ❌ Outlier Summary

### Step 2: Export Process

**Method 1: Manual Export (Current)**
1. Complete batch analysis in MassHunter
2. Go to **File → Export**
3. Select format: **CSV** or **XLSX**
4. Choose destination: `C:\MassHunterData\Exports\`
5. Filename pattern: `BatchResults_{date}_{time}.csv`

**Method 2: Automated Export (Recommended)** ⭐
MassHunter can be configured to auto-export batch results:
1. Set up post-acquisition script
2. Configure export template with required columns
3. Auto-save to monitored folder
4. Felicity picks up automatically

---

## Sample CSV Export Format

### Example MassHunter Batch Export CSV:
```csv
Sample Name,Sample Type,Acq. Date-Time,Compound,Calc. Conc.,Conc. Units,Accuracy,RT,Area,Height,S/N,Dilution
SCL-001,Unknown,2025-10-27 10:15:23,Caffeine,125.5,ng/mL,98.5,3.45,1234567,98765,150.2,1
SCL-001,Unknown,2025-10-27 10:15:23,Theophylline,85.2,ng/mL,102.1,4.12,987654,76543,120.5,1
SCL-002,Unknown,2025-10-27 10:28:45,Caffeine,245.8,ng/mL,95.2,3.46,2456789,187654,178.9,1
SCL-002,Unknown,2025-10-27 10:28:45,Theophylline,165.4,ng/mL,99.8,4.13,1897456,145678,145.2,1
QC-HIGH,QC Control,2025-10-27 10:42:12,Caffeine,500.0,ng/mL,101.2,3.45,5123456,398765,210.5,1
QC-HIGH,QC Control,2025-10-27 10:42:12,Theophylline,400.0,ng/mL,98.9,4.12,4098765,298543,195.8,1
```

### Key Fields Mapping:
| MassHunter Column | Felicity Field | Required | Notes |
|-------------------|----------------|----------|-------|
| Sample Name | sample_id | ✅ Yes | Must match existing sample in Felicity |
| Sample Type | sample_type | ✅ Yes | Unknown, Standard, QC, Blank |
| Acq. Date-Time | acquisition_date | ✅ Yes | ISO format preferred |
| Compound | analyte_name | ✅ Yes | Test/analyte being measured |
| Calc. Conc. | result_value | ✅ Yes | Numeric concentration |
| Conc. Units | result_unit | ✅ Yes | ng/mL, µg/mL, mg/L, etc. |
| Accuracy | accuracy_percent | ⚪ Optional | QC metric |
| RT | retention_time | ⚪ Optional | Minutes |
| Area | peak_area | ⚪ Optional | Chromatography metric |
| Height | peak_height | ⚪ Optional | Chromatography metric |
| S/N | signal_to_noise | ⚪ Optional | Quality metric |
| Dilution | dilution_factor | ⚪ Optional | Applied to result |

---

## Felicity Implementation

### Phase 1: Database Schema (Day 1)

Add LCMS-specific fields to existing tables:

```python
# felicity/apps/iol/lcms/entities.py

from sqlalchemy import Column, String, Float, DateTime, Integer, ForeignKey
from felicity.apps.abstract import BaseEntity

class LCMSInstrument(BaseEntity):
    """LCMS Instrument Configuration"""
    __tablename__ = "lcms_instrument"

    name = Column(String, nullable=False)  # e.g., "Agilent 6470 Triple Quad"
    model = Column(String)  # "6470"
    manufacturer = Column(String)  # "Agilent"
    software = Column(String)  # "MassHunter Quantitative Analysis"
    software_version = Column(String)  # "B.09.00"

    # File monitoring configuration
    export_directory = Column(String)  # Watch folder path
    archive_directory = Column(String)  # Processed files
    error_directory = Column(String)  # Failed imports

    # Parser configuration (JSON)
    parser_config = Column(JSONB)

    is_active = Column(Boolean, default=True)


class LCMSRawData(BaseEntity):
    """Store raw LCMS export files for traceability"""
    __tablename__ = "lcms_raw_data"

    lcms_instrument_uid = Column(String, ForeignKey("lcms_instrument.uid"))
    filename = Column(String, nullable=False)
    file_content = Column(Text)  # Store CSV content
    file_hash = Column(String)  # MD5 hash for duplicate detection
    import_status = Column(String)  # "pending", "processing", "completed", "failed"
    import_timestamp = Column(DateTime)
    error_message = Column(Text)
    samples_imported = Column(Integer, default=0)
    results_imported = Column(Integer, default=0)


class LCMSResult(BaseEntity):
    """Extended result fields specific to LCMS"""
    __tablename__ = "lcms_result"

    analysis_result_uid = Column(String, ForeignKey("analysis_result.uid"))

    # MassHunter specific fields
    acquisition_datetime = Column(DateTime)
    retention_time = Column(Float)  # minutes
    peak_area = Column(Float)
    peak_height = Column(Float)
    signal_to_noise = Column(Float)
    accuracy_percent = Column(Float)
    istd_response = Column(Float)
    qualifier_ion_ratio = Column(Float)
    dilution_factor = Column(Float, default=1.0)

    # QC flags
    rt_deviation = Column(Float)  # Deviation from expected RT
    qualifier_ratio_flag = Column(Boolean)  # Pass/Fail

    # Raw data reference
    lcms_raw_data_uid = Column(String, ForeignKey("lcms_raw_data.uid"))
```

### Phase 2: CSV Parser (Days 2-3)

```python
# felicity/apps/iol/lcms/parsers/masshunter.py

import csv
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime

class MassHunterCSVParser:
    """
    Parse Agilent MassHunter Quantitative Analysis batch export CSV
    """

    # Default column mappings (configurable per instrument)
    DEFAULT_COLUMN_MAP = {
        'sample_id': 'Sample Name',
        'sample_type': 'Sample Type',
        'acquisition_datetime': 'Acq. Date-Time',
        'compound': 'Compound',
        'concentration': 'Calc. Conc.',
        'unit': 'Conc. Units',
        'accuracy': 'Accuracy',
        'retention_time': 'RT',
        'peak_area': 'Area',
        'peak_height': 'Height',
        'signal_to_noise': 'S/N',
        'dilution_factor': 'Dilution'
    }

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.column_map = config.get('column_mappings', self.DEFAULT_COLUMN_MAP)
        self.delimiter = config.get('delimiter', ',')
        self.encoding = config.get('encoding', 'utf-8')
        self.skip_rows = config.get('skip_rows', 0)

    async def parse_file(self, file_path: Path) -> Tuple[List[Dict], str]:
        """
        Parse MassHunter CSV export file

        Returns:
            Tuple of (parsed_results, file_hash)
        """
        # Calculate file hash for duplicate detection
        file_hash = self.calculate_file_hash(file_path)

        results = []

        with open(file_path, 'r', encoding=self.encoding) as f:
            # Skip header rows if configured
            for _ in range(self.skip_rows):
                next(f)

            reader = csv.DictReader(f, delimiter=self.delimiter)

            line_num = 1
            for row in reader:
                try:
                    result = self.parse_row(row, line_num)
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.warning(f"Error parsing line {line_num}: {e}")
                    # Continue parsing, collect errors
                finally:
                    line_num += 1

        logger.info(f"Parsed {len(results)} results from {file_path.name}")
        return results, file_hash

    def parse_row(self, row: Dict, line_num: int) -> Dict:
        """Transform CSV row to Felicity result format"""
        result = {
            'line_number': line_num,
            'raw_data': dict(row)  # Store original for troubleshooting
        }

        # Map required fields
        for felicity_field, csv_column in self.column_map.items():
            value = row.get(csv_column, '').strip()

            if value:
                result[felicity_field] = self.convert_value(
                    value,
                    felicity_field
                )

        # Validate required fields
        required = ['sample_id', 'compound', 'concentration', 'unit']
        missing = [f for f in required if f not in result or not result[f]]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        # Add metadata
        result['import_timestamp'] = datetime.now().isoformat()
        result['data_source'] = 'masshunter_csv'

        return result

    def convert_value(self, value: str, field_type: str):
        """Convert and validate field values"""
        # Numeric fields
        if field_type in ['concentration', 'retention_time', 'peak_area',
                          'peak_height', 'signal_to_noise', 'accuracy',
                          'dilution_factor']:
            # Remove common non-numeric characters
            value = value.replace(',', '').replace('%', '').strip()
            try:
                return float(value) if value else None
            except ValueError:
                logger.warning(f"Cannot convert '{value}' to float for {field_type}")
                return None

        # Datetime fields
        elif field_type == 'acquisition_datetime':
            # MassHunter format: "2025-10-27 10:15:23"
            try:
                return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                # Try alternate formats
                for fmt in ['%m/%d/%Y %H:%M:%S', '%d-%b-%Y %H:%M:%S']:
                    try:
                        return datetime.strptime(value, fmt)
                    except ValueError:
                        continue
                logger.warning(f"Cannot parse datetime: {value}")
                return None

        # String fields (sample_id, compound, unit, sample_type)
        else:
            return value.strip() if value else None

    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file for duplicate detection"""
        hash_md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def validate_results(self, results: List[Dict]) -> Tuple[List[Dict], List[str]]:
        """
        Validate parsed results

        Returns:
            Tuple of (valid_results, validation_errors)
        """
        valid_results = []
        errors = []

        for result in results:
            validation_errors = []

            # Check concentration is positive
            if result.get('concentration') and result['concentration'] <= 0:
                validation_errors.append(
                    f"Line {result['line_number']}: Negative concentration"
                )

            # Check unit is valid
            valid_units = ['ng/mL', 'µg/mL', 'mg/L', 'mg/mL', 'ng/L',
                          'pg/mL', 'ppm', 'ppb', '%']
            if result.get('unit') and result['unit'] not in valid_units:
                validation_errors.append(
                    f"Line {result['line_number']}: Invalid unit '{result['unit']}'"
                )

            # Check sample type
            valid_types = ['Unknown', 'Standard', 'QC', 'QC Control',
                          'Blank', 'Calibration']
            if result.get('sample_type') and result['sample_type'] not in valid_types:
                validation_errors.append(
                    f"Line {result['line_number']}: Invalid sample type"
                )

            if validation_errors:
                errors.extend(validation_errors)
            else:
                valid_results.append(result)

        return valid_results, errors
```

### Phase 3: File Monitor Service (Days 3-4)

```python
# felicity/apps/iol/lcms/services/file_monitor.py

import asyncio
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

class MassHunterFileMonitor(FileSystemEventHandler):
    """
    Monitor directory for MassHunter export files
    Auto-import when new files detected
    """

    def __init__(self, lcms_instrument_config: dict, parser: MassHunterCSVParser):
        self.config = lcms_instrument_config
        self.parser = parser
        self.watch_dir = Path(lcms_instrument_config['export_directory'])
        self.archive_dir = Path(lcms_instrument_config['archive_directory'])
        self.error_dir = Path(lcms_instrument_config['error_directory'])
        self.processed_hashes = set()  # Prevent duplicate imports

        # Create directories if they don't exist
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.error_dir.mkdir(parents=True, exist_ok=True)

    def on_created(self, event):
        """Handle new file creation"""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Check if should process
        if self.should_process(file_path):
            # Wait for file to be fully written
            asyncio.create_task(self.process_file_when_ready(file_path))

    def should_process(self, file_path: Path) -> bool:
        """Check if file should be processed"""
        # Check extension
        if file_path.suffix.lower() not in ['.csv', '.xlsx']:
            return False

        # Check filename pattern (if configured)
        pattern = self.config.get('filename_pattern')
        if pattern and not re.match(pattern, file_path.name):
            return False

        # Check if temp file
        if file_path.name.startswith('~') or file_path.name.startswith('.'):
            return False

        return True

    async def process_file_when_ready(self, file_path: Path):
        """
        Wait for file to be completely written before processing
        (File may still be open by MassHunter during export)
        """
        max_wait = 60  # seconds
        check_interval = 2  # seconds
        elapsed = 0

        last_size = -1
        while elapsed < max_wait:
            try:
                current_size = file_path.stat().st_size

                # File size hasn't changed, assume complete
                if current_size == last_size and current_size > 0:
                    await self.process_file(file_path)
                    return

                last_size = current_size
                await asyncio.sleep(check_interval)
                elapsed += check_interval

            except Exception as e:
                logger.error(f"Error checking file {file_path}: {e}")
                await asyncio.sleep(check_interval)
                elapsed += check_interval

        logger.warning(f"File {file_path} not stable after {max_wait}s")

    async def process_file(self, file_path: Path):
        """Parse and import MassHunter export file"""
        logger.info(f"Processing MassHunter file: {file_path}")

        try:
            # Parse file
            results, file_hash = await self.parser.parse_file(file_path)

            # Check for duplicate import
            if file_hash in self.processed_hashes:
                logger.warning(f"File {file_path.name} already processed (duplicate hash)")
                await self.archive_file(file_path, reason="duplicate")
                return

            # Validate results
            valid_results, validation_errors = self.parser.validate_results(results)

            if validation_errors:
                logger.warning(f"Validation errors in {file_path.name}:")
                for error in validation_errors:
                    logger.warning(f"  - {error}")

            if not valid_results:
                raise ValueError("No valid results found in file")

            # Create raw data record
            raw_data_record = await self.create_raw_data_record(
                file_path, file_hash, len(valid_results)
            )

            # Import results to Felicity
            import_summary = await self.import_results(
                valid_results, raw_data_record['uid']
            )

            # Update raw data record
            await self.update_raw_data_record(
                raw_data_record['uid'],
                status='completed',
                samples_imported=import_summary['samples'],
                results_imported=import_summary['results']
            )

            # Add to processed set
            self.processed_hashes.add(file_hash)

            # Archive file
            await self.archive_file(file_path, reason="success")

            logger.info(
                f"Successfully imported {import_summary['results']} results "
                f"from {file_path.name}"
            )

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            await self.handle_error(file_path, str(e))

    async def import_results(self, results: List[Dict], raw_data_uid: str) -> Dict:
        """Import results to Felicity database"""
        from felicity.apps.analysis.services import AnalysisResultService
        from felicity.apps.iol.lcms.services import LCMSResultService

        samples_count = 0
        results_count = 0
        errors = []

        # Group by sample
        from collections import defaultdict
        by_sample = defaultdict(list)
        for result in results:
            by_sample[result['sample_id']].append(result)

        for sample_id, sample_results in by_sample.items():
            try:
                # Find sample in Felicity
                sample = await SampleService.get_by_sample_id(sample_id)

                if not sample:
                    logger.warning(f"Sample not found: {sample_id}")
                    errors.append(f"Sample not found: {sample_id}")
                    continue

                samples_count += 1

                # Import each result
                for result_data in sample_results:
                    try:
                        # Create analysis result
                        analysis_result = await AnalysisResultService.create({
                            'sample_uid': sample.uid,
                            'analysis_uid': result_data['compound'],  # Map to analysis
                            'result': str(result_data['concentration']),
                            'unit': result_data['unit'],
                            'instrument': 'masshunter_lcms',
                            'method': result_data.get('method'),
                            'analyst_uid': None,  # System import
                        })

                        # Create LCMS-specific result data
                        await LCMSResultService.create({
                            'analysis_result_uid': analysis_result.uid,
                            'acquisition_datetime': result_data.get('acquisition_datetime'),
                            'retention_time': result_data.get('retention_time'),
                            'peak_area': result_data.get('peak_area'),
                            'peak_height': result_data.get('peak_height'),
                            'signal_to_noise': result_data.get('signal_to_noise'),
                            'accuracy_percent': result_data.get('accuracy'),
                            'dilution_factor': result_data.get('dilution_factor', 1.0),
                            'lcms_raw_data_uid': raw_data_uid
                        })

                        results_count += 1

                    except Exception as e:
                        logger.error(
                            f"Error importing result for {sample_id}, "
                            f"{result_data['compound']}: {e}"
                        )
                        errors.append(str(e))

            except Exception as e:
                logger.error(f"Error processing sample {sample_id}: {e}")
                errors.append(str(e))

        return {
            'samples': samples_count,
            'results': results_count,
            'errors': errors
        }

    async def archive_file(self, file_path: Path, reason: str = "success"):
        """Move file to archive directory"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        new_name = f"{timestamp}_{file_path.name}"
        archive_path = self.archive_dir / new_name

        shutil.move(str(file_path), str(archive_path))
        logger.info(f"Archived file to: {archive_path}")

    async def handle_error(self, file_path: Path, error_message: str):
        """Move file to error directory for manual review"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        new_name = f"{timestamp}_{file_path.name}"
        error_path = self.error_dir / new_name

        shutil.move(str(file_path), str(error_path))

        # Also save error log
        error_log_path = error_path.with_suffix('.error.txt')
        with open(error_log_path, 'w') as f:
            f.write(f"Error processing file: {file_path.name}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Error: {error_message}\n")

        logger.error(f"Moved failed file to: {error_path}")
```

---

## Configuration Example

```json
{
  "lcms_instrument": {
    "name": "SCL Agilent 6470 Triple Quad",
    "model": "6470",
    "manufacturer": "Agilent",
    "software": "MassHunter Quantitative Analysis",
    "software_version": "B.09.00",
    "export_directory": "C:\\MassHunterData\\Exports",
    "archive_directory": "C:\\MassHunterData\\Processed",
    "error_directory": "C:\\MassHunterData\\Errors",
    "file_monitor": {
      "enabled": true,
      "poll_interval_seconds": 60,
      "filename_pattern": ".*BatchResults.*\\.(csv|xlsx)$"
    },
    "parser_config": {
      "format": "csv",
      "delimiter": ",",
      "encoding": "utf-8",
      "skip_rows": 0,
      "column_mappings": {
        "sample_id": "Sample Name",
        "sample_type": "Sample Type",
        "acquisition_datetime": "Acq. Date-Time",
        "compound": "Compound",
        "concentration": "Calc. Conc.",
        "unit": "Conc. Units",
        "accuracy": "Accuracy",
        "retention_time": "RT",
        "peak_area": "Area",
        "peak_height": "Height",
        "signal_to_noise": "S/N",
        "dilution_factor": "Dilution"
      }
    }
  }
}
```

---

## Implementation Timeline

### Week 1: Core Development

**Day 1** (Database & Models):
- [ ] Create LCMS entities (LCMSInstrument, LCMSRawData, LCMSResult)
- [ ] Create database migration
- [ ] Run migration, verify schema

**Day 2-3** (Parser):
- [ ] Implement MassHunterCSVParser
- [ ] Add unit tests with sample CSVs
- [ ] Validate all field conversions
- [ ] Test error handling

**Day 3-4** (File Monitor):
- [ ] Implement file watcher service
- [ ] Add duplicate detection
- [ ] Implement result import logic
- [ ] Add error handling and logging

**Day 5** (GraphQL API):
- [ ] Add LCMS instrument queries/mutations
- [ ] Add import status queries
- [ ] Add manual import trigger
- [ ] Test API endpoints

### Week 2: Frontend, Testing & Deployment

**Day 6-7** (Admin Interface):
- [ ] LCMS instrument configuration page
- [ ] File import monitoring dashboard
- [ ] Manual import trigger UI
- [ ] Error log viewer

**Day 8-9** (Testing):
- [ ] Unit tests for parser
- [ ] Integration tests for import
- [ ] Test with real MassHunter exports
- [ ] Error scenario testing
- [ ] Performance testing (large batches)

**Day 10** (Deployment):
- [ ] Deploy to staging
- [ ] Configure MassHunter export
- [ ] Parallel testing (manual + automated)
- [ ] Production deployment
- [ ] User training

---

## Success Criteria

✅ **Automated Import**: Files automatically imported within 2 minutes of export
✅ **Accuracy**: 100% of valid results imported correctly
✅ **Error Handling**: Failed imports logged and moved to error folder
✅ **Traceability**: Full audit trail from raw file to result
✅ **Performance**: Process 100+ samples in < 30 seconds
✅ **User Satisfaction**: Lab staff report time savings and reduced errors

---

## Next Steps - Action Required

### 1. Provide Sample Export File
**Please export a sample batch from MassHunter and share:**
- File format (CSV or Excel)
- Actual column names used
- At least 5-10 sample results
- Include different sample types (Unknown, QC, Standard)

This will allow me to:
- Verify column mappings
- Test the parser
- Ensure all data is captured correctly

### 2. Confirm File Locations
**Windows paths where files will be stored:**
- Export folder (where MassHunter saves): `C:\MassHunterData\Exports\`?
- Archive folder (successful imports): `C:\MassHunterData\Processed\`?
- Error folder (failed imports): `C:\MassHunterData\Errors\`?

### 3. Sample Naming Convention
**How are samples named in MassHunter?**
- Do they match Felicity sample IDs exactly?
- Example format: `SCL-001`, `2025-001`, `SL123456`?
- Any prefix/suffix to remove?

### 4. Analyte/Test Mapping
**How do MassHunter compound names map to Felicity analyses?**
- Are they exact matches?
- Example: MassHunter "Caffeine" = Felicity "CAF"?
- Need mapping table?

---

## Questions?

1. How many samples do you typically run per batch?
2. How often do you export results? (Daily? Per batch? Weekly?)
3. Do you need bidirectional integration (send sample info to MassHunter)?
4. Any specific QC rules to apply automatically?
5. What reports do you currently generate manually that should be automated?

---

**Status**: Awaiting sample export file to finalize implementation
**Estimated Start**: Immediate upon receiving sample data
**Estimated Completion**: 1-2 weeks from start

**Last Updated**: 2025-10-27
