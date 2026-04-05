
from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.modules.quiz.schemas import QuestionRead, QuizOverview, QuizResult, QuizSubmission


router = APIRouter(prefix="/api/v1/quiz", tags=["quiz"])


@router.get("/quizzes", response_model=list[QuizOverview])
async def get_all_quizzes():
    """Returns the 'Semua Quiz' list and 'Rekomendasi Untuk Kamu'."""
    raise NotImplementedError

@router.get("/quizzes/{quiz_id}/start", response_model=QuestionRead)
async def start_quiz(quiz_id: int):
    """Initializes a quiz session and returns the first question."""
    raise NotImplementedError

@router.get("/quizzes/{quiz_id}/questions/{question_num}", response_model=QuestionRead)
async def get_quiz_question(quiz_id: int, question_num: int):
    """Fetches a specific question for the 'pengerjaan quiz' screen."""
    raise NotImplementedError

@router.post("/quizzes/{quiz_id}/submit", response_model=QuizResult)
async def submit_quiz(quiz_id: int, submission: QuizSubmission):
    """Calculates results, updates streak, and awards XP (Selesai Quiz screen)."""
    raise NotImplementedError

@router.get("/quizzes/{quiz_id}/certificate", response_class=FileResponse)
async def download_certificate(quiz_id: int):
    """Triggers the 'Download Sertifikat' action."""
    raise NotImplementedError

@router.post("/quizzes/{quiz_id}/exit")
async def exit_quiz_early(quiz_id: int):
    """Handles the 'Anda yakin ingin keluar quiz?' logic (Pop up quiz)."""
    raise NotImplementedError