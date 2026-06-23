from datetime import date
import re
from pydantic import BaseModel, EmailStr, Field, field_validator
from enum import Enum

from app.users.models import User

class RegisterRequest(BaseModel):
    email: EmailStr

    username: str = Field(
        min_length=1,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="Username can only contain letters, numbers, and underscores."
    )
    password: str = Field(
        min_length=8,
        description="Password must be at least 8 characters long and contain at least one letter, one number, and one special character."
    )
    
    phone_number: str = Field(
        pattern=r"^\+?\d{9,20}$",
        description="International or local format, 9 to 20 digits."
    )
    
    nim: str | None = Field(
        default=None,
        pattern=r"^\d+$",
        description="NIM must contain only digits"
    )
    
    full_name: str
    birth_date: date | None = None

    @field_validator("password")
    def validate_password_complexity(cls, v):
        pattern = r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&_.]).{8,}$"
        if not re.match(pattern, v):
            raise ValueError(
                "Password must contain at least one letter, one number, and one special character"
            )
        return v

    @field_validator("username")
    def strip_username(cls, v: str) -> str:
        return v.strip()

class LoginRequest(BaseModel):
    email_or_username: str
    password: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr

class UpdatePasswordRequest(BaseModel):
    access_token: str
    password: str = Field(min_length=8)

    @field_validator("password")
    def validate_password_complexity(cls, v):
        # at least one letter: (?=.*[A-Za-z])
        # at least one digit: (?=.*\d)
        # at least one special character: (?=.*[@$!%*#?&])
        # at least 8 char long: {8,}
        pattern = r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$"
        
        if not re.match(pattern, v):
            raise ValueError(
                "Password must contain at least one letter, one number, and one special character"
            )
        return v

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: User

class Visibility(str, Enum):
    public = "public"
    private = "private"

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class TokenRefreshResponse(BaseModel):
    access_token: str
    refresh_token: str