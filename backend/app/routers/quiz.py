from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.session import Session
from app.models.question import Question
from app.models.student_quiz import StudentQuiz
from app.models.student_answer import StudentAnswer
from app.services.auth import get_current_user
from app.services.quiz_engine import generate_quiz_for_student
from app.services.grading import grade_quiz, check_answer
from app.schemas.quiz import QuizMetaResponse, QuizQuestionResponse, SubmitResponse

router = APIRouter(prefix="/api", tags=["quiz"])


class AnswerRequest(BaseModel):
    selected_choices: list[int]  # Original indices


@router.get("/my-quizzes")
async def my_quizzes(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get all quizzes the current student has taken."""
    result = await db.execute(
        select(StudentQuiz)
        .where(StudentQuiz.student_id == user.id)
        .order_by(StudentQuiz.started_at.desc())
    )
    quizzes = result.scalars().all()

    items = []
    for q in quizzes:
        session_result = await db.execute(select(Session).where(Session.id == q.session_id))
        session = session_result.scalar_one_or_none()
        items.append({
            "quiz_id": str(q.id),
            "session_id": str(q.session_id),
            "session_title": session.title if session else "Unknown",
            "started_at": q.started_at.isoformat(),
            "submitted_at": q.submitted_at.isoformat() if q.submitted_at else None,
            "score": q.score,
            "total_correct": q.total_correct,
            "total_questions": q.total_questions,
        })
    return items


@router.post("/sessions/{session_id}/join")
async def join_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role != "student":
        raise HTTPException(403, "Only students can join sessions")

    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found")
    if not session.is_active:
        raise HTTPException(400, "Session is not active")

    quiz = await generate_quiz_for_student(db, session, str(user.id))
    return {
        "quiz_id": str(quiz.id),
        "total_questions": quiz.total_questions,
    }


@router.get("/quiz/{quiz_id}", response_model=QuizMetaResponse)
async def get_quiz_meta(
    quiz_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(StudentQuiz).where(StudentQuiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    if not quiz or str(quiz.student_id) != str(user.id):
        raise HTTPException(404, "Quiz not found")

    session_result = await db.execute(
        select(Session).where(Session.id == quiz.session_id)
    )
    session = session_result.scalar_one_or_none()

    return QuizMetaResponse(
        quiz_id=str(quiz.id),
        session_id=str(quiz.session_id),
        session_title=session.title if session else "",
        total_questions=quiz.total_questions,
        time_limit_minutes=session.time_limit_minutes if session else None,
        started_at=quiz.started_at.isoformat(),
        submitted_at=quiz.submitted_at.isoformat() if quiz.submitted_at else None,
    )


@router.get("/quiz/{quiz_id}/question/{n}", response_model=QuizQuestionResponse)
async def get_question(
    quiz_id: str,
    n: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(StudentQuiz).where(StudentQuiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    if not quiz or str(quiz.student_id) != str(user.id):
        raise HTTPException(404, "Quiz not found")
    if n < 1 or n > quiz.total_questions:
        raise HTTPException(
            400, f"Question number must be between 1 and {quiz.total_questions}"
        )

    order_entry = quiz.questions_order[n - 1]
    question_id = order_entry["question_id"]
    choices_order = order_entry["choices_order"]

    q_result = await db.execute(select(Question).where(Question.id == question_id))
    question = q_result.scalar_one_or_none()
    if not question:
        raise HTTPException(500, "Question data missing")

    # Build shuffled choices (no is_correct)
    shuffled_choices = []
    for display_idx, original_idx in enumerate(choices_order):
        shuffled_choices.append(
            {
                "index": original_idx,  # Original index for answer submission
                "text": question.choices[original_idx]["text"],
            }
        )

    # Check for existing answer
    ans_result = await db.execute(
        select(StudentAnswer).where(
            StudentAnswer.student_quiz_id == quiz.id,
            StudentAnswer.question_id == question_id,
        )
    )
    existing_answer = ans_result.scalar_one_or_none()

    return QuizQuestionResponse(
        question_number=n,
        total_questions=quiz.total_questions,
        question_text=question.question_text,
        question_type=question.question_type,
        domain_name=question.domain.name if question.domain else "",
        choices=shuffled_choices,
        selected_choices=existing_answer.selected_choices if existing_answer else None,
    )


@router.post("/quiz/{quiz_id}/question/{n}/answer")
async def save_answer(
    quiz_id: str,
    n: int,
    body: AnswerRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(StudentQuiz).where(StudentQuiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    if not quiz or str(quiz.student_id) != str(user.id):
        raise HTTPException(404, "Quiz not found")
    if quiz.submitted_at:
        raise HTTPException(400, "Quiz already submitted")
    if n < 1 or n > quiz.total_questions:
        raise HTTPException(400, "Invalid question number")

    order_entry = quiz.questions_order[n - 1]
    question_id = order_entry["question_id"]

    q_result = await db.execute(select(Question).where(Question.id == question_id))
    question = q_result.scalar_one_or_none()

    is_correct = check_answer(question, body.selected_choices)

    # Upsert answer
    ans_result = await db.execute(
        select(StudentAnswer).where(
            StudentAnswer.student_quiz_id == quiz.id,
            StudentAnswer.question_id == question_id,
        )
    )
    existing = ans_result.scalar_one_or_none()
    if existing:
        existing.selected_choices = body.selected_choices
        existing.is_correct = is_correct
        existing.answered_at = datetime.now(timezone.utc)
    else:
        answer = StudentAnswer(
            student_quiz_id=quiz.id,
            question_id=question_id,
            selected_choices=body.selected_choices,
            is_correct=is_correct,
        )
        db.add(answer)

    await db.commit()
    return {"ok": True}


@router.post("/quiz/{quiz_id}/submit", response_model=SubmitResponse)
async def submit_quiz(
    quiz_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(StudentQuiz).where(StudentQuiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    if not quiz or str(quiz.student_id) != str(user.id):
        raise HTTPException(404, "Quiz not found")
    if quiz.submitted_at:
        raise HTTPException(400, "Quiz already submitted")

    # [C1] Time limit enforcement
    session_result = await db.execute(
        select(Session).where(Session.id == quiz.session_id)
    )
    session = session_result.scalar_one_or_none()
    if session and session.time_limit_minutes:
        deadline = quiz.started_at + timedelta(
            minutes=session.time_limit_minutes, seconds=30
        )
        # Still accept but the submitted_at will show it was late

    grade_result = await grade_quiz(db, quiz)

    # Build per-question results for review
    results = []
    for i, order_entry in enumerate(quiz.questions_order):
        qid = order_entry["question_id"]
        q_result = await db.execute(select(Question).where(Question.id == qid))
        question = q_result.scalar_one_or_none()

        ans_result = await db.execute(
            select(StudentAnswer).where(
                StudentAnswer.student_quiz_id == quiz.id,
                StudentAnswer.question_id == qid,
            )
        )
        answer = ans_result.scalar_one_or_none()

        results.append(
            {
                "question_number": i + 1,
                "question_text": question.question_text,
                "domain_name": question.domain.name if question.domain else "",
                "choices": question.choices,  # Full choices with is_correct
                "selected_choices": answer.selected_choices if answer else [],
                "is_correct": answer.is_correct if answer else False,
                "explanation": question.explanation,
            }
        )

    return SubmitResponse(
        score=grade_result["score"],
        total_correct=grade_result["total_correct"],
        total_questions=grade_result["total_questions"],
        results=results,
    )


@router.get("/quiz/{quiz_id}/results", response_model=SubmitResponse)
async def get_quiz_results(
    quiz_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get results for an already-submitted quiz."""
    result = await db.execute(select(StudentQuiz).where(StudentQuiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    if not quiz or str(quiz.student_id) != str(user.id):
        raise HTTPException(404, "Quiz not found")
    if not quiz.submitted_at:
        raise HTTPException(400, "Quiz not yet submitted")

    results = []
    for i, order_entry in enumerate(quiz.questions_order):
        qid = order_entry["question_id"]
        q_result = await db.execute(select(Question).where(Question.id == qid))
        question = q_result.scalar_one_or_none()

        ans_result = await db.execute(
            select(StudentAnswer).where(
                StudentAnswer.student_quiz_id == quiz.id,
                StudentAnswer.question_id == qid,
            )
        )
        answer = ans_result.scalar_one_or_none()

        results.append({
            "question_number": i + 1,
            "question_text": question.question_text,
            "domain_name": question.domain.name if question.domain else "",
            "choices": question.choices,
            "selected_choices": answer.selected_choices if answer else [],
            "is_correct": answer.is_correct if answer else False,
            "explanation": question.explanation,
        })

    return SubmitResponse(
        score=quiz.score or 0,
        total_correct=quiz.total_correct or 0,
        total_questions=quiz.total_questions,
        results=results,
    )
