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
    streak_count: int
    streak_bonus: int
    certificate_id: Optional[str] = None

class QuizSummary(BaseModel):
    total_quiz: int
    total_quiz_completed: int

class GeneratedCertificate(BaseModel):
    certificate_id: str

## admin
class QuestionCreate(BaseModel):
    text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: QuizOption

class QuestionUpdate(BaseModel):
    order_index: Optional[int] = None
    text: Optional[str] = None
    option_a: Optional[str] = None
    option_b: Optional[Optional[str]] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    correct_option: Optional[QuizOption] = None

# Schema untuk membuat & mengedit Kuis
class QuizCreate(BaseModel):
    title: str
    category: str
    duration_minutes: int
    minimum_score: int = 0
    xp_reward: int = 0
    difficulty: QuizDifficulty
    is_active: bool = True
    questions: List[QuestionCreate] = []

class QuizUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    duration_minutes: Optional[int] = None
    minimum_score: Optional[int] = None
    xp_reward: Optional[int] = None
    difficulty: Optional[QuizDifficulty] = None
    is_active: Optional[bool] = None

class QuestionDetailResponse(QuestionCreate):
    id: int
    order_index: int

class QuizDetailResponse(BaseModel):
    id: int
    title: str
    category: str
    duration_minutes: int
    minimum_score: int
    xp_reward: int
    difficulty: QuizDifficulty
    is_active: bool
    created_at: datetime
    questions: List[QuestionDetailResponse]

    class Config:
        from_attributes = True

class QuestionUpdateBulk(BaseModel):
    id: Optional[int] = None 
    text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: QuizOption

class QuizFullUpdate(BaseModel):
    title: str
    category: str
    duration_minutes: int
    minimum_score: int = 0
    xp_reward: int = 0
    difficulty: QuizDifficulty
    is_active: bool = True
    questions: List[QuestionUpdateBulk] = []

class QuizRaw(BaseModel):
    id: int
    title: str
    category: str
    duration_minutes: int
    minimum_score: int
    xp_reward: int
    difficulty: QuizDifficulty
    is_active: bool
    created_at: datetime
    question_count: int
