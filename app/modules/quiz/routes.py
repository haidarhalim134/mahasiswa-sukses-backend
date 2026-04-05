
from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.modules.quiz.schemas import QuestionRead, QuizOverview, QuizResult, QuizSubmission


router = APIRouter(prefix="/api/v1/quiz", tags=["quiz"])


@router.get("/quizzes", response_model=list[QuizOverview])
async def get_all_quizzes():
    """Endpoint untuk mengambil semua quiz tersedia bersama status pengerjaanya"""
    raise NotImplementedError

@router.get("/quizzes/{quiz_id}/start", response_model=QuestionRead)
async def start_quiz(quiz_id: int):
    """Endpoint untuk memulai quiz"""
    raise NotImplementedError

@router.get("/quizzes/{quiz_id}/questions/{question_num}", response_model=QuestionRead)
async def get_quiz_question(quiz_id: int, question_num: int):
    """Endpoint untuk mengambil quiz tertentu"""
    raise NotImplementedError

@router.post("/quizzes/{quiz_id}/submit", response_model=QuizResult)
async def submit_quiz(quiz_id: int, submission: QuizSubmission):
    """CEndpoint untuk mengirim quiz selesai"""
    raise NotImplementedError

@router.post("/quizzes/{quiz_id}/exit")
async def exit_quiz_early(quiz_id: int):
    """Endpoint untuk membatalkan quiz"""
    raise NotImplementedError