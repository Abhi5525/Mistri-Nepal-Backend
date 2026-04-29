# QUICK-REFERENCE.md

# ⚡ Quick Reference Guide - FastAPI Migration

## 📌 Essential Commands

### Project Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install fastapi uvicorn[standard] sqlalchemy asyncpg
pip install python-jose[cryptography] passlib[bcrypt]
pip install pydantic[email] python-multipart
pip install aioredis firebase-admin httpx

# Save requirements
pip freeze > requirements.txt
```

### Database
```bash
# Start PostgreSQL
sudo systemctl start postgresql  # Linux
brew services start postgresql   # Mac

# Connect to database
psql -U postgres -d service_manpower

# Run schema
psql -U postgres -d service_manpower -f schema.sql

# Check tables
\dt

# Exit
\q
```

### Redis
```bash
# Start Redis
redis-server

# Test connection
redis-cli ping  # Should return PONG
```

### Run FastAPI
```bash
# Development mode
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker
```bash
# Build and run
docker-compose up -d --build

# View logs
docker-compose logs -f api

# Stop
docker-compose down

# Rebuild
docker-compose up -d --build --force-recreate
```

---
