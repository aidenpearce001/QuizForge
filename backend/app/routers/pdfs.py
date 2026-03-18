import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, async_session
from app.models.user import User
from app.models.domain import Domain
from app.models.question import Question
from app.models.pdf_upload import PdfUpload
from app.services.auth import require_instructor
from app.services.pdf_parser import parse_pdf_with_llm
from app.schemas.pdf import PdfUploadResponse

router = APIRouter(prefix="/api/subjects/{subject_id}/pdfs", tags=["pdfs"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


async def _process_pdf(pdf_id: str, subject_id: str):
    """Background task to parse PDF with LLM."""
    async with async_session() as db:
        result = await db.execute(select(PdfUpload).where(PdfUpload.id == pdf_id))
        pdf_upload = result.scalar_one()
        domain_result = await db.execute(
            select(Domain).where(Domain.subject_id == subject_id)
        )
        domains = list(domain_result.scalars())
        await parse_pdf_with_llm(db, pdf_upload, domains)


@router.post("", response_model=list[PdfUploadResponse])
async def upload_pdfs(
    subject_id: str,
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_instructor),
):
    responses = []
    for file in files:
        if not file.filename.endswith(".pdf"):
            raise HTTPException(400, f"File {file.filename} is not a PDF")

        file_id = str(uuid.uuid4())
        file_path = UPLOAD_DIR / f"{file_id}.pdf"
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        pdf_upload = PdfUpload(
            subject_id=subject_id,
            filename=file.filename,
            file_path=str(file_path),
            uploaded_by=user.id,
        )
        db.add(pdf_upload)
        await db.commit()
        await db.refresh(pdf_upload)

        background_tasks.add_task(_process_pdf, str(pdf_upload.id), subject_id)

        responses.append(PdfUploadResponse(
            id=str(pdf_upload.id),
            filename=pdf_upload.filename,
            status=pdf_upload.status,
            questions_extracted=pdf_upload.questions_extracted,
            error_message=pdf_upload.error_message,
            uploaded_at=pdf_upload.uploaded_at.isoformat(),
        ))
    return responses


@router.get("", response_model=list[PdfUploadResponse])
async def list_pdfs(
    subject_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_instructor),
):
    result = await db.execute(
        select(PdfUpload).where(PdfUpload.subject_id == subject_id).order_by(PdfUpload.uploaded_at.desc())
    )
    return [PdfUploadResponse(
        id=str(p.id), filename=p.filename, status=p.status,
        questions_extracted=p.questions_extracted,
        error_message=p.error_message,
        uploaded_at=p.uploaded_at.isoformat(),
    ) for p in result.scalars()]


@router.post("/{pdf_id}/reprocess")
async def reprocess_pdf(
    subject_id: str, pdf_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_instructor),
):
    result = await db.execute(select(PdfUpload).where(PdfUpload.id == pdf_id))
    pdf_upload = result.scalar_one_or_none()
    if not pdf_upload:
        raise HTTPException(404, "PDF not found")
    if pdf_upload.status not in ("error", "done"):
        raise HTTPException(400, "Can only reprocess errored or completed uploads")

    # Delete old questions from this PDF
    await db.execute(delete(Question).where(Question.source_pdf_id == pdf_id))

    pdf_upload.status = "pending"
    pdf_upload.questions_extracted = 0
    pdf_upload.error_message = None
    await db.commit()

    background_tasks.add_task(_process_pdf, pdf_id, subject_id)
    return {"ok": True}


@router.delete("/{pdf_id}")
async def delete_pdf(
    subject_id: str, pdf_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_instructor),
):
    result = await db.execute(select(PdfUpload).where(PdfUpload.id == pdf_id))
    pdf_upload = result.scalar_one_or_none()
    if not pdf_upload:
        raise HTTPException(404, "PDF not found")

    # Delete associated questions
    await db.execute(delete(Question).where(Question.source_pdf_id == pdf_id))
    await db.delete(pdf_upload)
    await db.commit()
    return {"ok": True}
