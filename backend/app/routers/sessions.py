import io
import uuid as uuid_module
import qrcode
import base64
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings
from app.models.user import User
from app.models.question import Question
from app.models.session import Session, SessionQuestion
from app.models.student_quiz import StudentQuiz
from app.models.student_answer import StudentAnswer
from app.services.auth import require_instructor
from app.schemas.session import (
    SessionCreate,
    SessionResponse,
    AttendanceEntry,
    SessionResultEntry,
)

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def generate_qr_base64(url: str) -> str:
    qr = qrcode.make(url)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


@router.post("", response_model=SessionResponse)
async def create_session(
    body: SessionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_instructor),
):
    session = Session(
        subject_id=body.subject_id,
        title=body.title,
        created_by=user.id,
        domain_ids=body.domain_ids,
        questions_per_quiz=body.questions_per_quiz,
        time_limit_minutes=body.time_limit_minutes,
    )
    db.add(session)
    await db.flush()

    # [C3] Convert string domain_ids to UUIDs for the query
    domain_uuids = [uuid_module.UUID(d) for d in body.domain_ids]
    result = await db.execute(
        select(Question).where(Question.domain_id.in_(domain_uuids))
    )
    questions = result.scalars().all()
    for q in questions:
        db.add(SessionQuestion(session_id=session.id, question_id=q.id))

    await db.commit()
    await db.refresh(session)

    return SessionResponse(
        id=str(session.id),
        subject_id=str(session.subject_id),
        title=session.title,
        domain_ids=session.domain_ids,
        questions_per_quiz=session.questions_per_quiz,
        time_limit_minutes=session.time_limit_minutes,
        is_active=session.is_active,
        created_at=session.created_at.isoformat(),
        question_pool_size=len(questions),
    )


@router.get("", response_model=list[SessionResponse])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_instructor),
):
    result = await db.execute(select(Session).order_by(Session.created_at.desc()))
    sessions = result.scalars().all()
    responses = []
    for s in sessions:
        pool_result = await db.execute(
            select(func.count(SessionQuestion.id)).where(
                SessionQuestion.session_id == s.id
            )
        )
        pool_size = pool_result.scalar()
        responses.append(
            SessionResponse(
                id=str(s.id),
                subject_id=str(s.subject_id),
                title=s.title,
                domain_ids=s.domain_ids or [],
                questions_per_quiz=s.questions_per_quiz,
                time_limit_minutes=s.time_limit_minutes,
                is_active=s.is_active,
                created_at=s.created_at.isoformat(),
                question_pool_size=pool_size,
            )
        )
    return responses


@router.get("/{session_id}")
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found")

    pool_result = await db.execute(
        select(func.count(SessionQuestion.id)).where(
            SessionQuestion.session_id == session.id
        )
    )
    pool_size = pool_result.scalar()

    qr_url = f"{settings.frontend_url}/session/{session_id}"
    qr_base64 = generate_qr_base64(qr_url)

    return {
        "id": str(session.id),
        "subject_id": str(session.subject_id),
        "subject_name": session.subject.name if session.subject else None,
        "title": session.title,
        "domain_ids": session.domain_ids or [],
        "questions_per_quiz": session.questions_per_quiz,
        "time_limit_minutes": session.time_limit_minutes,
        "is_active": session.is_active,
        "created_at": session.created_at.isoformat(),
        "question_pool_size": pool_size,
        "qr_code": qr_base64,
        "qr_url": qr_url,
    }


@router.put("/{session_id}/toggle")
async def toggle_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_instructor),
):
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found")
    session.is_active = not session.is_active
    await db.commit()
    return {"is_active": session.is_active}


@router.get("/{session_id}/attendance", response_model=list[AttendanceEntry])
async def get_attendance(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_instructor),
):
    result = await db.execute(
        select(StudentQuiz).where(StudentQuiz.session_id == session_id)
    )
    quizzes = result.scalars().all()
    entries = []
    for q in quizzes:
        # Count answered questions
        ans_result = await db.execute(
            select(func.count(StudentAnswer.id)).where(
                StudentAnswer.student_quiz_id == q.id
            )
        )
        answered = ans_result.scalar()

        if q.submitted_at:
            status = "completed"
        elif answered > 0:
            status = "in_progress"
        else:
            status = "joined"

        entries.append(
            AttendanceEntry(
                student_id=str(q.student_id),
                full_name=q.student.full_name,
                status=status,
                current_question=answered if status == "in_progress" else None,
                total_questions=q.total_questions,
                score=q.score,
            )
        )
    return entries


@router.get("/{session_id}/questions-review")
async def get_session_questions_review(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_instructor),
):
    """Get all questions in a session with answers, explanations, and stats."""
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found")

    # Get session questions with explicit eager loading
    from sqlalchemy.orm import selectinload
    sq_result = await db.execute(
        select(SessionQuestion)
        .where(SessionQuestion.session_id == session_id)
        .options(
            selectinload(SessionQuestion.question).selectinload(Question.domain)
        )
    )
    session_questions = sq_result.scalars().all()

    # Get all submitted quizzes for stats
    quiz_result = await db.execute(
        select(StudentQuiz).where(
            StudentQuiz.session_id == session_id,
            StudentQuiz.submitted_at.isnot(None),
        )
    )
    quizzes = quiz_result.scalars().all()

    # Build per-question answer stats
    q_stats: dict[str, dict] = {}
    for quiz in quizzes:
        for a in quiz.answers:
            qid = str(a.question_id)
            if qid not in q_stats:
                q_stats[qid] = {"correct": 0, "total": 0, "correct_students": [], "incorrect_students": []}
            q_stats[qid]["total"] += 1
            if a.is_correct:
                q_stats[qid]["correct"] += 1
                q_stats[qid]["correct_students"].append(quiz.student.full_name)
            else:
                q_stats[qid]["incorrect_students"].append(quiz.student.full_name)

    # Build question lookup from session pool
    question_map = {}
    for sq in session_questions:
        if sq.question:
            question_map[str(sq.question.id)] = sq.question

    # Include ALL session pool questions, not just answered ones
    questions = []
    for qid, q in question_map.items():
        stats = q_stats.get(qid, {"correct": 0, "total": 0, "correct_students": [], "incorrect_students": []})
        rate = round(stats["correct"] / stats["total"] * 100, 1) if stats["total"] > 0 else None

        questions.append({
            "question_id": qid,
            "question_text": q.question_text,
            "question_type": q.question_type,
            "domain_name": q.domain.name if q.domain else "",
            "choices": q.choices,
            "explanation": q.explanation,
            "correct_rate": rate,
            "total_attempts": stats["total"],
            "correct_count": stats["correct"],
            "correct_students": stats["correct_students"],
            "incorrect_students": stats["incorrect_students"],
        })

    # Sort: answered questions by correct_rate ascending (hardest first), unanswered at end
    questions.sort(key=lambda q: (q["correct_rate"] is None, q["correct_rate"] or 0))

    return {
        "session_title": session.title,
        "total_questions": len(questions),
        "questions": questions,
    }


@router.get("/{session_id}/leaderboard")
async def get_leaderboard(session_id: str, db: AsyncSession = Depends(get_db)):
    """Public endpoint — students can see rankings after submitting."""
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found")

    result = await db.execute(
        select(StudentQuiz).where(
            StudentQuiz.session_id == session_id,
            StudentQuiz.submitted_at.isnot(None),
        )
    )
    quizzes = result.scalars().all()

    entries = []
    for q in quizzes:
        time_taken = None
        if q.submitted_at and q.started_at:
            time_taken = int((q.submitted_at - q.started_at).total_seconds())
        entries.append({
            "full_name": q.student.full_name,
            "score": q.score or 0,
            "total_correct": q.total_correct or 0,
            "total_questions": q.total_questions,
            "time_taken_seconds": time_taken,
        })

    # Sort by score desc, then time_taken asc (faster is better)
    entries.sort(key=lambda e: (-e["score"], e["time_taken_seconds"] or float("inf")))

    # Add rank
    for i, entry in enumerate(entries):
        entry["rank"] = i + 1

    return {
        "session_title": session.title,
        "entries": entries,
    }


@router.get("/{session_id}/results")
async def get_results(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_instructor),
):
    result = await db.execute(
        select(StudentQuiz).where(
            StudentQuiz.session_id == session_id,
            StudentQuiz.submitted_at.isnot(None),
        )
    )
    quizzes = result.scalars().all()

    # [I4] Track per-question correct counts for hardest question metric
    question_correct_counts: dict[str, int] = {}
    question_total_counts: dict[str, int] = {}
    question_text_map: dict[str, str] = {}

    entries = []
    for q in quizzes:
        time_taken = None
        if q.submitted_at and q.started_at:
            time_taken = int((q.submitted_at - q.started_at).total_seconds())

        # Domain breakdown
        domain_scores: dict[str, dict] = {}
        for a in q.answers:
            domain_name = a.question.domain.name if a.question.domain else "Unknown"
            if domain_name not in domain_scores:
                domain_scores[domain_name] = {"correct": 0, "total": 0}
            domain_scores[domain_name]["total"] += 1
            if a.is_correct:
                domain_scores[domain_name]["correct"] += 1

            # Track for hardest question
            qid = str(a.question_id)
            question_total_counts[qid] = question_total_counts.get(qid, 0) + 1
            if a.is_correct:
                question_correct_counts[qid] = question_correct_counts.get(qid, 0) + 1
            else:
                question_correct_counts.setdefault(qid, 0)
            question_text_map[qid] = a.question.question_text

        entries.append(
            SessionResultEntry(
                student_id=str(q.student_id),
                full_name=q.student.full_name,
                score=q.score or 0,
                total_correct=q.total_correct or 0,
                total_questions=q.total_questions,
                time_taken_seconds=time_taken,
                domain_scores=domain_scores,
            )
        )

    sorted_entries = sorted(entries, key=lambda e: e.score, reverse=True)

    # [I4] Compute hardest question
    hardest_question = None
    if question_total_counts:
        hardest_qid = min(
            question_total_counts.keys(),
            key=lambda qid: question_correct_counts.get(qid, 0)
            / question_total_counts[qid],
        )
        total = question_total_counts[hardest_qid]
        correct = question_correct_counts.get(hardest_qid, 0)
        hardest_question = {
            "question_id": hardest_qid,
            "question_text": question_text_map.get(hardest_qid, ""),
            "correct_rate": round(correct / total * 100, 1) if total > 0 else 0,
            "total_attempts": total,
        }

    # Build per-question stats with who answered correctly
    question_stats = []
    for qid in question_total_counts:
        total = question_total_counts[qid]
        correct = question_correct_counts.get(qid, 0)
        # Find who answered this question correctly/incorrectly
        correct_students = []
        incorrect_students = []
        for q in quizzes:
            for a in q.answers:
                if str(a.question_id) == qid:
                    if a.is_correct:
                        correct_students.append(q.student.full_name)
                    else:
                        incorrect_students.append(q.student.full_name)
        question_stats.append({
            "question_id": qid,
            "question_text": question_text_map.get(qid, ""),
            "correct_rate": round(correct / total * 100, 1) if total > 0 else 0,
            "total_attempts": total,
            "correct_count": correct,
            "correct_students": correct_students,
            "incorrect_students": incorrect_students,
        })

    # Sort by correct_rate ascending (hardest first)
    question_stats.sort(key=lambda q: q["correct_rate"])

    return {
        "results": [e.model_dump() for e in sorted_entries],
        "hardest_question": hardest_question,
        "question_stats": question_stats,
    }
