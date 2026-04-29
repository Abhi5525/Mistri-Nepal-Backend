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
