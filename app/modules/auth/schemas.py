from typing import Optional
import re
from pydantic import BaseModel, ConfigDict, Field, field_validator

class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=3, max_length=100)
    phone_number: str = Field(..., min_length=10, max_length=10)
    password: str = Field(..., min_length=6, max_length=100)
    confirm_password: str

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v):
        if not re.match(r'^[a-zA-Z ]+$', v):
            raise ValueError("Full name must contain only letters and spaces")
        return v

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v):
        if not v.isdigit():
            raise ValueError("Phone must contain only digits")
        if not re.match(r"^98\d{8}$", v):
            raise ValueError("Must be a valid Nepal number starting with 98")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if not (
            any(c.islower() for c in v) and
            any(c.isupper() for c in v) and
            any(c.isdigit() for c in v)
        ):
            raise ValueError("Password must contain upper, lower, and number")
        return v

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v
    
class UserLogin(BaseModel):
    phone_number: str = Field(..., min_length=10, max_length=10)
    password: str = Field(..., min_length=6, max_length=100)

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v):
        if not v.isdigit():
            raise ValueError("Phone must contain only digits")
        if not re.match(r"^98\d{8}$", v):
            raise ValueError("Must be a valid Nepal number starting with 98")
        return v
    
class TokenResponse(BaseModel):
    """Response model for authentication tokens"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    """Data contained in JWT token payload"""
    user_id: Optional[int] = None
    full_name: Optional[str] = None 
    is_client: Optional[bool] = True
    is_professional: Optional[bool] = False
    phone_number: Optional[str] = None

class UserResponse(BaseModel):
    """User response model"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    phone_number: str
    email: Optional[str] = None
    is_client: bool = True
    is_professional: bool = False
    is_active: bool = True

class UserUpdate(BaseModel):
    """User update model"""
    model_config = ConfigDict(from_attributes=True)
    
    full_name: str
    phone_number: str
    email: Optional[str] = None
    
class PasswordChange(BaseModel):
    """Model for changing user password"""
    old_password: str 
    new_password: str = Field(..., min_length=6, max_length=100)
    confirm_new_password: str 

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v):
        if not (
            any(c.islower() for c in v) and
            any(c.isupper() for c in v) and
            any(c.isdigit() for c in v)
        ):
            raise ValueError("Password must contain upper, lower, and number")
        return v

    @field_validator("confirm_new_password")
    @classmethod
    def new_passwords_match(cls, v, info):
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("New passwords do not match")
        return v
    
class FcmTokenUpdate(BaseModel):
    """Model for updating FCM token"""
    fcm_token: str