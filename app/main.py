from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.permissions import require_user
import app.auth.routes as auth
from app.core.config import settings
from app.users.models import Role
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Mahasiswa Sukses Backend")

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)

@app.get("/")
async def health():
    return {"status": "ok"}


@app.get("/api/v1/me")
async def get_profile(
    current_user = Depends(require_user())
):
    return {
        "message": "Authenticated user",
        "user_id": str(current_user.id),
        "email": current_user.email,
        "role": current_user.role.name
    }


@app.get("/api/v1/admin/dashboard")
async def admin_dashboard(
    current_user = Depends(require_user(role=Role.admin))
):
    return {
        "message": "Admin access granted",
        "admin_id": str(current_user.id)
    }