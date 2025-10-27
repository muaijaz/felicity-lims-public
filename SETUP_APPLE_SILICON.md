# Felicity LIMS - Apple Silicon (M1/M2/M3/M4) Setup Guide

This guide covers the specific setup requirements and fixes for running Felicity LIMS on Apple Silicon Macs.

## Prerequisites

- **macOS** with Apple Silicon (M1, M2, M3, or M4)
- **Docker Desktop** for Mac (ARM64 version)
- **Git**
- At least **8GB RAM** available

## Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/felicity-lims.git
cd felicity-lims

# Start all services
docker compose -f docker-compose.dev.yml up -d --build

# Wait for services to be ready (2-3 minutes)
# Check status
docker ps

# Run database migrations
docker compose -f docker-compose.dev.yml exec felicity-api alembic upgrade head

# Access the application
open http://localhost:3000
```

## Apple Silicon Specific Fixes

This fork includes several fixes specifically for Apple Silicon compatibility:

### 1. Password Hashing (Critical Fix)
**Issue**: bcrypt library has ARM64 compatibility issues
**Solution**: Changed to argon2 password hashing

File: `felicity/core/security.py`
```python
# Changed from:
schemes=["bcrypt"]

# To:
schemes=["argon2", "bcrypt"]
```

### 2. Database Configuration
**Issue**: MongoDB and PostgreSQL database naming inconsistencies
**Solution**: Standardized to `felicity_lims` database name

Files modified:
- `felicity/database/mongo.py` - MongoDB database name
- `docker-compose.dev.yml` - DbGate MongoDB config
- `felicity/version/upgrade.py` - PostgreSQL connection string

### 3. GitHub Version Check
**Issue**: Hardcoded expired GitHub token causing 502 errors
**Solution**: Made GitHub token optional via environment variable

File: `felicity/version/version.py`
```python
# Now uses environment variable
_pat = os.getenv("GITHUB_TOKEN", None)
```

### 4. WebSocket Connections
**Issue**: WebSocket auth failures causing stream errors
**Solution**: Made WebSocket auth non-blocking, enforced at subscription level

File: `felicity/lims/gql_router.py`

### 5. MongoDB Logging Verbosity
**Issue**: Excessive connection logs cluttering Docker console
**Solution**: Added quiet mode to MongoDB

File: `docker-compose.dev.yml`
```yaml
command: ["mongod", "--quiet", "--logpath", "/dev/null"]
```

## Default Credentials

### Felicity LIMS Web Application
- **URL**: http://localhost:3000
- **Email**: `admin@example.com` (check your database or setup configuration)
- **Password**: `Admin2024!` (default, change immediately in production)

### DbGate (Database Admin)
- **URL**: http://localhost:8051
- **Username**: `felicity`
- **Password**: `dbgate_secure_2024`

### MinIO Console (Object Storage)
- **URL**: http://localhost:9001
- **Username**: `felicity`
- **Password**: `minio_secure_2024`

## Environment Variables

The `.env` file is pre-configured for Apple Silicon. Key variables:

```bash
# Database
POSTGRES_DB=felicity_lims
POSTGRES_USER=felicity
POSTGRES_PASSWORD=felicity

# MongoDB
MONGODB_USER=felicity
MONGODB_PASS=felicity

# MinIO
MINIO_ACCESS=felicity
MINIO_SECRET=felicity

# API Settings
LOAD_SETUP_DATA=False  # Set to True to load sample data
TESTING=False

# Security
FIRST_SUPERUSER_PASSWORD='!Felicity#100'  # Not used with existing DB
SYSTEM_DAEMON_PASSWORD='!System@Daemon#100'  # Not used with existing DB

# Optional: GitHub version check
GITHUB_TOKEN=  # Leave empty to disable version checks
```

## Port Mappings

| Service | Container Port | Host Port | Purpose |
|---------|----------------|-----------|---------|
| Web App | 3000 | 3000 | Vue.js frontend |
| API | 8000 | 8000 | FastAPI + GraphQL |
| PostgreSQL | 5432 | 5434 | Primary database |
| MongoDB | 27017 | 27027 | Audit logs |
| MinIO API | 9000 | 9000 | Object storage |
| MinIO Console | 9001 | 9001 | Storage admin UI |
| DragonflyDB | 6379 | 6379 | Redis cache |
| DbGate | 3000 | 8051 | Database admin |

## Docker Resource Limits

For optimal performance on Apple Silicon:

```yaml
# In docker-compose.dev.yml (already configured)
services:
  felicity-api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

Adjust based on your Mac's specifications:
- **8GB RAM Mac**: Use defaults
- **16GB+ RAM Mac**: Can increase to 4G memory

## Troubleshooting

### ARM64-Specific Issues

#### Issue: bcrypt Installation Fails
**Solution**: System now uses argon2 instead of bcrypt

#### Issue: PostgreSQL "database does not exist"
**Cause**: Old hardcoded database names
**Solution**: Already fixed in this fork

#### Issue: MongoDB Excessive Logging
**Solution**: Already configured with `--quiet` mode

### General Issues

#### Ports Already in Use
```bash
# Check what's using the port
lsof -i :3000
lsof -i :8000

# Kill the process or change ports in docker-compose.dev.yml
```

#### Database Connection Errors
```bash
# Check PostgreSQL health
docker exec felicity-postgres pg_isready -U felicity

# View logs
docker logs felicity-postgres --tail 50
```

#### API Won't Start
```bash
# Check logs
docker logs felicity-api --tail 100

# Common causes:
# 1. Database not ready - wait 30 seconds after starting
# 2. Migration needed - run alembic upgrade head
# 3. Port conflict - check if 8000 is in use
```

#### Frontend Build Errors
```bash
# Rebuild frontend
docker compose -f docker-compose.dev.yml up -d --build felicity-webapp

# Check logs
docker logs felicity-webapp --tail 50
```

## Performance Optimization

### Rosetta 2 (Not Needed)
Docker Desktop for Mac ARM64 runs natively on Apple Silicon - no Rosetta 2 needed.

### Docker Desktop Settings
Recommended settings for Apple Silicon:
- **CPUs**: 4-6 (depending on your Mac)
- **Memory**: 8GB (minimum), 12GB (recommended)
- **Swap**: 2GB
- **Disk**: 60GB (for development)

### Build Performance
```bash
# Use BuildKit for faster builds
export DOCKER_BUILDKIT=1
docker compose -f docker-compose.dev.yml build
```

## Development Workflow

### Hot Reload (Already Enabled)
- **Backend**: Edit `felicity/**/*.py` → Auto-reloads
- **Frontend**: Edit `webapp/**/*.vue` → Auto-reloads

### Running Tests
```bash
# Backend tests
docker compose -f docker-compose.dev.yml exec felicity-api pytest

# Frontend tests
docker compose -f docker-compose.dev.yml exec felicity-webapp npm test
```

### Database Access
```bash
# PostgreSQL
docker exec -it felicity-postgres psql -U felicity -d felicity_lims

# MongoDB
docker exec -it felicity-mongo mongosh -u felicity -p felicity
```

## Known Limitations on Apple Silicon

1. **Syncfusion Word Processor**: Commented out in docker-compose (no ARM64 image)
2. **Some Python packages**: May build from source (slower first build)
3. **QEMU emulation**: Not needed - all images are ARM64 native

## Performance Optimizations

This fork includes extensive Apple Silicon optimizations. For detailed information, see:
- **[APPLE_SILICON_OPTIMIZATIONS.md](APPLE_SILICON_OPTIMIZATIONS.md)** - Comprehensive performance guide

**Quick Performance Tips**:
- Enable BuildKit: `export DOCKER_BUILDKIT=1`
- Use warm cache: 2-3x faster rebuilds
- All images are ARM64-native (no emulation)
- Resource limits tuned for M2/M3/M4 performance cores

## Additional Resources

- [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
- [Apple Silicon Docker Performance](https://docs.docker.com/desktop/mac/apple-silicon/)
- [Felicity LIMS Documentation](docs/)
- [Apple Silicon Optimizations Guide](APPLE_SILICON_OPTIMIZATIONS.md)

## Contributing

If you find Apple Silicon-specific issues:
1. Check this guide first
2. Search existing issues
3. Open a new issue with:
   - Mac model and chip (M1/M2/M3/M4)
   - macOS version
   - Docker Desktop version
   - Error logs

## License

Same as main Felicity LIMS project - see [LICENSE](LICENSE)

---

**Last Updated**: October 27, 2024
**Tested On**: M2 Max, macOS Sonoma 15.0
**Docker Desktop**: 4.25+
