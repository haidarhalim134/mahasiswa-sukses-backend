from datetime import date
import re
from pydantic import BaseModel, EmailStr, Field, field_validator
from enum import Enum

from app.users.models import User

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    phone_number: str
    # nim: str
    full_name: str
    birth_date: date

    @field_validator("phone_number")
    def validate_phone(cls, v):
        if not re.match(r"^\+?\d{9,20}$", v):
            raise ValueError("Invalid phone number format")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr

class UpdatePasswordRequest(BaseModel):
    access_token: str
    password: str = Field(min_length=8)

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