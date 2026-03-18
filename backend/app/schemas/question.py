from pydantic import BaseModel


class ChoiceSchema(BaseModel):
    text: str
    is_correct: bool


class QuestionCreate(BaseModel):
    domain_id: str
    question_text: str
    question_type: str = "single"
    choices: list[ChoiceSchema]
    explanation: str | None = None


class QuestionUpdate(BaseModel):
    question_text: str | None = None
    question_type: str | None = None
    choices: list[ChoiceSchema] | None = None
    explanation: str | None = None
    domain_id: str | None = None


class QuestionResponse(BaseModel):
    id: str
    domain_id: str
    domain_name: str
    question_text: str
    question_type: str
    choices: list[ChoiceSchema]
    explanation: str | None
    source: str
    created_at: str

    class Config:
        from_attributes = True
