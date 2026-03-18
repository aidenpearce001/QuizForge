from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.domain import Domain
from app.models.domain_cheatsheet import DomainCheatsheet
from app.models.user import User
from app.services.auth import require_instructor

router = APIRouter(prefix="/api/study", tags=["study"])


class StudyCardResponse(BaseModel):
    domain_id: str
    domain_name: str
    content: str


class CheatsheetUpdate(BaseModel):
    content: str


@router.get("/{subject_id}/cards", response_model=list[StudyCardResponse])
async def list_study_cards(
    subject_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Domain, DomainCheatsheet)
        .outerjoin(DomainCheatsheet, DomainCheatsheet.domain_id == Domain.id)
        .where(Domain.subject_id == subject_id)
        .order_by(Domain.name)
        .offset((page - 1) * limit)
        .limit(limit)
    )
    cards = []
    for domain, cheatsheet in result.all():
        if cheatsheet:
            cards.append(
                StudyCardResponse(
                    domain_id=str(domain.id),
                    domain_name=domain.name,
                    content=cheatsheet.content,
                )
            )
    return cards


@router.get("/domain/{domain_id}", response_model=StudyCardResponse)
async def get_study_card(domain_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Domain, DomainCheatsheet)
        .outerjoin(DomainCheatsheet, DomainCheatsheet.domain_id == Domain.id)
        .where(Domain.id == domain_id)
    )
    row = result.one_or_none()
    if not row or not row[1]:
        raise HTTPException(404, "Study card not found")
    domain, cheatsheet = row
    return StudyCardResponse(
        domain_id=str(domain.id),
        domain_name=domain.name,
        content=cheatsheet.content,
    )


@router.put("/domain/{domain_id}", response_model=StudyCardResponse)
async def update_cheatsheet(
    domain_id: str,
    body: CheatsheetUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_instructor),
):
    result = await db.execute(
        select(DomainCheatsheet).where(DomainCheatsheet.domain_id == domain_id)
    )
    cheatsheet = result.scalar_one_or_none()
    if cheatsheet:
        cheatsheet.content = body.content
    else:
        cheatsheet = DomainCheatsheet(domain_id=domain_id, content=body.content)
        db.add(cheatsheet)
    await db.commit()
    domain_result = await db.execute(select(Domain).where(Domain.id == domain_id))
    domain = domain_result.scalar_one()
    return StudyCardResponse(
        domain_id=str(domain.id),
        domain_name=domain.name,
        content=cheatsheet.content,
    )
