from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import selectinload
from sqlmodel import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.certificate.schemas import CertificateSource
from app.modules.certificate.services import generate_certificate
from app.modules.gamification.services import add_xp
from app.modules.quiz.models import Quiz, QuizAttempt, QuizAttemptAnswer, QuizQuestion
from app.modules.quiz.schemas import (
    GeneratedCertificate,
    QuestionRead,
    QuizCreate,
    QuizFullUpdate,
    QuizOverview,
    QuizResult,
    QuizStarting,
    QuizStatus,
    QuizSubmission,
)
from app.users.models import User


from sqlalchemy import select, func, desc
from sqlalchemy.orm import aliased
from sqlalchemy.sql import label
from sqlalchemy import and_
from sqlalchemy.orm import contains_eager
from sqlalchemy import literal_column
from sqlalchemy import case
from sqlalchemy import over


async def get_all_quizzes(db: AsyncSession, current_user: User) -> list[QuizOverview]:
    now = datetime.now(timezone.utc)
    completion_subq = (
        select(
            QuizAttempt.quiz_id,
            func.count(QuizAttempt.id).label("completion_count")
        )
        .join(Quiz, QuizAttempt.quiz_id == Quiz.id)
        .where(
            QuizAttempt.submitted_at.is_(None),
            QuizAttempt.exited_at.is_(None),
            (
                QuizAttempt.started_at +
                Quiz.duration_minutes * text("INTERVAL '1 minute'")
            ) > now
        )
        .group_by(QuizAttempt.quiz_id)
        .subquery()
    )

    latest_attempt_subq = (
        select(
            QuizAttempt.id,
            QuizAttempt.quiz_id,
            QuizAttempt.passed,
            QuizAttempt.certificate_id,
            func.row_number()
            .over(
                partition_by=QuizAttempt.quiz_id,
                order_by=QuizAttempt.started_at.desc()
            )
            .label("rn")
        )
        .where(QuizAttempt.user_id == current_user.id)
        .subquery()
    )

    latest_attempt_filtered = (
        select(latest_attempt_subq)
        .where(latest_attempt_subq.c.rn == 1)
        .subquery()
    )

    stmt = (
        select(
            Quiz,
            func.coalesce(completion_subq.c.completion_count, 0),
            latest_attempt_filtered.c.passed,
            latest_attempt_filtered.c.certificate_id,
        )
        .outerjoin(
            completion_subq,
            completion_subq.c.quiz_id == Quiz.id
        )
        .outerjoin(
            latest_attempt_filtered,
            latest_attempt_filtered.c.quiz_id == Quiz.id
        )
        .where(Quiz.is_active.is_(True))
        .order_by(Quiz.created_at.desc())
    )

    rows = (await db.execute(stmt)).all()

    result: list[QuizOverview] = []
    for quiz, completion_count, passed, certificate_id in rows:
        result.append(
            QuizOverview(
                id=quiz.id,
                title=quiz.title,
                category=quiz.category,
                duration_minutes=quiz.duration_minutes,
                minimum_score=quiz.minimum_score,
                xp_reward=quiz.xp_reward,
                difficulty=quiz.difficulty,
                certificate_id=certificate_id,
                completion_count=int(completion_count or 0),
                last_attempt_successfull=bool(passed) if passed is not None else False,
            )
        )

    return result


async def start_quiz(db: AsyncSession, quiz_id: int, current_user: User) -> QuizStarting:
    quiz = await _get_quiz_or_404(db, quiz_id)

    # NOTE: just reset i think if user rejoined, end date etc
    active_attempt = await _get_last_attempt(db, quiz_id, current_user.id)
    if active_attempt is None:
        active_attempt = QuizAttempt(
            quiz_id=quiz.id,
            user_id=current_user.id,
            status=QuizStatus.BERJALAN.value,
            total_questions=len(quiz.questions),
            minimum_score=quiz.minimum_score,
        )
        db.add(active_attempt)
        await db.commit()
        await db.refresh(active_attempt)

    questions = sorted(quiz.questions, key=lambda item: item.order_index)
    if not questions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz have no question")

    return QuizStarting(
        attempt_id=active_attempt.id,
        text=quiz.title,
        total_questions=len(questions),
        end_date_time=active_attempt.started_at + timedelta(minutes=quiz.duration_minutes),
        first_question=_question_to_read(questions[0], 1),
    )


async def get_quiz_question(db: AsyncSession, quiz_id: int, question_num: int, current_user: User) -> QuestionRead:
    await _get_last_attempt_or_404(db, quiz_id, current_user.id)
    quiz = await _get_quiz_or_404(db, quiz_id)

    questions = sorted(quiz.questions, key=lambda item: item.order_index)
    if question_num < 1 or question_num > len(questions):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    return _question_to_read(questions[question_num - 1], question_num)


async def submit_quiz(db: AsyncSession, quiz_id: int, submission: QuizSubmission, current_user: User) -> QuizResult:
    attempt = await _get_last_attempt_or_404(db, quiz_id, current_user.id)
    quiz = await _get_quiz_or_404(db, quiz_id)

    # give 1 minute buffer
    if datetime.now(timezone.utc) > attempt.started_at + timedelta(minutes=quiz.duration_minutes + 1):
        print(datetime.now(timezone.utc))
        print(attempt.started_at)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Quiz attempt closed",
        )

    questions = sorted(quiz.questions, key=lambda item: item.order_index)

    existing_answers_stmt = select(QuizAttemptAnswer).where(QuizAttemptAnswer.attempt_id == attempt.id)
    existing_answers = (await db.execute(existing_answers_stmt)).scalars().all()
    for answer in existing_answers:
        await db.delete(answer)

    correct_answers = 0
    for question in questions:
        selected_option = submission.answers.get(question.id)
        if selected_option is None:
            continue

        is_correct = selected_option.value == question.correct_option
        if is_correct:
            correct_answers += 1

        db.add(
            QuizAttemptAnswer(
                attempt_id=attempt.id,
                question_id=question.id,
                selected_option=selected_option,
                is_correct=is_correct,
            )
        )

    total_questions = len(questions)
    passed = correct_answers >= quiz.minimum_score
    points_gained = quiz.xp_reward if passed else 0

    streak_count, streak_bonus = 0, 0
    if passed:
        streak_count, streak_bonus = await _calculate_streak_bonus(db, current_user.id, attempt.id)

    attempt.submitted_at = datetime.now(timezone.utc)
    attempt.correct_answers = correct_answers
    attempt.total_questions = total_questions
    attempt.minimum_score = quiz.minimum_score
    attempt.passed = passed
    attempt.points_gained = points_gained
    attempt.streak_bonus = streak_bonus

    await db.commit()
    await db.refresh(attempt)

    if passed:
        await add_xp(db, current_user, points_gained + streak_bonus)

    return QuizResult(
        correct_answers=correct_answers,
        total_questions=total_questions,
        minimum_score=quiz.minimum_score,
        passed=passed,
        points_gained=points_gained,
        streak_count=streak_count,
        streak_bonus=streak_bonus,
        certificate_id=attempt.certificate_id,
    )

# submit_quiz helper
async def _calculate_streak_bonus(db: AsyncSession, user_id, current_attempt_id) -> tuple[int, int]:
    """Helper function to calculate streak count and streak bonus points."""
    stmt = (
        select(QuizAttempt)
        .where(
            QuizAttempt.user_id == user_id,
            QuizAttempt.submitted_at.is_not(None),
            QuizAttempt.exited_at.is_(None),
            QuizAttempt.id != current_attempt_id
        )
        .order_by(desc(QuizAttempt.submitted_at))
    )
    result = await db.execute(stmt)
    past_attempts = result.scalars().all()

    streak_count = 0
    for past in past_attempts:
        if not past.passed:
            break
        streak_count += 1
        
    return streak_count, streak_count * 10
# submit_quiz helper

async def exit_quiz_early(db: AsyncSession, quiz_id: int, current_user: User) -> None:
    attempt = await _get_last_attempt_or_404(db, quiz_id, current_user.id)
    attempt.exited_at = datetime.now(timezone.utc)
    await db.commit()


async def generate_quiz_certificate(db: AsyncSession, quiz_id: int, current_user: User) -> GeneratedCertificate:
    attempt = await _get_last_attempt_or_404(db, quiz_id, current_user.id, active=False)
    quiz = await _get_quiz_or_404(db, quiz_id)

    if attempt.computed_status != QuizStatus.SELESAI or not attempt.passed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attempt did not pass",
        )

    if attempt.certificate_id:
        return GeneratedCertificate(certificate_id=attempt.certificate_id)

    attempt.certificate_id = await generate_certificate(db, current_user.id, quiz.title, quiz.category, CertificateSource.QUIZ, quiz_id, "quiz_certificate.svg", {
        '{NAMA}': current_user.full_name.upper(),
        '{tanggal_selesai}': _format_date(attempt.submitted_at),
        '{nama_kuis}': quiz.title
    })
    await db.commit()
    await db.refresh(attempt)

    return GeneratedCertificate(certificate_id=attempt.certificate_id)


async def _get_quiz_or_404(db: AsyncSession, quiz_id: int) -> Quiz:
    quiz_stmt = select(Quiz).where(Quiz.id == quiz_id, Quiz.is_active.is_(True)).options(selectinload(Quiz.questions))
    quiz = (await db.execute(quiz_stmt)).scalars().first()
    if quiz is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
    return quiz


async def _get_last_attempt(db: AsyncSession, quiz_id: int, user_id, active=True) -> Optional[QuizAttempt]:
    now = datetime.now(timezone.utc)
    attempt_stmt = select(QuizAttempt).join(Quiz, QuizAttempt.quiz_id == Quiz.id).where(
        QuizAttempt.quiz_id == quiz_id,
        QuizAttempt.user_id == user_id,
    ).order_by(QuizAttempt.started_at.desc())

    if active:
        attempt_stmt = attempt_stmt.where(        
            QuizAttempt.submitted_at.is_(None),
            QuizAttempt.exited_at.is_(None),
            (
                QuizAttempt.started_at +
                Quiz.duration_minutes * text("INTERVAL '1 minute'")
            ) > now
        )

    from sqlalchemy.dialects import postgresql

    return (await db.execute(attempt_stmt)).scalars().first()


async def _get_last_attempt_or_404(db: AsyncSession, quiz_id: int, user_id, active=True) -> QuizAttempt:
    attempt = await _get_last_attempt(db, quiz_id, user_id, active)
    if attempt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz attempt not found")
    return attempt


def _question_to_read(question: QuizQuestion, current_number: int) -> QuestionRead:
    return QuestionRead(
        id=question.id,
        current_number=current_number,
        text=question.text,
        option_a=question.option_a,
        option_b=question.option_b,
        option_c=question.option_c,
        option_d=question.option_d,
    )

# NOTE: move in case it is reusable elsewhere
def _format_date(dt):
    bulan = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    return f"{dt.day} {bulan[dt.month - 1]} {dt.year}"

## admin
async def create_quiz_service(db: AsyncSession, quiz_data: QuizCreate):
    new_quiz = Quiz(
        title=quiz_data.title,
        category=quiz_data.category,
        duration_minutes=quiz_data.duration_minutes,
        minimum_score=quiz_data.minimum_score,
        xp_reward=quiz_data.xp_reward,
        difficulty=quiz_data.difficulty,
        is_active=quiz_data.is_active
    )
    db.add(new_quiz)
    await db.flush() # Mendapatkan ID kuis
    
    # Auto-imply order_index menggunakan enumerate (dimulai dari 1)
    for index, q in enumerate(quiz_data.questions, start=1):
        new_question = QuizQuestion(
            quiz_id=new_quiz.id,
            order_index=index,  # Di-imply otomatis di sini
            text=q.text,
            option_a=q.option_a,
            option_b=q.option_b,
            option_c=q.option_c,
            option_d=q.option_d,
            correct_option=q.correct_option
        )
        db.add(new_question)
        
    await db.commit()
    
    result = await db.execute(
        select(Quiz).where(Quiz.id == new_quiz.id).options(selectinload(Quiz.questions))
    )
    return result.scalar_one()

async def update_quiz_full_service(db: AsyncSession, quiz_id: int, quiz_data: QuizFullUpdate):
    result = await db.execute(
        select(Quiz).where(Quiz.id == quiz_id).options(selectinload(Quiz.questions))
    )
    quiz = result.scalar_one_or_none()
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # 1. Update info kuis utama
    quiz.title = quiz_data.title
    quiz.category = quiz_data.category
    quiz.duration_minutes = quiz_data.duration_minutes
    quiz.minimum_score = quiz_data.minimum_score
    quiz.xp_reward = quiz_data.xp_reward
    quiz.difficulty = quiz_data.difficulty
    quiz.is_active = quiz_data.is_active

    # Map pertanyaan lama di database {id: objek}
    existing_questions = {q.id: q for q in quiz.questions}
    incoming_question_ids = set()
    
    # 2. Sinkronisasi dengan dynamic order_index
    for index, q_data in enumerate(quiz_data.questions, start=1):
        if q_data.id and q_data.id in existing_questions:
            # Kasus A: Update data lama + perbarui urutan posisinya (order_index)
            question = existing_questions[q_data.id]
            question.order_index = index
            question.text = q_data.text
            question.option_a = q_data.option_a
            question.option_b = q_data.option_b
            question.option_c = q_data.option_c
            question.option_d = q_data.option_d
            question.correct_option = q_data.correct_option
            incoming_question_ids.add(q_data.id)
        else:
            # Kasus B: Buat data baru + tentukan urutan posisinya (order_index)
            new_question = QuizQuestion(
                quiz_id=quiz.id,
                order_index=index,
                text=q_data.text,
                option_a=q_data.option_a,
                option_b=q_data.option_b,
                option_c=q_data.option_c,
                option_d=q_data.option_d,
                correct_option=q_data.correct_option
            )
            db.add(new_question)

    # Kasus C: Hapus yang tidak dikirim di request
    for old_id, old_question in existing_questions.items():
        if old_id not in incoming_question_ids:
            await db.delete(old_question)

    await db.commit()
    
    # Ambil ulang data kuis segar dari DB
    final_result = await db.execute(
        select(Quiz).where(Quiz.id == quiz_id).options(selectinload(Quiz.questions))
    )
    return final_result.scalar_one()

async def get_quiz_detail_service(db: AsyncSession, quiz_id: int):
    result = await db.execute(
        select(Quiz).where(Quiz.id == quiz_id).options(selectinload(Quiz.questions))
    )
    quiz = result.scalar_one_or_none()
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return quiz

async def delete_quiz_service(db: AsyncSession, quiz_id: int):
    result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
        
    await db.delete(quiz)
    await db.commit()
    return None

async def set_active_service(db: AsyncSession, quiz_id: int, new_is_active: bool):
    result = await db.execute(
        select(Quiz).where(Quiz.id == quiz_id).options(selectinload(Quiz.questions))
    )
    quiz = result.scalar_one_or_none()
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    quiz.is_active = new_is_active

    await db.commit()