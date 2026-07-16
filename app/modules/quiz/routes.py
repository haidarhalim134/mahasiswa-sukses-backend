from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.permissions import get_current_user, require_user
from app.db.session import get_db
from app.modules.quiz.schemas import GeneratedCertificate, QuestionRead, QuizCreate, QuizDetailResponse, QuizFullUpdate, QuizOverview, QuizResult, QuizStarting, QuizSubmission
from app.modules.quiz.services import (
    create_quiz_service,
    delete_quiz_service,
    exit_quiz_early as exit_quiz_early_service,
    generate_quiz_certificate as generate_certificate_service,
    get_all_quizzes as get_all_quizzes_service,
    get_quiz_detail_service,
    get_quiz_question as get_quiz_question_service,
    set_active_service,
    start_quiz as start_quiz_service,
    submit_quiz as submit_quiz_service,
    update_quiz_full_service,
)
from app.users.models import Role, User

router = APIRouter(prefix="/api/v1/quiz", tags=["quiz"])


@router.get("/", response_model=list[QuizOverview])
async def get_all_quizzes(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Endpoint untuk mengambil semua quiz tersedia bersama status pengerjaanya"""
    return await get_all_quizzes_service(db, current_user)


@router.post("/{quiz_id}/start", response_model=QuizStarting)
async def start_quiz(
    quiz_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Endpoint untuk memulai quiz"""
    return await start_quiz_service(db, quiz_id, current_user)


@router.get("/{quiz_id}/questions/{question_num}", response_model=QuestionRead)
async def get_quiz_question(
    quiz_id: int,
    question_num: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Endpoint untuk mengambil quiz tertentu"""
    return await get_quiz_question_service(db, quiz_id, question_num, current_user)


@router.post("/{quiz_id}/submit", response_model=QuizResult)
async def submit_quiz(
    quiz_id: int,
    submission: QuizSubmission,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Endpoint untuk mengirim quiz selesai, answer dikirim dalam bentuk dictionary dengan key adalah id pertanyaan dan value adalah pilihan jawaban (a, b, c, atau d). Jika hasilnya melampaui batas minimal (passed), endpoint /{quiz_id}/certificate bisa dipanggil untuk membuat serifikat tersedia untuk di unduh"""
    return await submit_quiz_service(db, quiz_id, submission, current_user)


@router.post("/{quiz_id}/exit")
async def exit_quiz_early(
    quiz_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Endpoint untuk membatalkan quiz"""
    await exit_quiz_early_service(db, quiz_id, current_user)


@router.post("/{quiz_id}/certificate", response_model=GeneratedCertificate)
async def generate_certificate(
    quiz_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Endpoint generate sertifikat untuk attempt quiz tertentu, mengembalikan certificate_id"""
    return await generate_certificate_service(db, quiz_id, current_user)

## admin
@router.post("/", response_model=QuizDetailResponse)
async def create_quiz(
    quiz_data: QuizCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_user(role=Role.admin))],
):
    """Endpoint untuk membuat kuis baru sekaligus dengan daftar pertanyaannya"""
    return await create_quiz_service(db, quiz_data)

@router.put("/{quiz_id}", response_model=QuizDetailResponse, include_in_schema=False)
async def update_quiz_full(
    quiz_id: int,
    quiz_data: QuizFullUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Endpoint untuk memperbarui keseluruhan kuis beserta semua pertanyaannya.
    - Pertanyaan dengan ID lama yang cocok akan di-update.
    - Pertanyaan baru (tanpa ID) akan ditambahkan.
    - Pertanyaan lama di DB yang tidak dikirim di request akan dihapus.
    """
    return await update_quiz_full_service(db, quiz_id, quiz_data)

@router.get("/{quiz_id}", response_model=QuizDetailResponse)
async def get_quiz_detail(
    quiz_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_user(role=Role.admin))],
):
    """Endpoint untuk mengambil detail kuis berdasarkan ID beserta pertanyaannya"""
    return await get_quiz_detail_service(db, quiz_id)

@router.delete("/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quiz(
    quiz_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_user(role=Role.admin))],
):
    """Endpoint untuk menghapus kuis bersama pertanyaanya."""
    return await delete_quiz_service(db, quiz_id)


@router.post("/{quiz_id}/set-active", status_code=status.HTTP_204_NO_CONTENT)
async def set_active(
    quiz_id: int,
    active: bool,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_user(role=Role.admin))],
):
    """Endpoint untuk menghapus kuis bersama pertanyaanya."""
    return await set_active_service(db, quiz_id, active)
