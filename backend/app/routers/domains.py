from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.domain import Domain
from app.models.question import Question
from app.models.user import User
from app.services.auth import require_instructor
from app.schemas.domain import DomainCreate, DomainUpdate, DomainResponse

router = APIRouter(prefix="/api", tags=["domains"])


@router.post("/subjects/{subject_id}/domains", response_model=DomainResponse)
async def create_domain(
    subject_id: str,
    body: DomainCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_instructor),
):
    domain = Domain(subject_id=subject_id, name=body.name, description=body.description)
    db.add(domain)
    await db.commit()
    await db.refresh(domain)
    return DomainResponse(
        id=str(domain.id),
        subject_id=str(domain.subject_id),
        name=domain.name,
        description=domain.description,
    )


@router.put("/domains/{domain_id}", response_model=DomainResponse)
async def update_domain(
    domain_id: str,
    body: DomainUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_instructor),
):
    result = await db.execute(select(Domain).where(Domain.id == domain_id))
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(404, "Domain not found")
    if body.name is not None:
        domain.name = body.name
    if body.description is not None:
        domain.description = body.description
    await db.commit()
    await db.refresh(domain)
    return DomainResponse(
        id=str(domain.id),
        subject_id=str(domain.subject_id),
        name=domain.name,
        description=domain.description,
    )


@router.delete("/domains/{domain_id}")
async def delete_domain(
    domain_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_instructor),
):
    result = await db.execute(select(Domain).where(Domain.id == domain_id))
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(404, "Domain not found")
    count_result = await db.execute(
        select(func.count(Question.id)).where(Question.domain_id == domain_id)
    )
    count = count_result.scalar()
    if count > 0:
        raise HTTPException(
            409, f"Domain has {count} questions. Delete or reassign questions first."
        )
    await db.delete(domain)
    await db.commit()
    return {"ok": True}
