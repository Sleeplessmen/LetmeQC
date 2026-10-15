# Phase 1: Docker Setup

## 📌 Overview

**Component:** Docker & Development Environment  
**Duration:** Week 3  
**Owner:** DevOps  
**Priority:** 🟡 MEDIUM  
**Estimate:** 2 days

---

## 🎯 Objectives

Set up **multi-container Docker environment** for:
- Backend FastAPI service
- PostgreSQL database
- Development tools (pgAdmin)

---

## 🐳 Docker Configuration

### Directory Structure
```
LetmeQC/
├── Dockerfile                  # Backend Dockerfile
├── Dockerfile.dev             # Development Dockerfile (optional)
├── docker-compose.yml         # Production compose
├── docker-compose.dev.yml    # Development compose
├── .env.example               # Environment template
└── scripts/
    └── wait-for-db.sh         # DB readiness script
```

---

## 📦 Dockerfile

### Production Dockerfile

```dockerfile
# Dockerfile
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies for PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create database migrations directory
RUN mkdir -p /app/database/migrations/versions

# Set default environment variables
ENV SERVER_HOST=0.0.0.0 \
    SERVER_PORT=8000 \
    ENVIRONMENT=production

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()" || exit 1

# Run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Development Dockerfile (Optional)

```dockerfile
# Dockerfile.dev
FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-dev.txt

# Copy application code
COPY . .

ENV SERVER_HOST=0.0.0.0 \
    SERVER_PORT=8000 \
    ENVIRONMENT=development

EXPOSE 8000

# Run with auto-reload for development
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

---

## 🐙 Docker Compose

### Production Compose (docker-compose.yml)

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    image: letmeqc/backend:latest
    container_name: letmeqc_backend
    environment:
      - CVAT_TOKEN=${CVAT_TOKEN}
      - CVAT_API_URL=${CVAT_API_URL:-https://app.cvat.ai/api}
      - CVAT_ORG_SLUG=${CVAT_ORG_SLUG:-}
      - DATABASE_URL=postgresql://${DB_USER:-letmeqc}:${DB_PASSWORD:-letmeqc}@db:5432/${DB_NAME:-letmeqc}
      - WEBHOOK_SECRET=${WEBHOOK_SECRET}
      - SERVER_HOST=0.0.0.0
      - SERVER_PORT=8000
      - ENVIRONMENT=production
      - MIN_BOX_AREA=${MIN_BOX_AREA:-100}
      - IOU_THRESHOLD=${IOU_THRESHOLD:-0.95}
      - DUPLICATE_IOU_THRESHOLD=${DUPLICATE_IOU_THRESHOLD:-0.98}
    ports:
      - "${SERVER_PORT:-8000}:8000"
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    networks:
      - letmeqc_network

  db:
    image: postgres:13
    container_name: letmeqc_db
    environment:
      - POSTGRES_USER=${DB_USER:-letmeqc}
      - POSTGRES_PASSWORD=${DB_PASSWORD:-letmeqc}
      - POSTGRES_DB=${DB_NAME:-letmeqc}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-letmeqc} -d ${DB_NAME:-letmeqc}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - letmeqc_network

  redis:
    image: redis:6
    container_name: letmeqc_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
    networks:
      - letmeqc_network

  nginx:
    image: nginx:latest
    container_name: letmeqc_nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certs:/etc/nginx/certs
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - letmeqc_network

volumes:
  postgres_data:
  redis_data:

networks:
  letmeqc_network:
    driver: bridge
```

### Development Compose (docker-compose.dev.yml)

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    image: letmeqc/backend:dev
    container_name: letmeqc_backend_dev
    environment:
      - CVAT_TOKEN=${CVAT_TOKEN}
      - CVAT_API_URL=${CVAT_API_URL:-https://app.cvat.ai/api}
      - CVAT_ORG_SLUG=${CVAT_ORG_SLUG:-}
      - DATABASE_URL=postgresql://${DB_USER:-letmeqc}:${DB_PASSWORD:-letmeqc}@db:5432/${DB_NAME:-letmeqc_dev}
      - WEBHOOK_SECRET=${WEBHOOK_SECRET:-dev_secret}
      - SERVER_HOST=0.0.0.0
      - SERVER_PORT=8000
      - ENVIRONMENT=development
    ports:
      - "8000:8000"
    volumes:
      - .:/app
      - /app/__pycache__
      - /app/.pytest_cache
      - /app/.mypy_cache
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped
    command: uvicorn app:app --host 0.0.0.0 --port 8000 --reload
    networks:
      - letmeqc_dev_network

  db:
    image: postgres:13
    container_name: letmeqc_db_dev
    environment:
      - POSTGRES_USER=${DB_USER:-letmeqc}
      - POSTGRES_PASSWORD=${DB_PASSWORD:-letmeqc}
      - POSTGRES_DB=${DB_NAME:-letmeqc_dev}
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-letmeqc} -d ${DB_NAME:-letmeqc_dev}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - letmeqc_dev_network

  pgadmin:
    image: dpage/pgadmin4
    container_name: letmeqc_pgadmin
    environment:
      - PGADMIN_DEFAULT_EMAIL=${PGADMIN_EMAIL:-admin@letmeqc.com}
      - PGADMIN_DEFAULT_PASSWORD=${PGADMIN_PASSWORD:-admin}
      - PGADMIN_CONFIG_SERVER_MODE=False
    ports:
      - "5050:80"
    depends_on:
      - db
    restart: unless-stopped
    volumes:
      - pgadmin_data:/var/lib/pgadmin
    networks:
      - letmeqc_dev_network

  redis:
    image: redis:6
    container_name: letmeqc_redis_dev
    ports:
      - "6379:6379"
    volumes:
      - redis_dev_data:/data
    restart: unless-stopped
    networks:
      - letmeqc_dev_network

volumes:
  postgres_dev_data:
  redis_dev_data:
  pgadmin_data:

networks:
  letmeqc_dev_network:
    driver: bridge
```

---

## 📄 Environment Configuration

### .env.example

```bash
# .env.example

# ====================
# CVAT Configuration
# ====================
CVAT_TOKEN=your_cvat_api_token_here
CVAT_API_URL=https://app.cvat.ai/api
CVAT_ORG_SLUG=your_organization_slug

# ====================
# Database Configuration
# ====================
DB_USER=letmeqc
DB_PASSWORD=letmeqc
DB_NAME=letmeqc
DATABASE_URL=postgresql://letmeqc:letmeqc@localhost:5432/letmeqc

# ====================
# Server Configuration
# ====================
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
ENVIRONMENT=development

# ====================
# Webhook Configuration
# ====================
WEBHOOK_SECRET=your_webhook_secret_here

# ====================
# QC Configuration (Default Values)
# ====================
MIN_BOX_AREA=100
IOU_THRESHOLD=0.95
DUPLICATE_IOU_THRESHOLD=0.98
MIN_POLYGON_POINTS=3
MAX_ASPECT_RATIO=10.0
MIN_ASPECT_RATIO=0.1
MASK_TOLERANCE=2.0
BBOX_TOLERANCE=2.0

# ====================
# pgAdmin Configuration (Dev only)
# ====================
PGADMIN_EMAIL=admin@letmeqc.com
PGADMIN_PASSWORD=admin
```

---

## 📦 requirements.txt

```text
# Core
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Database
sqlalchemy==2.0.23
alembic==1.13.0
psycopg2-binary==2.9.9

# HTTP Client
httpx==0.25.0

# CVAT Integration
opencv-python-headless==4.8.1.78

# Utilities
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx-mock==0.0.10

# Linting & Formatting
ruff==0.1.6
black==23.11.0
mypy==1.7.0

# Development
python-decouple==3.8

# Async Database Support
greenlet==3.0.1
```

### requirements-dev.txt

```text
# Include base requirements
-r requirements.txt

# Development tools
ipython==8.18.0
ipdb==0.13.13

# Code quality
flake8==6.1.0
isort==5.12.0

# Documentation
mkdocs==1.5.3
mkdocs-material==9.5.3

# Type checking extensions
pydantic-mypy==0.12.0
sqlalchemy2-stubs==0.0.2a43

# Testing
pytest-mock==3.12.0
factory-boy==3.3.0
```

---

## 📁 Database Session Configuration

```python
# database/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from src.config.settings import get_settings

settings = get_settings()

# Always use the DATABASE_URL from settings
# This works for both PostgreSQL (production) and SQLite (testing)
# but requires explicit configuration - no automatic fallback
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    # SQLite-specific settings only applied when using SQLite
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## 🚀 Usage Commands

### Development

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f backend

# Stop development environment
docker-compose -f docker-compose.dev.yml down

# Run database migrations
docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head

# Run tests
docker-compose -f docker-compose.dev.yml exec backend pytest

# Access pgAdmin
# Open http://localhost:5050 in browser
# Email: admin@letmeqc.com
# Password: admin

# Access API docs
# Open http://localhost:8000/docs in browser
```

### Production

```bash
# Build and start production environment
docker-compose -f docker-compose.yml up -d --build

# View logs
docker-compose logs -f backend

# Stop production environment
docker-compose down

# Run database migrations
docker-compose exec backend alembic upgrade head

# Update containers
docker-compose down
docker-compose pull
docker-compose up -d
```

---

## 🔧 Helper Scripts

### Wait for Database Script

```bash
# scripts/wait-for-db.sh
#!/bin/bash

set -e

host="$1"
shift
cmd="$@"

until psql -h "$host" -U "${DB_USER:-letmeqc}" -d "${DB_NAME:-letmeqc}" -c '\q' 2>/dev/null; do
  >&2 echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

>&2 echo "PostgreSQL is up - executing command"
exec $cmd
```

### Startup Script

```bash
# scripts/startup.sh
#!/bin/bash

# Wait for database to be ready
./wait-for-db.sh db python -c "print('Database is ready')"

# Run database migrations
alembic upgrade head

# Start the application
exec uvicorn app:app --host 0.0.0.0 --port 8000
```

---

## 🧪 Testing Docker Setup

### Test Commands

```bash
# Test backend container
curl http://localhost:8000/health

# Test database connection
docker-compose exec backend python -c "
from database.session import SessionLocal
from database.schemas.job import Job
db = SessionLocal()
result = db.query(Job).count()
print(f'Job count: {result}')
db.close()
"

# Test API endpoints
docker-compose exec backend python -c "
import httpx
response = httpx.get('http://localhost:8000/api/v1/jobs')
print(f'Status: {response.status_code}')
print(f'Response: {response.json()}')
"
```

---

## 🔒 Security Considerations

### Database Security
1. **Credentials:** Never hardcode credentials in Dockerfiles
2. **Environment Variables:** Use .env files with proper permissions
3. **Network Isolation:** Use separate Docker networks
4. **Volume Security:** Database volumes should be backed up regularly

### API Security
1. **HTTPS:** Always use HTTPS in production
2. **Authentication:** Consider adding authentication middleware
3. **CORS:** Configure CORS appropriately
4. **Rate Limiting:** Add rate limiting for public endpoints

### Production Checklist
- [ ] Database backups configured
- [ ] HTTPS/TLS certificates installed
- [ ] Monitoring and logging set up
- [ ] Health checks configured
- [ ] Resource limits set (CPU, memory)
- [ ] Auto-restart policies configured
- [ ] Security patches applied

---

## ✅ Acceptance Criteria

Phase 1 Docker Setup is **complete** when:

1. ✅ Dockerfiles created for backend
2. ✅ Docker Compose files created (dev and production)
3. ✅ Environment configuration (.env.example) created
4. ✅ Database session configuration implemented
5. ✅ requirements.txt and requirements-dev.txt updated
6. ✅ Helper scripts created
7. ✅ Development environment starts successfully
8. ✅ Database migrations work in containers
9. ✅ API is accessible in development environment

---

## 🔗 Related Documents

- [Phase 1 Overview](./phase-01-overview.md)
- [Phase 1 - Database Layer](./phase-01-database.md)
- [Phase 1 - API Layer](./phase-01-api.md)
- [Phase 1 - Services](./phase-01-services.md)
- [Main Development Plan](../README.md)
