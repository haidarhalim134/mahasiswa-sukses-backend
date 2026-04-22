from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.permissions import get_current_user
from app.db.session import get_db
from app.modules.quiz.schemas import GeneratedCertificate, QuestionRead, QuizOverview, QuizResult, QuizStarting, QuizSubmission
from app.modules.quiz.services import (
    exit_quiz_early as exit_quiz_early_service,
    generate_certificate as generate_certificate_service,
    get_all_quizzes as get_all_quizzes_service,
    get_quiz_question as get_quiz_question_service,
    start_quiz as start_quiz_service,
    submit_quiz as submit_quiz_service,
)
from app.users.models import User

router = APIRouter(prefix="/api/v1/quiz", tags=["quiz"])


@router.get("/", response_model=list[QuizOverview])
async def get_all_quizzes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Endpoint untuk mengambil semua quiz tersedia bersama status pengerjaanya"""
    return await get_all_quizzes_service(db, current_user)


@router.post("/{quiz_id}/start", response_model=QuizStarting)
async def start_quiz(
    quiz_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Endpoint untuk memulai quiz"""
    return await start_quiz_service(db, quiz_id, current_user)


@router.get("/{quiz_id}/questions/{question_num}", response_model=QuestionRead)
async def get_quiz_question(
    quiz_id: int,
    question_num: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Endpoint untuk mengambil quiz tertentu"""
    return await get_quiz_question_service(db, quiz_id, question_num, current_user)


@router.post("/{quiz_id}/submit", response_model=QuizResult)
async def submit_quiz(
    quiz_id: int,
    submission: QuizSubmission,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Endpoint untuk mengirim quiz selesai, answer dikirim dalam bentuk dictionary dengan key adalah id pertanyaan dan value adalah pilihan jawaban (a, b, c, atau d)"""
    return await submit_quiz_service(db, quiz_id, submission, current_user)


@router.post("/{quiz_id}/exit")
async def exit_quiz_early(
    quiz_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Endpoint untuk membatalkan quiz"""
    await exit_quiz_early_service(db, quiz_id, current_user)


@router.post("/{quiz_id}/certificate", response_model=GeneratedCertificate)
async def generate_certificate(
    quiz_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Endpoint generate sertifikat untuk attempt quiz tertentu, mengembalikan certificate_id"""
    raise NotImplementedError
    return await generate_certificate_service(db, quiz_id, current_user)
