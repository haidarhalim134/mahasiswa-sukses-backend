from pydantic import BaseModel, EmailStr
from enum import Enum

# add nim later
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    phone_number: str
    nim: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class Visibility(str, Enum):
    public = "public"
    private = "private"