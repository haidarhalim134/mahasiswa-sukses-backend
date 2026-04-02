from pydantic import BaseModel, EmailStr, Field
from enum import Enum

# add nim later
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    phone_number: str
    nim: str


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