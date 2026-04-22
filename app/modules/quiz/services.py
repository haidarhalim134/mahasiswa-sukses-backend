from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import selectinload
from sqlmodel import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.quiz.models import Quiz, QuizAttempt, QuizAttemptAnswer, QuizQuestion
from app.modules.quiz.schemas import (
    GeneratedCertificate,
    QuestionRead,
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
        .where(
            QuizAttempt.submitted_at.is_(None),
            QuizAttempt.exited_at.is_(None),
            (QuizAttempt.started_at + func.make_interval(0, 0, 0, 0, 0, Quiz.duration_minutes * 60)) > now
        )
        .group_by(QuizAttempt.quiz_id)
        .subquery()
    )

    latest_attempt_subq = (
        select(
            QuizAttempt.id,
            QuizAttempt.quiz_id,
            QuizAttempt.passed,
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
            latest_attempt_filtered.c.passed
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
    for quiz, completion_count, passed in rows:
        result.append(
            QuizOverview(
                id=quiz.id,
                title=quiz.title,
                category=quiz.category,
                duration_minutes=quiz.duration_minutes,
                minimum_score=quiz.minimum_score,
                xp_reward=quiz.xp_reward,
                difficulty=quiz.difficulty,
                certificate_id=None,
                completion_count=int(completion_count or 0),
                last_attempt_successfull=bool(passed) if passed is not None else False,
            )
        )

    return result


async def start_quiz(db: AsyncSession, quiz_id: int, current_user: User) -> QuizStarting:
    quiz = await _get_quiz_or_404(db, quiz_id)

    # TODO: just reset i think if user rejoined, end date etc
    active_attempt = await _get_active_attempt(db, quiz_id, current_user.id)
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
    await _get_active_attempt_or_404(db, quiz_id, current_user.id)
    quiz = await _get_quiz_or_404(db, quiz_id)

    questions = sorted(quiz.questions, key=lambda item: item.order_index)
    if question_num < 1 or question_num > len(questions):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    return _question_to_read(questions[question_num - 1], question_num)


async def submit_quiz(db: AsyncSession, quiz_id: int, submission: QuizSubmission, current_user: User) -> QuizResult:
    attempt = await _get_active_attempt_or_404(db, quiz_id, current_user.id)
    quiz = await _get_quiz_or_404(db, quiz_id)

    # give 1 minute buffer
    if datetime.now(timezone.utc) > attempt.started_at + timedelta(minutes=quiz.duration_minutes + 1):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Quiz attempt closed",
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
            # raise HTTPException(
            #     status_code=status.HTTP_400_BAD_REQUEST,
            #     detail=f"Jawaban untuk pertanyaan {question.id} belum diisi",
            # )
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
    streak_bonus = 0

    attempt.submitted_at = datetime.now(timezone.utc)
    attempt.correct_answers = correct_answers
    attempt.total_questions = total_questions
    attempt.minimum_score = quiz.minimum_score
    attempt.passed = passed
    attempt.points_gained = points_gained
    attempt.streak_bonus = streak_bonus

    await db.commit()
    await db.refresh(attempt)

    return QuizResult(
        correct_answers=correct_answers,
        total_questions=total_questions,
        minimum_score=quiz.minimum_score,
        passed=passed,
        points_gained=points_gained,
        streak_bonus=streak_bonus,
        certificate_id=attempt.certificate_id,
    )


async def exit_quiz_early(db: AsyncSession, quiz_id: int, current_user: User) -> None:
    attempt = await _get_active_attempt_or_404(db, quiz_id, current_user.id)
    attempt.exited_at = datetime.now(timezone.utc)
    await db.commit()


async def generate_certificate(db: AsyncSession, quiz_id: int, current_user: User) -> GeneratedCertificate:
    attempt = await _get_active_attempt_or_404(db, quiz_id, current_user.id)

    if attempt.computed_status != QuizStatus.SELESAI or not attempt.passed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attempt did not pass",
        )

    if attempt.certificate_id:
        return GeneratedCertificate(certificate_id=attempt.certificate_id)

    attempt.certificate_id = str(uuid4())
    await db.commit()
    await db.refresh(attempt)

    return GeneratedCertificate(certificate_id=attempt.certificate_id)


async def _get_quiz_or_404(db: AsyncSession, quiz_id: int) -> Quiz:
    quiz_stmt = select(Quiz).where(Quiz.id == quiz_id, Quiz.is_active.is_(True)).options(selectinload(Quiz.questions))
    quiz = (await db.execute(quiz_stmt)).scalars().first()
    if quiz is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
    return quiz


async def _get_active_attempt(db: AsyncSession, quiz_id: int, user_id) -> Optional[QuizAttempt]:
    now = datetime.now(timezone.utc)
    attempt_stmt = select(QuizAttempt).where(
        QuizAttempt.quiz_id == quiz_id,
        QuizAttempt.user_id == user_id,

        QuizAttempt.submitted_at.is_(None),
        QuizAttempt.exited_at.is_(None),
        (QuizAttempt.started_at + func.make_interval(0, 0, 0, 0, 0, Quiz.duration_minutes * 60)) > now
    )
    return (await db.execute(attempt_stmt)).scalars().first()


async def _get_active_attempt_or_404(db: AsyncSession, quiz_id: int, user_id) -> QuizAttempt:
    attempt = await _get_active_attempt(db, quiz_id, user_id)
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
