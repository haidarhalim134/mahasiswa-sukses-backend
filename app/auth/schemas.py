from datetime import date
from pydantic import BaseModel, EmailStr, Field
from enum import Enum

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    phone_number: str
    nim: str
    full_name: str
    birth_date: date


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

class Visibility(str, Enum):
    public = "public"
    private = "private"