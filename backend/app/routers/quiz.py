from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from sqlalchemy import delete as sa_delete
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


async def _build_quiz_results(quiz: StudentQuiz, db: AsyncSession) -> list[dict]:
    """Bulk-fetch questions and answers for a quiz, avoiding N+1 queries."""
    qids = [entry["question_id"] for entry in quiz.questions_order]
    q_result = await db.execute(select(Question).where(Question.id.in_(qids)))
    questions_by_id = {str(q.id): q for q in q_result.scalars().all()}
    ans_result = await db.execute(
        select(StudentAnswer).where(StudentAnswer.student_quiz_id == quiz.id)
    )
    answers_by_qid = {str(a.question_id): a for a in ans_result.scalars().all()}
    results = []
    for i, entry in enumerate(quiz.questions_order):
        qid = entry["question_id"]
        q = questions_by_id.get(qid)
        a = answers_by_qid.get(qid)
        results.append({
            "question_number": i + 1,
            "question_text": q.question_text if q else "",
            "domain_name": q.domain.name if q and q.domain else "",
            "choices": q.choices if q else [],
            "selected_choices": a.selected_choices if a else [],
            "is_correct": a.is_correct if a else False,
            "explanation": q.explanation if q else None,
        })
    return results


class AnswerRequest(BaseModel):
    selected_choices: list[int]  # Original indices

class PracticeQuizRequest(BaseModel):
    subject_id: str
    domain_ids: list[str] | None = None  # None = all domains
    questions_count: int = Field(default=10, ge=1)


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

    session_ids = {q.session_id for q in quizzes}
    sess_result = await db.execute(select(Session).where(Session.id.in_(session_ids)))
    sessions_by_id = {s.id: s for s in sess_result.scalars().all()}

    items = []
    for q in quizzes:
        session = sessions_by_id.get(q.session_id)
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


@router.post("/practice-quiz")
async def create_practice_quiz(
    body: PracticeQuizRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Student generates a practice quiz for self-study. No session needed."""
    import random
    import math
    from collections import defaultdict
    from app.models.domain import Domain
    import uuid as uuid_module

    if user.role != "student":
        raise HTTPException(403, "Only students can create practice quizzes")

    # Get questions from selected domains (or all in subject)
    query = select(Question).join(Domain, Question.domain_id == Domain.id).where(Domain.subject_id == body.subject_id)
    if body.domain_ids:
        domain_uuids = [uuid_module.UUID(d) for d in body.domain_ids]
        query = query.where(Question.domain_id.in_(domain_uuids))

    result = await db.execute(query)
    all_questions = result.scalars().all()

    if not all_questions:
        raise HTTPException(400, "No questions available for selected domains")

    target = min(body.questions_count, len(all_questions))
    if target <= 0:
        raise HTTPException(400, "questions_count must be at least 1")
    selected = random.sample(all_questions, target)
    random.shuffle(selected)

    questions_order = []
    for q in selected:
        num_choices = len(q.choices)
        choices_order = list(range(num_choices))
        random.shuffle(choices_order)
        questions_order.append({
            "question_id": str(q.id),
            "choices_order": choices_order,
        })

    # Create quiz without a session (session_id = None would break FK, so we use a special marker)
    # We'll create a practice session on the fly
    from app.models.session import Session as SessionModel
    practice_session = SessionModel(
        subject_id=body.subject_id,
        title=f"Practice — {user.full_name}",
        created_by=user.id,
        domain_ids=body.domain_ids or [],
        questions_per_quiz=target,
        is_active=False,  # Not a real session
    )
    db.add(practice_session)
    await db.flush()

    quiz = StudentQuiz(
        session_id=practice_session.id,
        student_id=user.id,
        questions_order=questions_order,
        total_questions=target,
    )
    db.add(quiz)
    await db.commit()
    await db.refresh(quiz)

    return {
        "quiz_id": str(quiz.id),
        "total_questions": quiz.total_questions,
        "is_practice": True,
    }


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

    # Enforce session-level time limit: block new joins after time has expired
    if session.time_limit_minutes and session.activated_at:
        elapsed = (datetime.now(timezone.utc) - session.activated_at).total_seconds()
        if elapsed > session.time_limit_minutes * 60:
            raise HTTPException(400, "Exam time has expired. No new submissions accepted.")

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

    # Auto-submit server-side if student's time has expired
    if not quiz.submitted_at and session and session.time_limit_minutes and quiz.started_at:
        elapsed = (datetime.now(timezone.utc) - quiz.started_at).total_seconds()
        if elapsed > session.time_limit_minutes * 60:
            await grade_quiz(db, quiz)
            await db.commit()
            await db.refresh(quiz)

    is_practice = bool(session and (not session.is_active or session.title.startswith("Practice")))
    return QuizMetaResponse(
        quiz_id=str(quiz.id),
        session_id=str(quiz.session_id),
        session_title=session.title if session else "",
        total_questions=quiz.total_questions,
        time_limit_minutes=session.time_limit_minutes if session else None,
        started_at=quiz.started_at.isoformat(),
        submitted_at=quiz.submitted_at.isoformat() if quiz.submitted_at else None,
        is_practice=is_practice,
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

    grade_result = await grade_quiz(db, quiz)
    results = await _build_quiz_results(quiz, db)

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

    results = await _build_quiz_results(quiz, db)

    return SubmitResponse(
        score=quiz.score or 0,
        total_correct=quiz.total_correct or 0,
        total_questions=quiz.total_questions,
        results=results,
    )


@router.post("/quiz/{quiz_id}/violation")
async def report_violation(
    quiz_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Record a tab-switch / focus-loss violation for this quiz. Idempotent — only counts while quiz is active."""
    result = await db.execute(select(StudentQuiz).where(StudentQuiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    if not quiz or str(quiz.student_id) != str(user.id):
        raise HTTPException(404, "Quiz not found")
    if not quiz.submitted_at:
        quiz.violation_count = (quiz.violation_count or 0) + 1
        await db.commit()
    return {"violation_count": quiz.violation_count}


@router.delete("/quiz/{quiz_id}")
async def delete_practice_quiz(
    quiz_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a practice quiz. Only the owning student can delete, and only practice quizzes."""
    result = await db.execute(select(StudentQuiz).where(StudentQuiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    if not quiz or str(quiz.student_id) != str(user.id):
        raise HTTPException(404, "Quiz not found")

    # Verify it's a practice quiz (session is_active=False and title starts with "Practice")
    session_result = await db.execute(select(Session).where(Session.id == quiz.session_id))
    session = session_result.scalar_one_or_none()
    if not session or session.is_active or not session.title.startswith("Practice"):
        raise HTTPException(403, "Only practice quizzes can be deleted")

    # Delete answers, then quiz, then the practice session (order matters for FK constraints)
    await db.execute(sa_delete(StudentAnswer).where(StudentAnswer.student_quiz_id == quiz.id))
    await db.execute(sa_delete(StudentQuiz).where(StudentQuiz.id == quiz.id))
    await db.execute(sa_delete(Session).where(Session.id == session.id))
    await db.commit()
    return {"ok": True}
