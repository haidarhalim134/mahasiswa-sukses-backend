from pydantic import BaseModel, EmailStr
from enum import Enum

# add nim later
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr

class Visibility(str, Enum):
    public = "public"
    private = "private"