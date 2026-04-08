from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

import app.auth.routes as auth
from app.core.scheduler import get_scheduler
import app.users.routes as user
import app.modules.community.routes as community
import app.modules.gamification.routes as gamification
import app.modules.progress_tracking.routes as progress_tracking
import app.modules.quiz.routes as quiz
import app.modules.certificate.routes as certificate
import app.modules.task.routes as task

from app.auth.permissions import get_current_user, require_user
from app.core.config import settings
from app.users.models import Role
from dotenv import load_dotenv
import traceback
import os

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    base_url = os.getenv("BASE_URL")
    if not base_url:
        base_url = os.getenv("VERCEL_PROJECT_PRODUCTION_URL")
        if base_url: 
            base_url = "https://" + base_url
    
    # silent skip for now
    if base_url:
        scheduler = get_scheduler()
        scheduler.schedule_daily(f"{base_url}/api/v1/task/daily", settings.task_token)
        scheduler.schedule_weekly(f"{base_url}/api/v1/task/weekly", settings.task_token)
    yield


app = FastAPI(title="Mahasiswa Sukses Backend", lifespan=lifespan)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    response = {"error": "Internal Server Error"}

    if settings.show_error_details:
        response["error_name"] = exc.__class__.__name__
        response["detail"] = str(exc)
        response["traceback"] = traceback.format_exc()

    return JSONResponse(status_code=500, content=response)


app.include_router(auth.router)
app.include_router(user.router)
app.include_router(community.router)
app.include_router(gamification.router)
app.include_router(progress_tracking.router)
app.include_router(quiz.router)
app.include_router(certificate.router)
app.include_router(task.router)

@app.get("/")
async def health():
    return {"status": "ok"}


@app.get("/api/v1/me", include_in_schema=False)
async def get_profile(
    current_user = Depends(get_current_user)
):
    return {
        "message": "Authenticated user",
        "user_id": str(current_user.id),
        "email": current_user.email,
        "role": current_user.role.name
    }


@app.get("/api/v1/admin/dashboard", include_in_schema=False)
async def admin_dashboard(
    current_user = Depends(require_user(role=Role.admin))
):
    return {
        "message": "Admin access granted",
        "admin_id": str(current_user.id)
    }