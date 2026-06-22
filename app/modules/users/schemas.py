from typing import Optional
import re
from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserResponse(BaseModel):
    """User response model"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    full_name: str
    phone_number: str
    email: Optional[str] = None


class UserDetailResponse(BaseModel):
    """User detail response with role and profile info"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    full_name: str
    phone_number: str
    email: Optional[str] = None
    fcm_token: Optional[str] = None
    is_active: bool
    created_at: Optional[str] = None


class UserUpdate(BaseModel):
    """User update model"""
    model_config = ConfigDict(from_attributes=True)
    
    full_name: Optional[str] = Field(None, min_length=3, max_length=100)
    email: Optional[str] = Field(None, min_length=5, max_length=255)
    
    @field_validator("full_name", mode="before")
    @classmethod
    def validate_full_name(cls, v):
        if v and not re.match(r'^[a-zA-Z ]+$', v):
            raise ValueError("Full name must contain only letters and spaces")
        return v.strip() if v else None
    
    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, v):
        if v:
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(pattern, v):
                raise ValueError("Invalid email format")
        return v


class PasswordChangeRequest(BaseModel):
    """Request model for password change"""
    old_password: str = Field(..., min_length=6)
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
    def passwords_match(cls, v, info):
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class PasswordChangeResponse(BaseModel):
    """Response after password change"""
    message: str = "Password changed successfully"


class FcmTokenUpdateRequest(BaseModel):
    """Request model for FCM token update"""
    fcm_token: str = Field(..., min_length=10)


class FcmTokenUpdateResponse(BaseModel):
    """Response after FCM token update"""
    message: str = "FCM token updated successfully"


class UserListResponse(BaseModel):
    """Response for user list"""
    users: list[UserResponse]
    total: int
    skip: int
    limit: int


class UserSearchResponse(BaseModel):
    """Response for user search"""
    results: list[UserResponse]
    total: int


class AccountDeletionRequest(BaseModel):
    """Request model for account deletion"""
    password: str = Field(..., min_length=6, description="Confirm password for deletion")


class AccountDeletionResponse(BaseModel):
    """Response after account deletion"""
    message: str = "Account deleted successfully"
