from datetime import date
import re
from pydantic import BaseModel, EmailStr, Field, field_validator
from enum import Enum

from app.users.models import User

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str = Field(min_length=8)
    phone_number: str
    nim: str | None = None
    full_name: str
    birth_date: date | None = None

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

    @field_validator("phone_number")
    def validate_phone(cls, v):
        if not re.match(r"^\+?\d{9,20}$", v):
            raise ValueError("Invalid phone number format")
        return v

    @field_validator("nim")
    def validate_nim(cls, v):
        if v is None:
            return v
        if not v.isdigit():
            raise ValueError("NIM must contain only digits")
        return v

    @field_validator("username")
    def validate_username(cls, v):
        v = v.strip()
        
        if not v:
            raise ValueError("Username cannot be empty")

        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username can only contain letters, numbers, and underscores (no spaces or special characters)")
            
        return v

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