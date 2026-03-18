from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.subject import Subject
from app.models.domain import Domain
from app.models.question import Question
from app.models.user import User
from app.services.auth import require_instructor
from app.schemas.subject import SubjectCreate, SubjectResponse, DomainInSubject

router = APIRouter(prefix="/api/subjects", tags=["subjects"])


@router.get("", response_model=list[SubjectResponse])
async def list_subjects(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Subject)
        .order_by(Subject.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    return [
        SubjectResponse(
            id=str(s.id),
            name=s.name,
            description=s.description,
            created_at=s.created_at.isoformat(),
        )
        for s in result.scalars()
    ]


@router.post("", response_model=SubjectResponse)
async def create_subject(
    body: SubjectCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_instructor),
):
    subject = Subject(name=body.name, description=body.description, created_by=user.id)
    db.add(subject)
    await db.commit()
    await db.refresh(subject)
    return SubjectResponse(
        id=str(subject.id),
        name=subject.name,
        description=subject.description,
        created_at=subject.created_at.isoformat(),
    )


@router.get("/{subject_id}/domains", response_model=list[DomainInSubject])
async def list_domains(
    subject_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Domain, func.count(Question.id).label("qcount"))
        .outerjoin(Question, Question.domain_id == Domain.id)
        .where(Domain.subject_id == subject_id)
        .group_by(Domain.id)
        .order_by(Domain.name)
        .offset((page - 1) * limit)
        .limit(limit)
    )
    return [
        DomainInSubject(
            id=str(row[0].id),
            name=row[0].name,
            description=row[0].description,
            question_count=row[1],
        )
        for row in result.all()
    ]
