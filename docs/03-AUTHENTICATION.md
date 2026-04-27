# 03-AUTHENTICATION.md

# Authentication System - JWT-Based with FastAPI

## 📋 Overview

This guide covers implementing secure JWT-based authentication for your FastAPI backend, replacing Django's session-based auth. This is optimized for mobile app integration.

---

## 🛠️ Required Packages

```bash
pip install fastapi
pip install python-jose[cryptography]  # JWT encoding/decoding
pip install passlib[bcrypt]  # Password hashing
pip install python-multipart  # Form data parsing
pip install pydantic[email]  # Email validation
pip install asyncpg  # Async PostgreSQL driver
pip install databases  # Database abstraction
```

**requirements.txt:**
```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
pydantic[email]==2.5.3
asyncpg==0.29.0
databases==0.8.0
bcrypt==4.1.2
```

---

## 🔐 Project Structure

```
service_manpower_api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database connection
│   ├── models/              # SQLAlchemy models
│   │   ├── __init__.py
│   │   └── user.py
│   ├── schemas/             # Pydantic schemas
│   │   ├── __init__.py
│   │   └── auth.py
│   ├── core/                # Core utilities
│   │   ├── __init__.py
│   │   ├── security.py      # Password hashing & JWT
│   │   └── dependencies.py  # Auth dependencies
│   ├── api/                 # API routes
│   │   ├── __init__.py
│   │   └── auth.py          # Authentication endpoints
│   └── services/            # Business logic
│       ├── __init__.py
│       └── auth_service.py
├── .env                     # Environment variables
└── requirements.txt
```

---

## ⚙️ Configuration

### `.env` File

```env
# Application
APP_NAME="Service Manpower API"
APP_VERSION="1.0.0"
DEBUG=True

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/service_manpower_fastapi

# JWT Settings
SECRET_KEY=your-super-secret-key-change-in-production-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Security
BCRYPT_ROUNDS=12

# CORS (for mobile app)
ALLOWED_ORIGINS=["*"]
```

### `app/config.py`

```python
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Service Manpower API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Security
    BCRYPT_ROUNDS: int = 12
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

---

## 🔑 Core Security Module

### `app/core/security.py`

```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from app.config import settings

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
    import re
    pattern = r'^98\d{8}$'
    return bool(re.match(pattern, phone))
```

---

## 📊 Database Models

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
    max_overflow=20
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

---

## 📝 Pydantic Schemas

### `app/schemas/auth.py`

```python
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime

class UserRegister(BaseModel):
    """Schema for user registration"""
    full_name: str = Field(..., min_length=3, max_length=100)
    phone_number: str = Field(..., min_length=10, max_length=10)
    password: str = Field(..., min_length=8)
    confirm_password: str
    
    @validator('phone_number')
    def validate_phone(cls, v):
        from app.core.security import validate_phone_number
        if not validate_phone_number(v):
            raise ValueError('Phone number must be 10 digits starting with 98')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isalpha() for c in v):
            raise ValueError('Password must contain at least one letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class UserLogin(BaseModel):
    """Schema for user login"""
    phone_number: str = Field(..., min_length=10, max_length=10)
    password: str
    
    @validator('phone_number')
    def validate_phone(cls, v):
        from app.core.security import validate_phone_number
        if not validate_phone_number(v):
            raise ValueError('Invalid phone number format')
        return v

class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    """Token payload schema"""
    user_id: Optional[int] = None
    phone_number: Optional[str] = None
    is_professional: Optional[bool] = False

class UserResponse(BaseModel):
    """User profile response"""
    id: int
    phone_number: str
    full_name: str
    email: Optional[str] = None
    is_client: bool
    is_professional: bool
    is_active: bool
    
    class Config:
        from_attributes = True

class PasswordChangeRequest(BaseModel):
    """Schema for password change"""
    old_password: str
    new_password: str = Field(..., min_length=8)
    confirm_new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isalpha() for c in v):
            raise ValueError('Password must contain at least one letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v
    
    @validator('confirm_new_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

class FCMTokenUpdate(BaseModel):
    """Schema for updating FCM token"""
    fcm_token: str
```

---

## 🔧 Authentication Dependencies

### `app/core/dependencies.py`

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.core.security import decode_token
from sqlalchemy import select

# OAuth2 scheme for extracting token from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token
    Use this dependency to protect routes that require authentication
    """
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
    """
    Get current user and verify they are an approved professional
    Use for professional-only endpoints
    """
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
    """
    Get current user and verify they are admin/staff
    Use for admin-only endpoints
    """
    if not (current_user.is_staff or current_user.is_superuser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return current_user
```

---

## 🚀 Authentication Service

### `app/services/auth_service.py`

```python
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    validate_phone_number
)
from fastapi import HTTPException, status

class AuthService:
    """Authentication service handling user registration, login, and token management"""
    
    @staticmethod
    async def register_user(db: AsyncSession, user_data: UserRegister) -> dict:
        """Register a new user"""
        
        # Check if phone number already exists
        result = await db.execute(
            select(User).where(User.phone_number == user_data.phone_number)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Phone number already registered"
            )
        
        # Check if email already exists (if provided)
        if user_data.email:
            result = await db.execute(
                select(User).where(User.email == user_data.email)
            )
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already registered"
                )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        
        new_user = User(
            phone_number=user_data.phone_number,
            full_name=user_data.full_name,
            password_hash=hashed_password,
            is_client=True,
            is_professional=False,
            is_active=True
        )
        
        db.add(new_user)
        await db.flush()  # Get the user ID
        await db.refresh(new_user)
        
        # Generate tokens
        access_token = create_access_token(
            data={"user_id": new_user.id, "phone_number": new_user.phone_number}
        )
        refresh_token = create_refresh_token(
            data={"user_id": new_user.id}
        )
        
        return {
            "user": new_user,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 1800  # 30 minutes in seconds
        }
    
    @staticmethod
    async def login_user(db: AsyncSession, login_data: UserLogin) -> dict:
        """Authenticate user and return tokens"""
        
        # Find user by phone number
        result = await db.execute(
            select(User).where(User.phone_number == login_data.phone_number)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid phone number or password"
            )
        
        # Verify password
        if not verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid phone number or password"
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated. Contact support."
            )
        
        # Update last login
        user.last_login = datetime.utcnow()
        await db.flush()
        
        # Generate tokens
        access_token = create_access_token(
            data={
                "user_id": user.id,
                "phone_number": user.phone_number,
                "is_professional": user.is_professional
            }
        )
        refresh_token = create_refresh_token(
            data={"user_id": user.id}
        )
        
        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 1800
        }
    
    @staticmethod
    async def refresh_access_token(db: AsyncSession, refresh_token: str) -> dict:
        """Refresh access token using refresh token"""
        
        try:
            from app.core.security import decode_token
            payload = decode_token(refresh_token)
            
            # Check token type
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            user_id = payload.get("user_id")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            # Fetch user
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive"
                )
            
            # Generate new access token
            new_access_token = create_access_token(
                data={
                    "user_id": user.id,
                    "phone_number": user.phone_number,
                    "is_professional": user.is_professional
                }
            )
            
            return {
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": 1800
            }
            
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
    
    @staticmethod
    async def change_password(
        db: AsyncSession,
        user_id: int,
        old_password: str,
        new_password: str
    ) -> dict:
        """Change user password"""
        
        # Fetch user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify old password
        if not verify_password(old_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )
        
        # Hash and update new password
        user.password_hash = get_password_hash(new_password)
        await db.flush()
        
        return {"message": "Password changed successfully"}
    
    @staticmethod
    async def update_fcm_token(
        db: AsyncSession,
        user_id: int,
        fcm_token: str
    ) -> dict:
        """Update Firebase Cloud Messaging token for push notifications"""
        
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.fcm_token = fcm_token
        await db.flush()
        
        return {"message": "FCM token updated successfully"}
```

---

## 🌐 API Endpoints

### `app/api/auth.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.auth import (
    UserRegister, UserLogin, TokenResponse, UserResponse,
    PasswordChangeRequest, FCMTokenUpdate