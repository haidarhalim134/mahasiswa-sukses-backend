from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from app.auth.permissions import get_current_user
from app.users.models import User

from app.modules.quiz.schemas import QuestionRead, QuizOverview, QuizResult, QuizSubmission


router = APIRouter(prefix="/api/v1/quiz", tags=["quiz"])


@router.get("/quizzes", response_model=list[QuizOverview])
async def get_all_quizzes(
    current_user: User = Depends(get_current_user),
):
    """Endpoint untuk mengambil semua quiz tersedia bersama status pengerjaanya"""
    raise NotImplementedError


@router.post("/quizzes/{quiz_id}/start", response_model=QuestionRead)
async def start_quiz(
    quiz_id: int,
    current_user: User = Depends(get_current_user),
):
    """Endpoint untuk memulai quiz"""
    raise NotImplementedError


@router.get("/quizzes/{quiz_id}/questions/{question_num}", response_model=QuestionRead)
async def get_quiz_question(
    quiz_id: int,
    question_num: int,
    current_user: User = Depends(get_current_user),
):
    """Endpoint untuk mengambil quiz tertentu"""
    raise NotImplementedError


@router.post("/quizzes/{quiz_id}/submit", response_model=QuizResult)
async def submit_quiz(
    quiz_id: int,
    submission: QuizSubmission,
    current_user: User = Depends(get_current_user),
):
    """CEndpoint untuk mengirim quiz selesai"""
    raise NotImplementedError


@router.post("/quizzes/{quiz_id}/exit")
async def exit_quiz_early(
    quiz_id: int,
    current_user: User = Depends(get_current_user),
):
    """Endpoint untuk membatalkan quiz"""
    raise NotImplementedError