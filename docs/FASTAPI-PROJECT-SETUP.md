# FASTAPI-PROJECT-SETUP.md

# 🚀 Complete FastAPI Project Setup Guide

## 📋 Table of Contents

1. [Project Structure](#project-structure)
2. [Environment Setup](#environment-setup)
3. [Dependencies Installation](#dependencies-installation)
4. [Configuration Files](#configuration-files)
5. [Core Application Files](#core-application-files)
6. [Database Setup](#database-setup)
7. [Running the Application](#running-the-application)
8. [Testing Setup](#testing-setup)
9. [Next Steps](#next-steps)

---

## 📁 Project Structure

Create this directory structure for your Service Manpower FastAPI backend:

```
service_manpower_api/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Configuration settings
│   ├── database.py             # Database connection
│   │
│   ├── core/                   # Core utilities
│   │   ├── __init__.py
│   │   ├── security.py         # JWT, password hashing
│   │   ├── dependencies.py     # Auth dependencies
│   │   └── exceptions.py       # Custom exceptions
│   │
│   ├── models/                 # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── professional.py
│   │   ├── booking.py
│   │   ├── payment.py
│   │   ├── review.py
│   │   ├── skill.py
│   │   └── professional_skill.py
│   │
│   ├── schemas/                # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── professional.py
│   │   ├── booking.py
│   │   ├── payment.py
│   │   └── review.py
│   │
│   ├── api/                    # API routes
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── professionals.py
│   │   ├── bookings.py
│   │   ├── payments.py
│   │   ├── location.py
│   │   ├── reviews.py
│   │   └── admin.py
│   │
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── professional_service.py
│   │   ├── booking_service.py
│   │   ├── payment_service.py
│   │   ├── location_service.py
│   │   ├── notification_service.py
│   │   └── file_service.py
│   │
│   ├── websockets/             # WebSocket handlers
│   │   ├── __init__.py
│   │   ├── chat.py
│   │   └── tracking.py
│   │
│   ├── middleware/             # Custom middleware
│   │   ├── __init__.py
│   │   └── logging.py
│   │
│   └── utils/                  # Utility functions
│       ├── __init__.py
│       ├── validators.py
│       └── helpers.py
│
├── tests/                      # Test files
│   ├── __init__.py
│   ├── conftest.py            # Test fixtures
│   ├── test_auth.py
│   ├── test_users.py
│   ├── test_professionals.py
│   └── test_bookings.py
│
├── uploads/                    # File uploads (KYC docs)
│   ├── profile_pictures/
│   └── citizenship/
│       ├── front/
│       └── back/
│
├── alembic/                    # Database migrations
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
│
├── .env                        # Environment variables
├── .env.example               # Example environment file
├── .gitignore
├── requirements.txt
├── requirements-dev.txt
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
└── README.md
```

---

## 🛠️ Environment Setup

### Step 1: Create Project Directory

```bash
# Navigate to your workspace
cd "d:\Sem Project\Service_Manpower"

# Create new directory for FastAPI backend
mkdir service_manpower_api
cd service_manpower_api
```

### Step 2: Initialize Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate
```

You should see `(venv)` prefix in your terminal after activation.

### Step 3: Verify Python Version

```bash
python --version
# Should be Python 3.10 or higher
```

---

## 📦 Dependencies Installation

### Create `requirements.txt`

```txt
# Core Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
gunicorn==21.2.0

# Database
sqlalchemy==2.0.25
asyncpg==0.29.0
alembic==1.13.1
psycopg2-binary==2.9.9

# Authentication & Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
bcrypt==4.1.2
python-multipart==0.0.6

# Validation
pydantic==2.5.3
pydantic-settings==2.1.0
email-validator==2.1.0

# Caching
redis==5.0.1
aioredis==2.0.1

# HTTP Client
httpx==0.26.0

# File Handling
python-magic==0.4.27
Pillow==10.2.0

# Push Notifications
firebase-admin==6.3.0

# WebSocket
websockets==12.0

# Monitoring
prometheus-fastapi-instrumentator==6.1.0

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
```

### Create `requirements-dev.txt`

```txt
-r requirements.txt

# Development Tools
black==23.12.1
flake8==7.0.0
isort==5.13.2
mypy==1.8.0
pre-commit==3.6.0

# Debugging
ipdb==0.13.13
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuration Files

### `.env.example`

```env
# Application
APP_NAME="Service Manpower API"
APP_VERSION="1.0.0"
DEBUG=True

# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/service_manpower_fastapi

# Redis
REDIS_URL=redis://localhost:6379

# JWT Settings
SECRET_KEY=your-super-secret-key-change-this-in-production-min-64-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Security
BCRYPT_ROUNDS=12

# CORS
ALLOWED_ORIGINS=["*"]

# File Upload
MAX_UPLOAD_SIZE=5242880
UPLOAD_DIR=./uploads

# Firebase (for push notifications)
FIREBASE_CREDENTIALS_PATH=./serviceAccountKey.json

# eSewa Payment
ESEWA_MERCHANT_CODE=EPAYTEST
ESEWA_SECRET_KEY=8gBm/:&EnhH.1/q
ESEWA_BASE_URL=https://rc-epay.esewa.com.np/api/epay/main/v2/form
```

### Create `.env` File

```bash
# Windows PowerShell
Copy-Item .env.example .env

# Then edit with your actual values
notepad .env
```

**Important:** Change these values in `.env`:
- `DATABASE_URL`: Your PostgreSQL connection string
- `SECRET_KEY`: Generate a strong random key (min 64 characters)
- `ALLOWED_ORIGINS`: Your Flutter app URLs in production

### `.gitignore`

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
ENV/
env/

# Environment variables
.env

# IDE
.vscode/
.idea/
*.swp
*.swo

# Uploads
uploads/*
!uploads/.gitkeep

# Database
*.db
*.sqlite3

# Testing
.pytest_cache/
.coverage
htmlcov/

# OS
.DS_Store
Thumbs.db

# Logs
*.log
```

---

## 🏗️ Core Application Files

### `app/__init__.py`

```python
"""Service Manpower API - FastAPI Backend"""

__version__ = "1.0.0"
```

### `app/config.py`

```python
from pydantic_settings import BaseSettings
from typing import List
from pydantic import field_validator

class Settings(BaseSettings):
    """Application configuration settings"""
    
    # App
    APP_NAME: str = "Service Manpower API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Security
    BCRYPT_ROUNDS: int = 12
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 5242880  # 5MB
    UPLOAD_DIR: str = "./uploads"
    
    # Firebase
    FIREBASE_CREDENTIALS_PATH: str = "./serviceAccountKey.json"
    
    # eSewa
    ESEWA_MERCHANT_CODE: str = "EPAYTEST"
    ESEWA_SECRET_KEY: str = "8gBm/:&EnhH.1/q"
    ESEWA_BASE_URL: str = "https://rc-epay.esewa.com.np/api/epay/main/v2/form"
    
    @field_validator('ALLOWED_ORIGINS', mode='before')
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.strip('[]').split(',')]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### `app/database.py`

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600
)

# Create session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Base class for models
Base = declarative_base()

# Dependency to get DB session
async def get_db():
    """Database session dependency"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

### `app/core/__init__.py`

```python
"""Core utilities module"""
```

### `app/core/security.py`

```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from app.config import settings
import re

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token with longer expiry"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> dict:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

def validate_phone_number(phone: str) -> bool:
    """Validate Nepal phone number format (98XXXXXXXX)"""
    pattern = r'^98\d{8}$'
    return bool(re.match(pattern, phone))
```

### `app/core/dependencies.py`

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.core.security import decode_token

# OAuth2 scheme for extracting token from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_token(token)
        
        # Check token type
        if payload.get("type") != "access":
            raise credentials_exception
        
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
            
    except HTTPException:
        raise
    except Exception:
        raise credentials_exception
    
    # Fetch user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    
    return user

async def get_current_active_professional(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current user and verify they are an approved professional"""
    if not current_user.is_professional:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a professional account"
        )
    
    # Check verification status
    from app.models.professional import ProfessionalProfile
    result = await db.execute(
        select(ProfessionalProfile).where(ProfessionalProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile or profile.verification_status != 'APPROVED':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Professional account not approved"
        )
    
    return current_user

async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current user and verify they are admin/staff"""
    if not (current_user.is_staff or current_user.is_superuser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return current_user
```

### `app/models/__init__.py`

```python
"""Database models"""
from app.models.user import User
from app.models.professional import ProfessionalProfile
from app.models.booking import Booking
from app.models.payment import Payment
from app.models.review import Review
from app.models.skill import Skill
from app.models.professional_skill import ProfessionalSkill
```

### `app/models/user.py`

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(10), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    full_name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_client = Column(Boolean, default=True)
    is_professional = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_staff = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    fcm_token = Column(String(255), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<User {self.phone_number}>"
```

### `app/schemas/__init__.py`

```python
"""Pydantic schemas"""
```

### `app/api/__init__.py`

```python
"""API routers"""
```

### `app/services/__init__.py`

```python
"""Business logic services"""
```

### `app/websockets/__init__.py`

```python
"""WebSocket handlers"""
```

### `app/middleware/__init__.py`

```python
"""Custom middleware"""
```

### `app/utils/__init__.py`

```python
"""Utility functions"""
```

### `app/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings

# Import API routers (create these files next)
# from app.api import auth, users, professionals, bookings, payments, location, reviews, admin

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Service Manpower API - Connecting clients with local professionals",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware for mobile app
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers (uncomment after creating router files)
# app.include_router(auth.router)
# app.include_router(users.router)
# app.include_router(professionals.router)
# app.include_router(bookings.router)
# app.include_router(payments.router)
# app.include_router(location.router)
# app.include_router(reviews.router)
# app.include_router(admin.router)

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION
    }

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "docs": "/docs",
        "redoc": "/redoc"
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
```

---

## 🗄️ Database Setup

### Step 1: Create PostgreSQL Database

```bash
# Open PostgreSQL command line
psql -U postgres

# Inside psql, run:
CREATE DATABASE service_manpower_fastapi;

# Optional: Create dedicated user
CREATE USER fastapi_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE service_manpower_fastapi TO fastapi_user;

# Exit psql
\q
```

### Step 2: Update `.env` with Database URL

```env
DATABASE_URL=postgresql+asyncpg://postgres:your_password@localhost:5432/service_manpower_fastapi
```

### Step 3: Run Database Schema

Refer to `02-DATABASE-SCHEMA.md` in your project root for the complete SQL schema.

```bash
# Extract SQL from the markdown file and run:
psql -U postgres -d service_manpower_fastapi -f schema.sql
```

Or manually create tables following the schema guide.

---

## 🧪 Testing Setup

### `tests/__init__.py`

```python
"""Test suite for Service Manpower API"""
```

### `tests/conftest.py`

```python
import pytest
from httpx import AsyncClient
from app.main import app
from app.database import Base, engine

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def client():
    """Test client fixture"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    """Setup test database"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
```

---

## 🚀 Running the Application

### Start Development Server

```bash
# Make sure virtual environment is activated
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux/Mac

# Navigate to project root
cd "d:\Sem Project\Service_Manpower\service_manpower_api"

# Start server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Access Your API

Open your browser and visit:
- **Swagger UI (Interactive Docs)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **Root**: http://localhost:8000/

You should see the interactive API documentation with your health check and root endpoints!

---

## ✅ Verification Checklist

Run these commands to verify your setup:

```bash
# 1. Check Python version
python --version
# Expected: Python 3.10+

# 2. Check installed packages
pip list | findstr fastapi  # Windows
# or
pip list | grep fastapi     # Linux/Mac

# 3. Test imports
python -c "from app.main import app; print('✅ Imports working!')"

# 4. Test database connection
python -c "from app.database import engine; print('✅ Database connection ready!')"

# 5. Run tests (will show no tests initially, that's OK)
pytest tests/ -v
```

---

## 📝 Next Steps - Building Your API

Now that your project structure is set up, follow this order to build your API:

### Phase 1: Authentication (Week 1-2)
1. Read `03-AUTHENTICATION.md` from your guides
2. Create `app/schemas/auth.py` - Authentication schemas
3. Create `app/services/auth_service.py` - Auth business logic
4. Create `app/api/auth.py` - Auth endpoints (register, login, refresh)
5. Test authentication flow

### Phase 2: User Management (Week 2)
1. Read `04-USER-MANAGEMENT.md`
2. Create `app/schemas/user.py` - User schemas
3. Create `app/services/user_service.py` - User operations
4. Create `app/api/users.py` - User endpoints
5. Implement profile CRUD operations

### Phase 3: Professional System (Week 2-3)
1. Read `05-PROFESSIONAL-REGISTRATION.md`
2. Create remaining models (`professional.py`, `skill.py`, etc.)
3. Create professional schemas and services
4. Implement KYC document upload
5. Build admin verification workflow

### Phase 4: Location Services (Week 3)
1. Read `06-LOCATION-SERVICES.md`
2. Create `app/services/location_service.py`
3. Create `app/api/location.py`
4. Implement geospatial queries
5. Test nearby professional search

### Phase 5: Booking System (Week 3-4)
1. Read `07-BOOKING-SYSTEM.md`
2. Create booking models, schemas, services
3. Implement time slot generation
4. Add conflict detection
5. Build booking lifecycle management

### Phase 6: Payment Integration (Week 4)
1. Read `08-PAYMENT-INTEGRATION.md`
2. Create payment service
3. Integrate eSewa gateway
4. Implement payment verification
5. Test payment flow

### Phase 7+: Advanced Features
Continue with real-time features, performance optimization, etc. following your guides.

---

## 🆘 Troubleshooting

### Common Issues and Solutions

#### 1. Import Error
```
ModuleNotFoundError: No module named 'xxx'
```
**Solution:**
```bash
pip install xxx
```

#### 2. Database Connection Failed
```
could not connect to server: Connection refused
```
**Solution:**
```bash
# Check if PostgreSQL is running
# Windows:
pg_ctl status

# Linux:
sudo systemctl status postgresql

# Verify DATABASE_URL in .env matches your setup
```

#### 3. Port Already in Use
```
Address already in use
```
**Solution:**
```bash
# Use different port
uvicorn app.main:app --reload --port 8001

# Or kill process using port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -ti:8000 | xargs kill -9
```

#### 4. CORS Error in Mobile App
```
No 'Access-Control-Allow-Origin' header
```
**Solution:**
Update `ALLOWED_ORIGINS` in `.env`:
```env
ALLOWED_ORIGINS=["http://localhost:3000","http://192.168.1.100:8080"]
```

#### 5. JWT Token Invalid
```
Invalid or expired token
```
**Solution:**
- Check `SECRET_KEY` in `.env` hasn't changed
- Verify token hasn't expired (default 30 minutes)
- Ensure token type is "access" not "refresh"

#### 6. Virtual Environment Not Activated
```
Command 'uvicorn' not found
```
**Solution:**
```bash
# Reactivate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

---

## 📊 Performance Tips from Day 1

1. **Use Async Everywhere**: All database operations should be async
2. **Enable Connection Pooling**: Already configured in `database.py`
3. **Add Logging**: Monitor slow requests
4. **Set Up Caching Early**: Redis integration from start
5. **Write Tests**: Test each feature as you build it

---

## 🎯 Quick Reference Commands

```bash
# Start development server
uvicorn app.main:app --reload

# Start production server
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Run tests
pytest tests/ -v

# Check code formatting
black app/

# Sort imports
isort app/

# Run linter
flake8 app/

# Type checking
mypy app/

# View dependencies
pip list

# Export dependencies
pip freeze > requirements.txt
```

---

## 📞 Getting Help

### Resources
- **FastAPI Official Docs**: https://fastapi.tiangolo.com
- **Your Migration Guides**: Located in `d:\Sem Project\Service_Manpower\`
- **Stack Overflow**: Tag questions with `fastapi`, `python`, `asyncio`
- **FastAPI Discord**: https://discord.gg/VQjSZaeJmf

### When Stuck
1. Check the specific guide file for detailed examples
2. Search FastAPI official documentation
3. Look for similar issues on GitHub
4. Ask in community forums
5. Take a break and return with fresh eyes

---

## 🎉 Congratulations!

Your FastAPI project is now set up with:
- ✅ Professional directory structure
- ✅ Virtual environment configured
- ✅ All dependencies installed
- ✅ Configuration files ready
- ✅ Core application files created
- ✅ Database connection established
- ✅ Testing framework in place
- ✅ Development server running

**You're ready to start building!** 🚀

Follow the migration guides in order, starting with `03-AUTHENTICATION.md`, and build your API systematically.

Good luck with your Service Manpower FastAPI backend! 💪

---

*Created for Service Manpower Project*  
*FastAPI Backend Migration Guide*  
*Version 1.0*
