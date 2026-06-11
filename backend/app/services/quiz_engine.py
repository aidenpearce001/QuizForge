import random
import math
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question import Question
from app.models.session import Session, SessionQuestion
from app.models.student_quiz import StudentQuiz


async def generate_quiz_for_student(
    db: AsyncSession, session: Session, student_id: str
) -> StudentQuiz:
    """Generate a unique shuffled quiz for a student.

    1. Fetch question pool grouped by domain
    2. Select proportional random subset (largest-remainder method)
    3. Shuffle order and choices
    """
    # Check if student already has a quiz (use first() to survive duplicate rows)
    existing = await db.execute(
        select(StudentQuiz)
        .where(
            StudentQuiz.session_id == session.id,
            StudentQuiz.student_id == student_id,
        )
        .order_by(StudentQuiz.started_at.desc())
        .limit(1)
    )
    existing_quiz = existing.scalar_one_or_none()
    if existing_quiz:
        return existing_quiz

    # Fetch pool
    result = await db.execute(
        select(Question)
        .join(SessionQuestion, SessionQuestion.question_id == Question.id)
        .where(SessionQuestion.session_id == session.id)
    )
    all_questions = result.scalars().all()

    total_pool = len(all_questions)
    target = min(session.questions_per_quiz, total_pool)

    selected = []
    if total_pool > 0 and session.exam_ratio is not None:
        # Weighted sampling: exam_ratio% from exam questions, rest from domain bank
        exam_qs = [q for q in all_questions if q.for_exam]
        domain_qs = [q for q in all_questions if not q.for_exam]

        target_exam = min(round(target * session.exam_ratio / 100), len(exam_qs))
        target_domain = min(target - target_exam, len(domain_qs))
        # Fill any remaining slots from whichever group has more
        shortage = target - target_exam - target_domain
        if shortage > 0:
            extra_exam = min(shortage, len(exam_qs) - target_exam)
            target_exam += extra_exam
            target_domain = min(target - target_exam, len(domain_qs))

        selected = (
            random.sample(exam_qs, target_exam)
            + random.sample(domain_qs, target_domain)
        )
    elif total_pool > 0:
        # Proportional selection by domain with largest-remainder method
        by_domain = defaultdict(list)
        for q in all_questions:
            by_domain[str(q.domain_id)].append(q)

        allocations = {}
        remainders = {}
        allocated = 0

        for domain_id, questions in by_domain.items():
            proportion = len(questions) / total_pool
            exact = proportion * target
            floor_val = math.floor(exact)
            allocations[domain_id] = floor_val
            remainders[domain_id] = exact - floor_val
            allocated += floor_val

        # Distribute remaining slots
        remaining = target - allocated
        sorted_domains = sorted(remainders.keys(), key=lambda d: remainders[d], reverse=True)
        for i in range(remaining):
            allocations[sorted_domains[i % len(sorted_domains)]] += 1

        for domain_id, count in allocations.items():
            pool = by_domain[domain_id]
            count = min(count, len(pool))
            selected.extend(random.sample(pool, count))

    # Shuffle question order
    random.shuffle(selected)

    # Generate shuffled choice indices for each question
    questions_order = []
    for q in selected:
        num_choices = len(q.choices)
        choices_order = list(range(num_choices))
        random.shuffle(choices_order)
        questions_order.append({
            "question_id": str(q.id),
            "choices_order": choices_order,
        })

    quiz = StudentQuiz(
        session_id=session.id,
        student_id=student_id,
        questions_order=questions_order,
        total_questions=len(selected),
    )
    db.add(quiz)
    await db.commit()
    await db.refresh(quiz)
    return quiz
