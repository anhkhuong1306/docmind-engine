import uuid

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

class UserRegisterRequest(BaseModel):
    """Schema for user registration request."""
    
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=100)
    
class UserLoginRequest(BaseModel):
    """Schema for user login request."""
    
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
    
class TokenResponse(BaseModel):
    """Schema for token response."""
    
    access_token: str
    token_type: str = "bearer"
    
class UserResponse(BaseModel):
    """Schema for user response."""
    
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime
    