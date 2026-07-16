from datetime import date, datetime, timedelta, timezone
import hashlib
import io
from typing import Annotated, Optional
from PIL import Image
from uuid import UUID
from fastapi import APIRouter, File, HTTPException, Query, Request, Response, Security, UploadFile, Depends, status
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import func, select

from app.auth.permissions import get_current_user, get_current_user_id, require_role
from app.core.storage_handler import Buckets, get_storage
from app.db.session import get_db
from app.modules.quiz.models import QuizAttempt
from app.users.models import Role, User, UserLoginHistory
from app.users.schemas import ProfileUpdate, QuizHistoryItem, SettingsUpdate, StudentDetailResponse, StudentListItemResponse, StudentListResponse, UserProfile, UserStats
from app.users.service import get_login_history_streak, get_user_by_id, update_profile_data, update_user_setting, user_to_private_view


router = APIRouter(prefix="/api/v1/user", tags=["user"])

HTTP_401_UNAUTHORIZED = {"description": "Missing or invalid authentication token"}
HTTP_404_NOT_FOUND = {"description": "Resource not found"}

@router.get(
    "/profile", 
    response_model=UserProfile,
    responses={
        200: {"description": "Profile data successfully retrieved."},
        401: HTTP_401_UNAUTHORIZED
    }
)
async def get_my_profile(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Endpoint untuk mengambil data profile user"""
    return user_to_private_view(current_user)


@router.post(
    "/profile", 
    response_model=UserProfile,
    responses={
        200: {"description": "Profile data successfully updated."},
        400: {"description": "Invalid input data format."},
        401: HTTP_401_UNAUTHORIZED
    }
)
async def update_profile(
    data: ProfileUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Endpoint untuk mengupdate data profile user. Set None/null untuk field yang tidak akan di update"""
    return await update_profile_data(db, current_user, data)


@router.post(
    "/profile/avatar",
    status_code=204,
    responses={
        204: {"description": "Avatar successfully processed and uploaded. No content returned."},
        400: {"description": "Uploaded file is not a valid image format."},
        401: HTTP_401_UNAUTHORIZED
    }
)
async def upload_avatar(
    current_user: Annotated[User, Depends(get_current_user)],
    file: Annotated[UploadFile, File(...)],
):
    """Endpoint untuk memperbarui avatar user. Menerima berbagai format gambar (`*.jpeg`, `*.png`, `*.webp`, dll.)"""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")

    storage = get_storage()

    contents = await file.read()
    image = Image.open(io.BytesIO(contents))

    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

    image.thumbnail((512, 512))

    buffer = io.BytesIO()
    image.save(buffer, format="WEBP", quality=80, optimize=True)
    buffer.seek(0)

    path = f"{current_user.id}.webp"

    await storage.upload(
        file=buffer,
        bucket=Buckets.AVATAR.value,
        path=path,
        content_type="image/webp"
    )

    # # delete old image (try to atleast)
    # try:
    #     await storage.delete(
    #         bucket=Buckets.AVATAR.value,
    #         path=path
    #     )
    # except:
    #     pass


@router.post(
    "/settings",
    responses={
        200: {"description": "Settings successfully updated."},
        400: {"description": "Invalid settings input data."},
        401: HTTP_401_UNAUTHORIZED
    }
)
async def update_settings(
    data: SettingsUpdate,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Endpoint untuk memperbarui setting profile mahasiswa. Set None/null untuk field yang tidak akan di update"""
    return await update_user_setting(db, current_user_id, data)

@router.get(
    "/avatar/{user_id}",
    response_class=Response,
    responses={
        200: {
            "content": {"image/webp": {}},
            "description": "Returns the user avatar or a fallback generated avatar in WebP format."
        },
        304: {
            "description": "Not Modified. Client's cached avatar is up to date (If cache mechanism is enabled)."
        },
        400: {
            "description": "Avatar missing from storage and user's full name is unavailable to generate placeholder."
        },
        404: HTTP_404_NOT_FOUND,
        502: {
            "description": "Bad Gateway. Failed to fetch fallback placeholder avatar from external API."
        }
    }
)
async def get_avatar(
    user_id: UUID, 
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Endpoint untuk mengambil avatar user tertentu"""
    user = await get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    storage = get_storage()
    path = f"{user_id}.webp"

    data = None

    try:
        data = await storage.download(Buckets.AVATAR.value, path)
    except Exception:
        if not user.full_name:
            raise HTTPException(status_code=400, detail="User full name not available")

        name_query = user.full_name.replace(" ", "+")
        url = f"https://ui-avatars.com/api/?name={name_query}&format=webp"

        async with httpx.AsyncClient() as client:
            resp = await client.get(url)

        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Failed to fetch avatar")

        data = resp.content

    # cache stuff
    etag = hashlib.sha512(data).hexdigest()
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304)

    return Response(
        content=data,
        media_type="image/webp",
        headers={
            "ETag": etag,
            "Cache-Control": "public, s-maxage=5, stale-while-revalidate=3600"
        }
    )

## admin
@router.get("", response_model=StudentListResponse)
async def get_students_list(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Security(require_role([Role.admin]), scopes=[Role.admin.value])],
    search: Optional[str] = Query(None, description="Search by name or NIM"),
):
    """
    Endpoint untuk mengambil list mahasiswa dengan view admin.
    """
    # Base query for Student
    query = select(User).where(User.role == "student")
    
    if search:
        # Search by name or NIM
        query = query.where(
            (User.full_name.ilike(f"%{search}%")) | 
            (User.nim.ilike(f"%{search}%"))
        )
        
    query = query.order_by(User.full_name.asc())
    result = await db.execute(query)
    students = result.scalars().all()
    
    students_data = []
    for student in students:
        # Get count of successfully submitted/finished quizzes
        quiz_count_statement = (
            select(func.count(QuizAttempt.id))
            .where(QuizAttempt.user_id == student.id)
            # Filter attempts where status is finished (submitted_at is present)
            .where(QuizAttempt.submitted_at.isnot(None)) 
        )
        quiz_count_res = await db.execute(quiz_count_statement)
        completed_quizzes = quiz_count_res.scalar() or 0
        
        students_data.append(
            StudentListItemResponse(
                id=student.id,
                full_name=student.full_name,
                total_xp=student.total_xp,
                current_streak=student.current_streak,
                total_quizzes_completed=completed_quizzes
            )
        )
        
    return StudentListResponse(
        students=students_data,
        total_found=len(students_data)
    )


@router.get("/{user_id}/detail", response_model=StudentDetailResponse)
async def get_student_detail(
    user_id: UUID,
    current_user: Annotated[User, Security(require_role([Role.admin]), scopes=[Role.admin.value])],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Endpoint untuk mengambil detail informasi admin untuk mahasiswa tertentu.
    """
    # 1. Fetch User details
    user = await db.get(User, user_id)
    if not user or user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_404_RESOURCE_NOT_FOUND, 
            detail="Student not found"
        )
        
    # 2. Get 30 Days login history activity list
    today = date.today()
    activity_30_days = await get_login_history_streak(db, user_id, 30)
    
    # 3. Retrieve Quiz performance analytics
    attempts_stmt = (
        select(QuizAttempt)
        .options(selectinload(QuizAttempt.quiz))
        .where(QuizAttempt.user_id == user_id)
        .where(QuizAttempt.submitted_at.isnot(None))
        .order_by(QuizAttempt.submitted_at.desc()) # Keep newest attempts first as a tie-breaker
    )
    attempts_res = await db.execute(attempts_stmt)
    all_attempts = attempts_res.scalars().all()
    
    # --- Deduplicate to keep only the HIGHEST score per quiz ---
    best_attempts_by_quiz = {}
    
    for attempt in all_attempts:
        # Calculate percentage score for this attempt
        score = (attempt.correct_answers / attempt.total_questions) * 100 if attempt.total_questions > 0 else 0.0
        
        existing_best = best_attempts_by_quiz.get(attempt.quiz_id)
        if existing_best is None:
            # First time seeing this quiz, store it
            best_attempts_by_quiz[attempt.quiz_id] = (attempt, score)
        else:
            existing_score = existing_best[1]
            # If this attempt has a strictly higher score, replace the old one
            if score > existing_score:
                best_attempts_by_quiz[attempt.quiz_id] = (attempt, score)
    
    # Extract the filtered, highest-score attempts
    best_attempts = [item[0] for item in best_attempts_by_quiz.values()]
    best_scores = [item[1] for item in best_attempts_by_quiz.values()]
    
    total_quizzes = len(best_attempts)
    
    # Calculate Average Score (using only best scores)
    avg_score = 0.0
    if total_quizzes > 0:
        avg_score = round(sum(best_scores) / total_quizzes, 1)
        
    # Build Quiz History (only highest score per quiz)
    quiz_history_items = []
    for att in best_attempts:
        quiz_title = att.quiz.title if att.quiz else "Quiz" 
        score_percentage = round((att.correct_answers / att.total_questions) * 100) if att.total_questions > 0 else 0
        
        quiz_history_items.append(
            QuizHistoryItem(
                quiz_title=quiz_title,
                completed_date=att.submitted_at.date(),
                score=score_percentage,
                passed=att.passed
            )
        )
        
    # 4. Progress percentage helper calculation
    xp_required = user.xp_required_for_this_milestone
    progress_percentage = 0.0
    if xp_required > 0:
        progress_percentage = round((user.current_level_xp / xp_required) * 100, 1)

    return StudentDetailResponse(
        id=user.id,
        full_name=user.full_name,
        nim=user.nim,
        current_level=user.level,
        current_streak=user.current_streak,
        
        current_level_xp=user.current_level_xp,
        xp_required_for_this_milestone=xp_required,
        progress_percentage=progress_percentage,
        
        total_xp=user.total_xp,
        total_quizzes_completed=total_quizzes,
        average_score=avg_score,  
        
        activity_30_days=activity_30_days,
        quiz_history=quiz_history_items, 
        
        last_updated=today
    )