from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from enum import Enum
from typing import List, Optional


class QuizDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class QuizStatus(str, Enum):
    BELUM_DIMULAI = "belum dimulai"
    SELESAI = "selesai"

class QuizOverview(BaseModel):
    id: int
    title: str
    category: str
    duration_minutes: int
    minimum_score: int
    xp_reward: int
    difficulty: QuizDifficulty
    status: QuizStatus
    completion_count: int

class QuestionOption(BaseModel):
    id: int
    text: str

class QuestionRead(BaseModel):
    id: int
    current_number: int
    total_questions: int
    text: str
    options: List[QuestionOption]
    end_date_time: datetime

class QuizSubmission(BaseModel):
    answers: dict[int, int] 

class QuizResult(BaseModel):
    correct_answers: int
    total_questions: int
    minimum_score: int
    passed: bool
    points_gained: int
    streak_bonus: int
    certificate_id: Optional[str] = None

class QuizSummary(BaseModel):
    total_quiz: int
    total_quiz_completed: int
