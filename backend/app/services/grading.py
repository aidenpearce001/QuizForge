from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student_quiz import StudentQuiz
from app.models.student_answer import StudentAnswer
from app.models.question import Question


async def grade_quiz(db: AsyncSession, quiz: StudentQuiz) -> dict:
    """Grade a submitted quiz and return results."""
    result = await db.execute(
        select(StudentAnswer).where(StudentAnswer.student_quiz_id == quiz.id)
    )
    answers = result.scalars().all()

    total_correct = sum(1 for a in answers if a.is_correct)
    total_questions = quiz.total_questions
    score = (total_correct / total_questions * 100) if total_questions > 0 else 0

    quiz.submitted_at = datetime.now(timezone.utc)
    quiz.score = round(score, 1)
    quiz.total_correct = total_correct
    await db.commit()

    return {
        "score": quiz.score,
        "total_correct": total_correct,
        "total_questions": total_questions,
    }


def check_answer(question: Question, selected_choices: list[int]) -> bool:
    """Check if selected choices (original indices) are correct."""
    correct_indices = {i for i, c in enumerate(question.choices) if c.get("is_correct")}
    return set(selected_choices) == correct_indices
