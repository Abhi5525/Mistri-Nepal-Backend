from typing import Optional

from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    """User response model"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    full_name: str
    phone_number: str
    email: Optional[str] = None

class UserUpdate(BaseModel):
    """User update model"""
    model_config = ConfigDict(from_attributes=True)
    
    full_name: str
    phone_number: str
    email: Optional[str] = None
