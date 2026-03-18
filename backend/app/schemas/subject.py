from pydantic import BaseModel


class SubjectCreate(BaseModel):
    name: str
    description: str | None = None


class SubjectResponse(BaseModel):
    id: str
    name: str
    description: str | None
    created_at: str

    class Config:
        from_attributes = True


class DomainInSubject(BaseModel):
    id: str
    name: str
    description: str | None
    question_count: int = 0

    class Config:
        from_attributes = True
