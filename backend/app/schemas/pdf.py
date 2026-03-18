from pydantic import BaseModel


class PdfUploadResponse(BaseModel):
    id: str
    filename: str
    status: str
    questions_extracted: int
    error_message: str | None
    uploaded_at: str
