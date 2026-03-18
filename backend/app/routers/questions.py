from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.domain import Domain
from app.models.question import Question
from app.models.session import SessionQuestion, Session
from app.models.user import User
from app.services.auth import require_instructor
from app.schemas.question import QuestionUpdate, QuestionResponse, ChoiceSchema

router = APIRouter(prefix="/api", tags=["questions"])


@router.get("/subjects/{subject_id}/questions", response_model=list[QuestionResponse])
async def list_questions(
    subject_id: str,
    domain_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_instructor),
):
    query = (
        select(Question)
        .join(Domain, Question.domain_id == Domain.id)
        .where(Domain.subject_id == subject_id)
        .options(selectinload(Question.domain))
    )
    if domain_id:
        query = query.where(Question.domain_id == domain_id)
    query = query.order_by(Question.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    questions = result.scalars().all()
    return [
        QuestionResponse(
            id=str(q.id),
            domain_id=str(q.domain_id),
            domain_name=q.domain.name,
            question_text=q.question_text,
            question_type=q.question_type,
            choices=[ChoiceSchema(**c) for c in q.choices],
            explanation=q.explanation,
            source=q.source,
            created_at=q.created_at.isoformat(),
        )
        for q in questions
    ]


@router.get("/questions/{question_id}", response_model=QuestionResponse)
async def get_question(
    question_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_instructor),
):
    result = await db.execute(
        select(Question)
        .where(Question.id == question_id)
        .options(selectinload(Question.domain))
    )
    q = result.scalar_one_or_none()
    if not q:
        raise HTTPException(404, "Question not found")
    return QuestionResponse(
        id=str(q.id),
        domain_id=str(q.domain_id),
        domain_name=q.domain.name,
        question_text=q.question_text,
        question_type=q.question_type,
        choices=[ChoiceSchema(**c) for c in q.choices],
        explanation=q.explanation,
        source=q.source,
        created_at=q.created_at.isoformat(),
    )


@router.put("/questions/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: str,
    body: QuestionUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_instructor),
):
    result = await db.execute(
        select(Question)
        .where(Question.id == question_id)
        .options(selectinload(Question.domain))
    )
    q = result.scalar_one_or_none()
    if not q:
        raise HTTPException(404, "Question not found")
    if body.question_text is not None:
        q.question_text = body.question_text
    if body.question_type is not None:
        q.question_type = body.question_type
    if body.choices is not None:
        q.choices = [c.model_dump() for c in body.choices]
    if body.explanation is not None:
        q.explanation = body.explanation
    if body.domain_id is not None:
        q.domain_id = body.domain_id
    await db.commit()
    await db.refresh(q)
    # Re-load domain relationship after refresh
    domain_result = await db.execute(select(Domain).where(Domain.id == q.domain_id))
    domain = domain_result.scalar_one()
    return QuestionResponse(
        id=str(q.id),
        domain_id=str(q.domain_id),
        domain_name=domain.name,
        question_text=q.question_text,
        question_type=q.question_type,
        choices=[ChoiceSchema(**c) for c in q.choices],
        explanation=q.explanation,
        source=q.source,
        created_at=q.created_at.isoformat(),
    )


@router.delete("/questions/{question_id}")
async def delete_question(
    question_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_instructor),
):
    result = await db.execute(select(Question).where(Question.id == question_id))
    q = result.scalar_one_or_none()
    if not q:
        raise HTTPException(404, "Question not found")
    # Check if in active session
    active_result = await db.execute(
        select(SessionQuestion)
        .join(Session, SessionQuestion.session_id == Session.id)
        .where(SessionQuestion.question_id == question_id, Session.is_active == True)
        .limit(1)
    )
    if active_result.scalar_one_or_none():
        raise HTTPException(
            409, "Question is in an active session. Deactivate the session first."
        )
    await db.delete(q)
    await db.commit()
    return {"ok": True}
