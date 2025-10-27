# Felicity LIMS Quick Start Guide

Get Felicity LIMS running on your machine in under 5 minutes!

## Prerequisites

- **Docker Desktop** installed and running
- **Git** installed
- At least **8GB RAM** available
- **20GB disk space** available

## One-Command Setup

```bash
git clone https://github.com/yourusername/felicity-lims.git
cd felicity-lims
./felicity-start.sh
```

That's it! The system will:
- ✅ Start all services (PostgreSQL, MongoDB, MinIO, Redis, API, WebApp)
- ✅ Run database migrations
- ✅ Load sample data (if enabled)
- ✅ Be ready to use in 2-3 minutes

## Access the Application

### Felicity LIMS Web Interface
**URL**: http://localhost:3000

**Login Credentials**:
- Email: `admin@example.com` (or the email configured during setup)
- Password: `Admin2024!` (default, change immediately)

### Additional Services

| Service | URL | Username | Password |
|---------|-----|----------|----------|
| API (GraphQL) | http://localhost:8000 | - | - |
| DbGate (Database Admin) | http://localhost:8051 | felicity | dbgate_secure_2024 |
| MinIO Console (Storage) | http://localhost:9001 | felicity | minio_secure_2024 |

## Manual Setup (Alternative)

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/felicity-lims.git
cd felicity-lims
```

### 2. Create Environment File
```bash
cp .env.example .env
```

The default `.env` is configured for development and includes:
- Database credentials
- HIPAA encryption keys
- Service endpoints
- Admin passwords

### 3. Start Docker Services
```bash
docker compose -f docker-compose.dev.yml up -d --build
```

### 4. Run Database Migrations
```bash
docker compose -f docker-compose.dev.yml exec felicity-api alembic upgrade head
```

### 5. Access the Application
Open http://localhost:3000 and log in with the credentials above.

## What's Running?

After startup, you'll have these containers:

| Container | Service | Port | Purpose |
|-----------|---------|------|---------|
| felicity-webapp | Frontend | 3000 | Vue.js web interface |
| felicity-api | Backend | 8000 | FastAPI + GraphQL |
| felicity-postgres | Database | 5434 | Primary database |
| felicity-mongo | Database | 27027 | Audit logs & documents |
| felicity-minio | Storage | 9000, 9001 | File storage |
| felicity-dragonfly | Cache | 6379 | Redis-compatible cache |
| felicity-dbgate | Admin UI | 8051 | Database management |

## Common Commands

### View Logs
```bash
# All services
docker compose -f docker-compose.dev.yml logs -f

# Specific service
docker logs -f felicity-api
docker logs -f felicity-webapp
```

### Stop Services
```bash
docker compose -f docker-compose.dev.yml down
```

### Stop and Remove Data
```bash
docker compose -f docker-compose.dev.yml down -v
```

### Restart a Service
```bash
docker restart felicity-api
docker restart felicity-webapp
```

## Troubleshooting

### Port Conflicts
If ports 3000, 8000, 5434, 27027, 9000, or 9001 are already in use:

1. Stop other services using those ports
2. Or edit `docker-compose.dev.yml` to use different ports

### Database Connection Errors
```bash
# Check if PostgreSQL is healthy
docker ps | grep felicity-postgres

# View PostgreSQL logs
docker logs felicity-postgres
```

### API Not Starting
```bash
# Check API logs
docker logs felicity-api --tail 50

# Restart API
docker restart felicity-api
```

### Web Interface Not Loading
```bash
# Check webapp logs
docker logs felicity-webapp --tail 50

# Rebuild webapp
docker compose -f docker-compose.dev.yml up -d --build felicity-webapp
```

## Loading Sample Data

The default configuration has `LOAD_SETUP_DATA=False`. To enable sample data:

1. Edit `.env`:
```bash
LOAD_SETUP_DATA=True
```

2. Restart the API:
```bash
docker restart felicity-api
```

Sample data includes:
- Test catalog
- Instrument types
- Quality control samples
- Microbiology panels
- Antibiotic susceptibility test (AST) configurations

## Architecture Overview

### Technology Stack
- **Frontend**: Vue 3 + Vite + Tailwind CSS + URQL GraphQL
- **Backend**: FastAPI + Strawberry GraphQL + SQLAlchemy
- **Primary Database**: PostgreSQL 12
- **Audit/Documents**: MongoDB 7
- **File Storage**: MinIO (S3-compatible)
- **Caching**: DragonflyDB (Redis-compatible)

### Key Features
- Multi-tenant laboratory management
- Patient and sample tracking
- Test result workflows
- Quality control (QC) management
- Inventory management
- Document management (QMS)
- Microbiology workflows
- Billing and invoicing
- HIPAA-compliant data encryption

## Development Mode

The default setup runs in development mode with:
- ✅ Hot reload for code changes
- ✅ Detailed logging
- ✅ Debug mode enabled
- ✅ CORS enabled for localhost
- ⚠️ NOT suitable for production

### Making Code Changes

**Backend** (Python):
1. Edit files in `felicity/` directory
2. API auto-reloads (uvicorn --reload)
3. No restart needed

**Frontend** (Vue):
1. Edit files in `webapp/` directory
2. Vite dev server auto-reloads
3. Changes appear immediately

## Production Deployment

For production deployment:

1. Use `docker-compose.prod.yml` instead
2. Set strong passwords in `.env`
3. Enable HTTPS/TLS
4. Configure proper backup strategy
5. Set `TESTING=False` and `DEBUG=False`
6. Review security settings

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed production setup.

## Next Steps

1. **Explore the Interface**: Navigate through patients, samples, tests, and results
2. **Configure Your Lab**: Add your test catalog, instruments, and users
3. **Review Documentation**: Check [docs/](docs/) for detailed feature guides
4. **Join Community**: Ask questions or contribute improvements

## Getting Help

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/felicity-lims/issues)
- **Community**: Join our discussions

## License

See [LICENSE](LICENSE) file for details.

---

**⚡ Quick Tip**: First startup takes 2-3 minutes while databases initialize. Subsequent starts are faster (~30 seconds).
