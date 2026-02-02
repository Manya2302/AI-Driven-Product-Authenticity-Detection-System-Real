"""
User model for database
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"
    USER = "user"

class User(BaseModel):
    """Base user model"""
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.USER
    is_active: bool = True
    is_blocked: bool = False

class UserCreate(BaseModel):
    """User creation model"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=100)
    role: UserRole = UserRole.USER

class UserInDB(User):
    """User model as stored in database"""
    id: Optional[str] = Field(None, alias="_id")
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class UserUpdate(BaseModel):
    """User update model"""
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_blocked: Optional[bool] = None

class UserResponse(BaseModel):
    """User response model (without sensitive data)"""
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    is_blocked: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class LoginRequest(BaseModel):
    """Login request model"""
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    """Login response model"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class TokenData(BaseModel):
    """Token payload data"""
    email: Optional[str] = None
    role: Optional[str] = None
