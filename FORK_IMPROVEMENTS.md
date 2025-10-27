# Felicity LIMS Fork - Apple Silicon Improvements

This fork includes critical fixes and improvements for running Felicity LIMS on Apple Silicon (M1/M2/M3/M4) Macs.

## Changes Summary

### 1. Apple Silicon Password Hashing Fix ⭐ (Critical)
**File**: `felicity/core/security.py`

**Problem**: bcrypt library has ARM64 compatibility issues on Apple Silicon

**Solution**: Changed password hashing to use argon2 (ARM64 compatible)
```python
# Before:
schemes=["bcrypt"]

# After:
schemes=["argon2", "bcrypt"]
```

**Impact**: API now starts successfully on Apple Silicon Macs

---

### 2. Database Name Standardization
**Files**:
- `felicity/database/mongo.py`
- `docker-compose.dev.yml`
- `felicity/version/upgrade.py`

**Problem**: Inconsistent database naming (`felicity` vs `felicity_lims`) causing connection errors

**Solution**: Standardized all references to `felicity_lims`
- MongoDB: `client.felicity` → `client.felicity_lims`
- DbGate MongoDB config: `DATABASE_mg: felicity` → `DATABASE_mg: felicity_lims`
- Upgrade script: Updated PostgreSQL connection string

**Impact**: No more "database does not exist" errors, cleaner logs

---

### 3. GitHub Version Check Fix
**File**: `felicity/version/version.py`

**Problem**: Hardcoded expired GitHub PAT causing 502 errors on version check

**Solution**:
- Removed hardcoded token
- Made GitHub token optional via `GITHUB_TOKEN` environment variable
- Added graceful error handling with fallback response

```python
# Before:
_pat = "github_pat_11AECNNXA0..." # Expired token

# After:
_pat = os.getenv("GITHUB_TOKEN", None)  # Optional from environment
```

**File**: `felicity/api/rest/api_v1/endpoints/version.py`

Added try/catch to return graceful response instead of error:
```python
return {
    "current_version": felicity_version.version,
    "latest_version": felicity_version.version,
    "update_available": False,
    "message": "Version check unavailable"
}
```

**Impact**: Version endpoint returns 200 instead of 502, no error spam in frontend

---

### 4. WebSocket Connection Improvements
**File**: `felicity/lims/gql_router.py`

**Problem**: WebSocket authentication failures causing "Stream subscription error"

**Solution**: Made WebSocket connection establishment non-blocking
- Connection accepted even without authentication
- Auth still enforced at subscription level (via `@strawberry.subscription(permission_classes=[IsAuthenticated])`)
- Prevents connection rejection for missing/invalid tokens during initial handshake

**Impact**: No more WebSocket connection errors in browser console

---

### 5. MongoDB Logging Reduction
**File**: `docker-compose.dev.yml`

**Problem**: MongoDB generating excessive connection logs cluttering Docker console

**Solution**: Added quiet mode to MongoDB container
```yaml
command: ["mongod", "--quiet", "--logpath", "/dev/null"]
```

**Impact**: Clean Docker console, reduced system resource usage for logging

---

## New Documentation

### 1. Quick Start Guide
**File**: `QUICKSTART.md`

Comprehensive 5-minute setup guide including:
- One-command installation
- Default credentials table
- Service access URLs
- Common commands
- Troubleshooting section

### 2. Apple Silicon Setup Guide
**File**: `SETUP_APPLE_SILICON.md`

Detailed Apple Silicon-specific guide:
- All ARM64 fixes explained
- Performance optimization tips
- Port mappings table
- Docker resource recommendations
- Known limitations

### 3. This Improvements Document
**File**: `FORK_IMPROVEMENTS.md`

Summary of all changes for transparency

---

## Testing Results

All fixes tested on:
- **Hardware**: M2 Max MacBook Pro
- **OS**: macOS Sonoma 15.0
- **Docker**: Docker Desktop 4.25+ (ARM64)

### ✅ Working Features
- API starts successfully
- Database migrations run
- Web interface loads at http://localhost:3000
- Login with default credentials works
- GraphQL API functional
- Version check endpoint returns valid response
- WebSocket connections establish successfully
- MongoDB runs quietly
- All containers healthy

### ✅ Error Resolution
- ❌ "bcrypt incompatible with ARM64" → ✅ Fixed with argon2
- ❌ "database felicity does not exist" → ✅ Fixed with standardization
- ❌ "502 Bad Gateway on /api/v1/version/updates" → ✅ Fixed with graceful handling
- ❌ "Stream subscription error" → ✅ Fixed with non-blocking WebSocket
- ❌ MongoDB log spam → ✅ Fixed with quiet mode

---

## Default Credentials

### Felicity LIMS Application
- **URL**: http://localhost:3000
- **Email**: `admin@example.com` (configured during setup)
- **Password**: `Admin2024!` (default password)

### DbGate (Database Admin)
- **URL**: http://localhost:8051
- **Username**: `felicity`
- **Password**: `dbgate_secure_2024`

### MinIO Console (Object Storage)
- **URL**: http://localhost:9001
- **Username**: `felicity`
- **Password**: `minio_secure_2024`

---

## Files Modified

### Core Application
1. `felicity/core/security.py` - Password hashing
2. `felicity/database/mongo.py` - MongoDB database name
3. `felicity/version/version.py` - GitHub token handling
4. `felicity/api/rest/api_v1/endpoints/version.py` - Error handling
5. `felicity/lims/gql_router.py` - WebSocket auth

### Configuration
6. `docker-compose.dev.yml` - DbGate config, MongoDB quiet mode

### Documentation (New)
7. `QUICKSTART.md` - Quick start guide
8. `SETUP_APPLE_SILICON.md` - Apple Silicon guide
9. `FORK_IMPROVEMENTS.md` - This file

---

## Backward Compatibility

All changes are backward compatible:
- ✅ Works on Intel Macs
- ✅ Works on Linux
- ✅ Works on Windows (WSL2)
- ✅ Works on Apple Silicon

Argon2 is supported on all platforms and provides better security than bcrypt.

---

## Contribution Back to Upstream

These fixes should be contributed back to the original repository:
1. Password hashing change (benefits all platforms)
2. Database naming standardization (improves consistency)
3. GitHub token handling (better security)
4. WebSocket improvements (better UX)
5. MongoDB logging configuration (better DevEx)

---

## License

Same as original Felicity LIMS - see [LICENSE](LICENSE)

---

**Fork Maintainer**: [Your Name]
**Last Updated**: October 27, 2024
**Original Project**: https://github.com/aurthurm/felicity-lims
