from pydantic import BaseModel


class DomainCreate(BaseModel):
    name: str
    description: str | None = None


class DomainUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class DomainResponse(BaseModel):
    id: str
    subject_id: str
    name: str
    description: str | None

    class Config:
        from_attributes = True
