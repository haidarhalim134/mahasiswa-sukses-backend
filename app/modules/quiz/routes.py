from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.permissions import get_current_user
from app.db.session import get_db
from app.users.models import User

from app.modules.quiz.schemas import GeneratedCertificate, QuestionRead, QuizOverview, QuizResult, QuizStarting, QuizSubmission


router = APIRouter(prefix="/api/v1/quiz", tags=["quiz"])


@router.get("/", response_model=list[QuizOverview])
async def get_all_quizzes(
    current_user: User = Depends(get_current_user),
):
    """Endpoint untuk mengambil semua quiz tersedia bersama status pengerjaanya"""
    return []


@router.post("/{quiz_id}/start", response_model=QuizStarting)
async def start_quiz(
    quiz_id: int,
    current_user: User = Depends(get_current_user),
):
    """Endpoint untuk memulai quiz"""
    raise NotImplementedError


@router.get("/{quiz_id}/questions/{question_num}", response_model=QuestionRead)
async def get_quiz_question(
    quiz_id: int,
    question_num: int,
    current_user: User = Depends(get_current_user),
):
    """Endpoint untuk mengambil quiz tertentu"""
    raise NotImplementedError


@router.post("/{quiz_id}/submit", response_model=QuizResult)
async def submit_quiz(
    quiz_id: int,
    submission: QuizSubmission,
    current_user: User = Depends(get_current_user),
):
    """Endpoint untuk mengirim quiz selesai, answer dikirim dalam bentuk dictionary dengan key adalah id pertanyaan dan value adalah pilihan jawaban (a, b, c, atau d)"""
    raise NotImplementedError


@router.post("/{quiz_id}/exit")
async def exit_quiz_early(
    quiz_id: int,
    current_user: User = Depends(get_current_user),
):
    """Endpoint untuk membatalkan quiz"""
    raise NotImplementedError

@router.post("/{quiz_id}/certificate", response_model=GeneratedCertificate)
async def generate_certificate(
    quiz_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Endpoint generate sertifikat untuk attempt quiz tertentu, mengembalikan certificate_id"""
    raise NotImplementedError