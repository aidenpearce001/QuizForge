from pydantic import BaseModel


class QuizMetaResponse(BaseModel):
    quiz_id: str
    session_title: str
    total_questions: int
    time_limit_minutes: int | None
    started_at: str
    submitted_at: str | None


class QuizQuestionResponse(BaseModel):
    question_number: int
    total_questions: int
    question_text: str
    question_type: str
    domain_name: str
    choices: list[dict]  # [{index: int, text: str}] -- shuffled order, no is_correct
    selected_choices: list[int] | None  # Previously saved answer (original indices)


class SubmitResponse(BaseModel):
    score: float
    total_correct: int
    total_questions: int
    results: list[dict]  # Per-question results
