from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from enum import Enum
from typing import List, Optional

# --- New Enums for Quiz Module ---

class QuizDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class QuizStatus(str, Enum):
    BELUM_DIMULAI = "belum dimulai"
    SELESAI = "selesai"

# --- New Schemas ---

class QuizOverview(BaseModel):
    id: int
    title: str
    category: str
    duration_minutes: int
    xp_reward: int
    difficulty: QuizDifficulty
    status: QuizStatus

class QuestionOption(BaseModel):
    id: int
    text: str

class QuestionRead(BaseModel):
    id: int
    current_number: int
    total_questions: int
    text: str
    options: List[QuestionOption]
    timer_seconds: int

class QuizSubmission(BaseModel):
    answers: dict[int, int]  # Question ID mapping to Option ID

class QuizResult(BaseModel):
    score_text: str  # e.g., "5 dari 5 soal benar"
    points_gained: int
    streak_bonus: int
    certificate_id: Optional[str] = None

class QuizSummary(BaseModel):
    total_quiz: int
    total_quiz_completed: int
