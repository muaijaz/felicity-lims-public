# LCMS Integration with Felicity LIMS

**Date**: 2025-10-27
**Status**: Requirements Gathering
**Priority**: 🔥 HIGHEST - Required ASAP

---

## Overview

Comprehensive guide for integrating Liquid Chromatography-Mass Spectrometry (LCMS) instruments with Felicity LIMS. This document covers common integration patterns, protocols, file formats, and implementation strategies.

---

## Common LCMS Software Platforms

### 1. Agilent MassHunter
- **Raw Data Format**: `.d` directories (proprietary)
- **Export Formats**: MGF, mzML, mzXML, CSV
- **API Support**: Yes (SDK available)
- **LIMS Integration**: File export, API, database

### 2. Waters MassLynx
- **Raw Data Format**: `.raw` files (proprietary)
- **Export Formats**: NetCDF, ASCII, PKL, DTA, MGF, mzML
- **API Support**: Yes (Waters API for third-party integration)
- **LIMS Integration**: File export, API, post-run automation

### 3. Thermo Scientific Xcalibur
- **Raw Data Format**: `.RAW` files (proprietary)
- **Export Formats**: mzML, mzXML, MGF, CSV, Excel
- **API Support**: Yes (FileIO library, MSFileReader)
- **LIMS Integration**: File export, API

### 4. Shimadzu LabSolutions
- **Raw Data Format**: Proprietary formats
- **Export Formats**: ASCII, CSV, mzML
- **API Support**: Limited
- **LIMS Integration**: File export, database

### 5. PerkinElmer Chromera
- **Raw Data Format**: Proprietary
- **Export Formats**: CSV, Excel, PDF reports
- **API Support**: Limited
- **LIMS Integration**: File export

---

## Standard Data File Formats

### 1. mzML (Recommended)
**Description**: XML-based open format, industry standard since 2008
**Established By**: Proteomics Standards Initiative (PSI)
**Advantages**:
- Open standard, vendor-neutral
- Comprehensive metadata support
- Wide tool support (ProteoWizard, mzmine, etc.)
- Suitable for proteomics and metabolomics

**Structure**:
```xml
<?xml version="1.0" encoding="utf-8"?>
<mzML xmlns="http://psi.hupo.org/ms/mzml">
  <cvList>...</cvList>
  <fileDescription>...</fileDescription>
  <referenceableParamGroupList>...</referenceableParamGroupList>
  <sampleList>...</sampleList>
  <softwareList>...</softwareList>
  <instrumentConfigurationList>...</instrumentConfigurationList>
  <dataProcessingList>...</dataProcessingList>
  <run>
    <spectrumList>
      <spectrum>...</spectrum>
    </spectrumList>
  </run>
</mzML>
```

### 2. mzXML
**Description**: XML-based predecessor to mzML
**Advantages**: Legacy support, simpler than mzML
**Disadvantages**: Being replaced by mzML

### 3. mzMLb (Modern Alternative)
**Description**: HDF5-based binary format
**Advantages**:
- Optimized for read/write speed
- Smaller file sizes
- Efficient random access
**Disadvantages**: Newer, less tool support

### 4. NetCDF (CDF)
**Description**: Network Common Data Format
**Advantages**: Simple, widely supported
**Disadvantages**: Limited metadata, older standard

### 5. MGF (Mascot Generic Format)
**Description**: Text-based MS/MS data format
**Use Case**: Primarily for MS/MS search engines
**Structure**:
```
BEGIN IONS
TITLE=Spectrum 1
RTINSECONDS=120.5
PEPMASS=456.789 1000.0
CHARGE=2+
123.456 789.0
234.567 890.0
END IONS
```

### 6. CSV/TXT (Simple Export)
**Description**: Tabular data format
**Use Case**: Quantitation results, peak lists
**Structure**:
```csv
Sample ID,Analyte,Concentration,Unit,RT,Area,Height
S001,Caffeine,125.5,ng/mL,3.45,1234567,98765
S001,Theophylline,85.2,ng/mL,4.12,987654,76543
```

---

## Integration Patterns

### Pattern 1: File-Based Integration (Most Common) ⭐

**How It Works**:
```
LCMS Software → Export Results → File System → Felicity File Monitor → Parse → Import
```

**Advantages**:
- ✅ Simple, reliable, no network dependencies
- ✅ Works with any LCMS software that can export files
- ✅ No special permissions or API access needed
- ✅ Easy to troubleshoot and retry failed imports

**Disadvantages**:
- ❌ Not real-time (polling interval delay)
- ❌ Requires file system access
- ❌ Manual export setup per instrument

**Implementation in Felicity**:
```python
# felicity/apps/iol/lcms/file_monitor.py

import asyncio
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class LCMSFileMonitor(FileSystemEventHandler):
    """
    Monitor directory for LCMS result files
    Supports: CSV, mzML, mzXML, TXT
    """

    def __init__(self, watch_dir: str, parser_config: dict):
        self.watch_dir = Path(watch_dir)
        self.parser_config = parser_config
        self.processed_files = set()

    def on_created(self, event):
        """Handle new file creation"""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Check if file matches expected pattern
        if self.should_process(file_path):
            asyncio.create_task(self.process_file(file_path))

    def should_process(self, file_path: Path) -> bool:
        """Check if file should be processed"""
        # Check extension
        allowed_extensions = ['.csv', '.txt', '.mzml', '.mzxml']
        if file_path.suffix.lower() not in allowed_extensions:
            return False

        # Check if already processed
        if str(file_path) in self.processed_files:
            return False

        # Check filename pattern (e.g., must contain "results")
        pattern = self.parser_config.get('filename_pattern', None)
        if pattern and not re.match(pattern, file_path.name):
            return False

        return True

    async def process_file(self, file_path: Path):
        """Parse and import LCMS results"""
        try:
            # Wait for file to be fully written
            await self.wait_for_file_complete(file_path)

            # Parse based on format
            if file_path.suffix.lower() == '.csv':
                results = await self.parse_csv(file_path)
            elif file_path.suffix.lower() in ['.mzml', '.mzxml']:
                results = await self.parse_mzml(file_path)
            else:
                results = await self.parse_txt(file_path)

            # Import to Felicity
            await self.import_results(results)

            # Mark as processed
            self.processed_files.add(str(file_path))

            # Archive or delete file
            await self.archive_file(file_path)

            logger.info(f"Successfully processed LCMS file: {file_path}")

        except Exception as e:
            logger.error(f"Error processing LCMS file {file_path}: {e}")
            # Move to error directory for manual review
            await self.move_to_error_dir(file_path)
```

**Configuration**:
```json
{
  "lcms_file_monitor": {
    "watch_directory": "/data/lcms/exports",
    "archive_directory": "/data/lcms/processed",
    "error_directory": "/data/lcms/errors",
    "poll_interval_seconds": 30,
    "filename_pattern": ".*_results_.*\\.csv$",
    "parser": {
      "format": "csv",
      "delimiter": ",",
      "encoding": "utf-8",
      "skip_rows": 0,
      "column_mappings": {
        "sample_id": "Sample ID",
        "analyte": "Analyte",
        "result": "Concentration",
        "unit": "Unit",
        "retention_time": "RT",
        "peak_area": "Area",
        "peak_height": "Height"
      }
    }
  }
}
```

---

### Pattern 2: REST API Integration

**How It Works**:
```
LCMS Software API ← HTTP Requests ← Felicity
```

**Advantages**:
- ✅ Real-time data access
- ✅ Bidirectional (can send sample info to LCMS)
- ✅ Structured data format (JSON/XML)

**Disadvantages**:
- ❌ Requires LCMS software with API support
- ❌ More complex setup (authentication, networking)
- ❌ Vendor-specific implementations

**Implementation**:
```python
# felicity/apps/iol/lcms/api_client.py

import aiohttp
from typing import Dict, List

class LCMSAPIClient:
    """
    Generic LCMS API client
    Supports: Agilent MassHunter, Waters MassLynx APIs
    """

    def __init__(self, base_url: str, api_key: str, instrument_type: str):
        self.base_url = base_url
        self.api_key = api_key
        self.instrument_type = instrument_type
        self.session = None

    async def connect(self):
        """Establish API connection"""
        self.session = aiohttp.ClientSession(
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
        )

    async def get_samples(self, status: str = 'completed') -> List[Dict]:
        """Retrieve samples by status"""
        url = f"{self.base_url}/api/v1/samples"
        params = {'status': status}

        async with self.session.get(url, params=params) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_results(self, sample_id: str) -> Dict:
        """Get results for specific sample"""
        url = f"{self.base_url}/api/v1/samples/{sample_id}/results"

        async with self.session.get(url) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def submit_sample(self, sample_data: Dict) -> Dict:
        """Submit new sample to LCMS"""
        url = f"{self.base_url}/api/v1/samples"

        async with self.session.post(url, json=sample_data) as resp:
            resp.raise_for_status()
            return await resp.json()
```

---

### Pattern 3: Database Integration

**How It Works**:
```
LCMS Database ← SQL Queries ← Felicity
```

**Advantages**:
- ✅ Direct data access
- ✅ Real-time updates
- ✅ Can query historical data

**Disadvantages**:
- ❌ Requires database credentials and permissions
- ❌ Must understand vendor database schema
- ❌ Schema changes can break integration
- ❌ May violate vendor support agreements

**Implementation**:
```python
# felicity/apps/iol/lcms/database_connector.py

import asyncpg
from typing import List, Dict

class LCMSDatabaseConnector:
    """
    Connect to LCMS software database
    Example: MassHunter uses SQL Server, LabSolutions may use Oracle
    """

    def __init__(self, connection_string: str, schema: str):
        self.connection_string = connection_string
        self.schema = schema
        self.pool = None

    async def connect(self):
        """Establish database connection pool"""
        self.pool = await asyncpg.create_pool(self.connection_string)

    async def query_completed_samples(self, since_timestamp: str) -> List[Dict]:
        """Query samples completed since timestamp"""
        query = f"""
            SELECT
                sample_id,
                sample_name,
                acquisition_date,
                method_name,
                operator_name
            FROM {self.schema}.samples
            WHERE status = 'Completed'
            AND acquisition_date > $1
            ORDER BY acquisition_date DESC
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, since_timestamp)
            return [dict(row) for row in rows]

    async def query_results(self, sample_id: str) -> List[Dict]:
        """Query results for specific sample"""
        query = f"""
            SELECT
                r.compound_name,
                r.concentration,
                r.unit,
                r.retention_time,
                r.peak_area,
                r.peak_height,
                r.signal_to_noise
            FROM {self.schema}.results r
            WHERE r.sample_id = $1
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, sample_id)
            return [dict(row) for row in rows]
```

---

### Pattern 4: SiLA 2 Standard (Modern Labs)

**How It Works**:
```
LCMS (SiLA 2 Server) ← gRPC/HTTP2 ← Felicity (SiLA 2 Client)
```

**Advantages**:
- ✅ Industry standard for lab automation
- ✅ Plug-and-play compatibility
- ✅ Bidirectional communication
- ✅ Device control + data retrieval

**Disadvantages**:
- ❌ Limited LCMS vendor support currently
- ❌ Requires SiLA 2 enabled instruments
- ❌ More complex implementation

**SiLA 2 Overview**:
- Uses gRPC over HTTP/2
- Protocol Buffers for serialization
- Standardized commands and features
- Connects LIMS, ELN, CDS, and lab devices

**Reference**: https://sila-standard.com/

---

## Data Conversion Tools

### ProteoWizard MSConvert
**Purpose**: Convert vendor formats to open formats
**Supports**:
- Agilent (.d)
- Waters (.raw)
- Thermo (.RAW)
- Bruker (.d)
- AB Sciex (.wiff)

**Usage**:
```bash
msconvert input.d --mzML --filter "peakPicking true 1-" --output /path/to/output/
```

**Integration in Felicity**:
```python
import subprocess

async def convert_to_mzml(input_file: str, output_dir: str) -> str:
    """Convert vendor format to mzML using msconvert"""
    cmd = [
        'msconvert',
        input_file,
        '--mzML',
        '--output', output_dir
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Conversion failed: {result.stderr}")

    # Return path to converted file
    return Path(output_dir) / f"{Path(input_file).stem}.mzML"
```

---

## Implementation Recommendations

### Phase 1: Discovery & Requirements (1-2 days)

**Questions to Answer**:
1. **What LCMS instruments do you have?**
   - Manufacturer and model
   - Software version (MassHunter, MassLynx, Xcalibur, etc.)
   - Current version numbers

2. **What is the current workflow?**
   - How are results currently captured?
   - Manual entry into LIMS?
   - Export to Excel/CSV?
   - Any existing middleware?

3. **What data needs to be transferred?**
   - Sample ID
   - Analyte/compound names
   - Quantitation results (concentration)
   - Units of measurement
   - Retention times
   - Peak areas/heights
   - Calibration curve info
   - QC data
   - Chromatogram images?

4. **What is the data flow direction?**
   - Unidirectional: LCMS → LIMS only
   - Bidirectional: LIMS → LCMS (sample info) + LCMS → LIMS (results)

5. **What are the integration options available?**
   - Can LCMS software export files automatically?
   - Does it have an API?
   - Database access available?
   - Network connectivity?

6. **What is the expected volume?**
   - How many samples per day?
   - How many analytes per sample?
   - Data retention requirements?

### Phase 2: Design (2-3 days)

Based on answers to Phase 1, select integration pattern and design:

**File-Based Integration** (Most likely):
1. Determine export format (CSV recommended for simplicity)
2. Define export file location (shared network drive or local)
3. Map LCMS export columns to Felicity fields
4. Design file naming convention
5. Plan error handling and archival

**Example Design Document**:
```yaml
lcms_integration_design:
  instrument:
    manufacturer: "Agilent"
    model: "6470 Triple Quadrupole LC/MS"
    software: "MassHunter Quantitative Analysis"
    version: "B.09.00"

  integration_method: "file_based"

  file_export:
    format: "csv"
    location: "/data/lcms/exports/"
    frequency: "post_acquisition"  # or "scheduled_batch"
    filename_pattern: "{date}_{sequence}_{method}_results.csv"
    encoding: "utf-8"
    delimiter: ","

  data_mapping:
    sample_id: "Sample Name"
    analyte: "Compound"
    concentration: "Calc. Conc."
    unit: "Conc. Units"
    retention_time: "RT"
    peak_area: "Area"
    response: "Response"

  import_workflow:
    poll_interval: 60  # seconds
    validation:
      - check_sample_exists: true
      - validate_units: true
      - check_qc_status: true
    error_handling:
      - archive_successful: true
      - move_failed_to_error_dir: true
      - send_notification: true
```

### Phase 3: Implementation (1-2 weeks)

**Tasks**:
1. [ ] Create LCMS module in Felicity
   - `felicity/apps/iol/lcms/` directory structure
   - Models for LCMS instruments and results
   - Services for data parsing and import

2. [ ] Implement file parser
   - CSV parser with configurable column mapping
   - mzML parser if needed
   - Data validation logic

3. [ ] Implement file monitor
   - Directory watcher with configurable polling
   - File completion detection
   - Concurrent processing with asyncio

4. [ ] Implement result import
   - Map LCMS data to Felicity AnalysisResult
   - Handle units conversion
   - Link to existing samples
   - Generate audit trail

5. [ ] Add error handling
   - File parsing errors
   - Sample not found errors
   - Duplicate result handling
   - Notification system

6. [ ] Create admin interface
   - LCMS instrument configuration
   - File import monitoring dashboard
   - Manual import trigger
   - Error log viewer

### Phase 4: Testing (1 week)

**Test Scenarios**:
1. [ ] Happy path: Normal file import
2. [ ] Sample not found in LIMS
3. [ ] Malformed CSV file
4. [ ] Duplicate results
5. [ ] File locked (still being written)
6. [ ] Large batch processing (100+ samples)
7. [ ] Network interruption during file transfer
8. [ ] Invalid data values (negative concentrations, etc.)

### Phase 5: Deployment (1 week)

**Steps**:
1. [ ] Deploy to staging environment
2. [ ] Configure LCMS export to staging directory
3. [ ] Parallel testing (manual + automated)
4. [ ] Validate result accuracy
5. [ ] Train lab staff
6. [ ] Deploy to production
7. [ ] Monitor for 1 week
8. [ ] Optimize based on feedback

---

## Example CSV Parser Implementation

```python
# felicity/apps/iol/lcms/parsers/csv_parser.py

import csv
from pathlib import Path
from typing import List, Dict
from datetime import datetime

class LCMSCSVParser:
    """
    Parse LCMS CSV export files
    Configurable column mappings for different LCMS software
    """

    def __init__(self, config: dict):
        self.config = config
        self.column_map = config['data_mapping']
        self.delimiter = config.get('delimiter', ',')
        self.encoding = config.get('encoding', 'utf-8')
        self.skip_rows = config.get('skip_rows', 0)

    async def parse(self, file_path: Path) -> List[Dict]:
        """Parse CSV file and return structured data"""
        results = []

        with open(file_path, 'r', encoding=self.encoding) as f:
            # Skip header rows if configured
            for _ in range(self.skip_rows):
                next(f)

            reader = csv.DictReader(f, delimiter=self.delimiter)

            for row in reader:
                try:
                    result = self.transform_row(row)
                    if result:  # Skip empty rows
                        results.append(result)
                except Exception as e:
                    logger.warning(f"Error parsing row: {row}. Error: {e}")
                    continue

        return results

    def transform_row(self, row: Dict) -> Dict:
        """Transform CSV row to Felicity result format"""
        # Extract mapped fields
        result = {}

        for felicity_field, csv_column in self.column_map.items():
            value = row.get(csv_column)
            if value:
                result[felicity_field] = self.clean_value(value, felicity_field)

        # Add metadata
        result['import_timestamp'] = datetime.now().isoformat()
        result['data_source'] = 'lcms_csv_import'

        # Validate required fields
        required = ['sample_id', 'analyte', 'concentration']
        if not all(field in result for field in required):
            raise ValueError(f"Missing required fields: {required}")

        return result

    def clean_value(self, value: str, field_type: str) -> any:
        """Clean and convert value based on field type"""
        # Remove whitespace
        value = value.strip()

        # Handle numeric fields
        if field_type in ['concentration', 'retention_time', 'peak_area', 'peak_height']:
            # Remove common non-numeric characters
            value = value.replace(',', '').replace('%', '')
            try:
                return float(value)
            except ValueError:
                logger.warning(f"Could not convert '{value}' to float")
                return None

        # Return string for other fields
        return value
```

---

## Next Steps

To proceed with LCMS integration, please provide:

1. **LCMS Instrument Details**:
   - Manufacturer and model
   - Software name and version
   - How many instruments?

2. **Current Workflow**:
   - How are results currently handled?
   - Any existing export capabilities?

3. **Data Requirements**:
   - What data needs to be transferred?
   - Sample export file (CSV or other format)

4. **Integration Preferences**:
   - Preferred integration method (file, API, database)?
   - Network connectivity available?
   - IT/infrastructure constraints?

5. **Timeline**:
   - When is this needed by?
   - Pilot testing window?

---

## Resources

### Standards & Protocols
- **mzML**: https://www.psidev.info/mzml
- **SiLA 2**: https://sila-standard.com/
- **ASTM E1394**: Clinical laboratory instrument communication
- **ProteoWizard**: http://proteowizard.sourceforge.net/

### Vendor Documentation
- **Agilent MassHunter**: LIMS Integration Guide
- **Waters MassLynx**: API Documentation
- **Thermo Xcalibur**: FileIO Library Documentation

### Open Source Tools
- **mzmine**: Mass spectrometry data processing
- **xcms**: LC-MS data preprocessing
- **ProteoWizard MSConvert**: Format conversion

---

**Last Updated**: 2025-10-27
**Status**: Awaiting requirements from user
**Next Action**: Gather LCMS instrument and workflow information
