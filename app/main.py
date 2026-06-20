from contextlib import asynccontextmanager
import json
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from supabase_auth.errors import AuthInvalidJwtError

import app.auth.routes as auth
from app.core.scheduler import get_scheduler
from app.modules.logging.cache_request_body import CacheRequestBodyMiddleware
from app.modules.gamification.schemas import QuestFrequency
from app.modules.logging.services import save_error_log_async
from app.modules.task.schemas import QuestResetTask
import app.users.routes as user
import app.modules.community.routes as community
import app.modules.gamification.routes as gamification
import app.modules.progress_tracking.routes as progress_tracking
import app.modules.quiz.routes as quiz
import app.modules.certificate.routes as certificate
import app.modules.task.routes as task
import app.modules.friends.routes as friends

from app.auth.permissions import get_current_user, require_user
from app.core.config import settings
from app.users.models import Role
from dotenv import load_dotenv
import traceback
import os

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.app_env != "serverless":
        scheduler = get_scheduler()
        scheduler.schedule_daily(QuestResetTask(frequency=QuestFrequency.DAILY), settings.task_token)
        scheduler.schedule_weekly(QuestResetTask(frequency=QuestFrequency.WEEKLY), settings.task_token)
    yield


app = FastAPI(title="Mahasiswa Sukses Backend", lifespan=lifespan)

origins = ["*"]

app.add_middleware(CacheRequestBodyMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_cors_headers(request: Request) :
    origin = request.headers.get("origin")

    if origin in origins or origin:
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
        }
    return {}

async def global_exception_handler(request: Request, exc: Exception):
    headers = get_cors_headers(request)
    response = {"error": "Internal Server Error"}

    if isinstance(exc, AuthInvalidJwtError):
        return JSONResponse(status_code=401, content={"error": exc.__class__.__name__, "detail": str(exc)}, headers=headers)

    user_id = None
    user_role = None


    if hasattr(request.state, "current_user_id") and request.state.current_user_id:
        user_id = request.state.current_user_id
        user_role = "Unknown (Crashed before Role verification)"

    request_data = {
        "query_params": dict(request.query_params),
        "body": None
    }
    if hasattr(request.state, "body"):
        try:
            request_data["body"] = json.loads(request.state.body.decode("utf-8"))
        except Exception:
            request_data["body"] = "<Unparseable Data>"

    tb_text = traceback.format_exc()

    try:
        await save_error_log_async(
            exception_type=exc.__class__.__name__,
            message=str(exc),
            tb_text=tb_text,
            path=request.url.path,
            method=request.method,
            user_id=user_id,
            user_role=user_role,
            request_data=request_data
        )
    except Exception as db_log_err:
        print(f"CRITICAL: Failed to save error log to DB: {db_log_err}")
        print(tb_text)

    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=headers)

    if settings.show_error_details:
        response["error"] = exc.__class__.__name__
        response["detail"] = str(exc)
        response["traceback"] = tb_text

    return JSONResponse(
        status_code=500, 
        content=response,
        headers=headers
    )
app.add_exception_handler(HTTPException, global_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(community.router)
app.include_router(gamification.router)
app.include_router(progress_tracking.router)
app.include_router(quiz.router)
app.include_router(certificate.router)
app.include_router(task.router)
app.include_router(friends.router)

@app.get("/")
async def health():
    return {"status": "ok"}