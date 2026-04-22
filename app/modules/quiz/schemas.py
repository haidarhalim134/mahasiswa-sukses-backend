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
    BELUM_DIMULAI = "belum_dimulai"
    BERJALAN = "berjalan"
    BATAL = 'batal'
    SELESAI = "selesai"

class QuizOption(str, Enum):
    A = 'a'
    B = 'b'
    C = 'c'
    D = 'd'

class QuizOverview(BaseModel):
    id: int
    title: str
    category: str
    duration_minutes: int
    minimum_score: int
    xp_reward: int
    difficulty: QuizDifficulty
    last_attempt_successfull: bool = False # if true but no certificate id, must call generate first
    certificate_id: Optional[str] = None
    completion_count: int

class QuizStarting(BaseModel):
    attempt_id: int
    text: str
    total_questions: int
    end_date_time: datetime
    first_question: "QuestionRead"

class QuestionRead(BaseModel):
    id: int
    current_number: int
    text: str
    option_a: str 
    option_b: str 
    option_c: str 
    option_d: str 

class QuizSubmission(BaseModel):
    answers: dict[int, QuizOption] 

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

class GeneratedCertificate(BaseModel):
    certificate_id: str