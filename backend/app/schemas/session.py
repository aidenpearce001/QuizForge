from pydantic import BaseModel


class SessionCreate(BaseModel):
    subject_id: str
    title: str
    domain_ids: list[str]
    questions_per_quiz: int
    time_limit_minutes: int | None = None


class SessionResponse(BaseModel):
    id: str
    subject_id: str
    title: str
    domain_ids: list[str]
    questions_per_quiz: int
    time_limit_minutes: int | None
    is_active: bool
    created_at: str
    question_pool_size: int = 0


class AttendanceEntry(BaseModel):
    student_id: str
    full_name: str
    status: str  # "joined", "in_progress", "completed"
    current_question: int | None = None
    total_questions: int = 0
    score: float | None = None


class SessionResultEntry(BaseModel):
    student_id: str
    full_name: str
    score: float
    total_correct: int
    total_questions: int
    time_taken_seconds: int | None
    domain_scores: dict[str, dict]  # {domain_name: {correct: int, total: int}}
