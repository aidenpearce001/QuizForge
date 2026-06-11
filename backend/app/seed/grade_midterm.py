"""
Midterm grading script:
  1. Verify all exam questions (answers + explanations) via LLM
  2. Fix any wrong answers or missing/bad explanations
  3. Re-grade all student_answers and student_quizzes for the target sessions
  4. Print score report per session
"""
import asyncio
import json
import httpx
from datetime import datetime, timezone
from sqlalchemy import select, update
from app.database import async_session
from app.models.question import Question
from app.models.session import Session
from app.models.student_quiz import StudentQuiz
from app.models.student_answer import StudentAnswer
from app.config import settings

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemini-2.0-flash-001"
BATCH_SIZE = 10

SESSION_IDS = [
    "dcc9a904-b66f-48c8-85cb-520c555e3518",
    "fefdceb9-1633-4515-8dc4-d0cd54e7712f",
    "c0f2896e-656b-46f9-978a-a9e75d027155",
]


# ──────────────────────────────────────────────
# LLM helpers
# ──────────────────────────────────────────────

def en_only(text: str, sep: str) -> str:
    idx = text.find(sep)
    return text[:idx].strip() if idx != -1 else text.strip()


def build_verify_prompt(questions: list[dict]) -> str:
    body = ""
    for i, q in enumerate(questions):
        q_en = en_only(q["question_text"], "\n\n")
        body += f'\n{i+1}. [{q["type"]}] {q_en[:500]}\n'
        for j, c in enumerate(q["choices"]):
            c_en = en_only(c["text"], "\n")
            mark = "✓" if c["is_correct"] else " "
            body += f'   [{mark}] {j}: {c_en[:300]}\n'
        if q.get("explanation"):
            body += f'   Current explanation: {q["explanation"][:400]}\n'

    return f"""You are an AWS Cloud Practitioner exam expert. Review each question below carefully.

For each question return a JSON object with:
- "correct_indices": int (single) or int[] (multiple) — the 0-based index/indices of the correct answer(s)
- "answer_ok": true if the currently marked answer (✓) is correct, false otherwise
- "explanation": a concise 2-3 sentence explanation of WHY the correct answer is right (in English only)

{body}

Return ONLY a JSON array (one object per question, in order). Example for 3 questions:
[
  {{"correct_indices": 2, "answer_ok": true, "explanation": "..."}},
  {{"correct_indices": [0, 3], "answer_ok": false, "explanation": "..."}},
  {{"correct_indices": 1, "answer_ok": true, "explanation": "..."}}
]"""


async def verify_batch(client: httpx.AsyncClient, questions: list[dict]) -> list | None:
    prompt = build_verify_prompt(questions)
    try:
        resp = await client.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,
            },
            timeout=180,
        )
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"].strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(raw)
    except Exception as e:
        print(f"    LLM error: {e}")
        return None


# ──────────────────────────────────────────────
# Grading helpers
# ──────────────────────────────────────────────

def check_correct(question: Question, selected: list[int]) -> bool:
    correct = {i for i, c in enumerate(question.choices) if c.get("is_correct")}
    return set(selected) == correct


async def regrade_quiz(db, quiz: StudentQuiz, questions_by_id: dict) -> dict:
    """Re-grade all answers for a quiz and update quiz totals."""
    ans_result = await db.execute(
        select(StudentAnswer).where(StudentAnswer.student_quiz_id == quiz.id)
    )
    answers = ans_result.scalars().all()

    total_correct = 0
    for ans in answers:
        q = questions_by_id.get(str(ans.question_id))
        if not q:
            continue
        is_correct = check_correct(q, ans.selected_choices or [])
        ans.is_correct = is_correct
        if is_correct:
            total_correct += 1

    total_q = quiz.total_questions or len(quiz.questions_order)
    answered = len(answers)
    score = round((total_correct / total_q) * 100, 1) if total_q else 0

    quiz.total_correct = total_correct
    quiz.total_questions = total_q
    quiz.score = score

    return {
        "student_id": str(quiz.student_id),
        "quiz_id": str(quiz.id),
        "total_correct": total_correct,
        "answered": answered,
        "total_q": total_q,
        "score": score,
        "submitted": quiz.submitted_at is not None,
    }


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

async def main():
    if not settings.openrouter_api_key:
        print("ERROR: OPENROUTER_API_KEY not set")
        return

    async with async_session() as db:

        # ── Step 1: fetch all exam questions ──────────────────────────────
        exam_q_result = await db.execute(
            select(Question).where(Question.for_exam.is_(True)).order_by(Question.id)
        )
        exam_questions = exam_q_result.scalars().all()
        print(f"Step 1: Verifying {len(exam_questions)} exam questions via LLM...")

        fixed_answers = 0
        fixed_explanations = 0
        total_batches = (len(exam_questions) + BATCH_SIZE - 1) // BATCH_SIZE

        async with httpx.AsyncClient(timeout=180) as client:
            for i in range(0, len(exam_questions), BATCH_SIZE):
                batch = exam_questions[i: i + BATCH_SIZE]
                batch_num = i // BATCH_SIZE + 1

                batch_data = [
                    {
                        "question_text": q.question_text,
                        "choices": q.choices,
                        "type": q.question_type,
                        "explanation": q.explanation or "",
                    }
                    for q in batch
                ]

                print(f"  Batch {batch_num}/{total_batches} ({i+1}-{min(i+BATCH_SIZE, len(exam_questions))})...", end=" ", flush=True)
                results = await verify_batch(client, batch_data)

                if results is None or len(results) != len(batch):
                    print(f"SKIP (unexpected response)")
                    continue

                batch_fixed_a = 0
                batch_fixed_e = 0
                for q, r in zip(batch, results):
                    changed = False

                    # Fix answer if wrong
                    if not r.get("answer_ok", True):
                        ci = r.get("correct_indices", [])
                        if isinstance(ci, int):
                            ci = [ci]
                        ci = sorted(int(x) for x in ci)
                        if ci and all(x < len(q.choices) for x in ci):
                            q.choices = [
                                {"text": c["text"], "is_correct": j in ci}
                                for j, c in enumerate(q.choices)
                            ]
                            changed = True
                            batch_fixed_a += 1
                            fixed_answers += 1
                            q_en = en_only(q.question_text, "\n\n")
                            print(f"\n    FIXED ANSWER: {q_en[:80]}")

                    # Always update explanation if LLM gave one
                    new_exp = r.get("explanation", "").strip()
                    if new_exp and new_exp != (q.explanation or "").strip():
                        q.explanation = new_exp
                        batch_fixed_e += 1
                        fixed_explanations += 1

                await db.commit()
                print(f"answers fixed: {batch_fixed_a}, explanations updated: {batch_fixed_e}")

        print(f"\nStep 1 done — {fixed_answers} answers corrected, {fixed_explanations} explanations updated.\n")

        # ── Step 2: build question lookup for re-grading ─────────────────
        print("Step 2: Re-grading all student quizzes in target sessions...\n")

        # Reload all exam questions (may have changed) + bank questions
        all_q_result = await db.execute(select(Question))
        all_questions = all_q_result.scalars().all()
        questions_by_id = {str(q.id): q for q in all_questions}

        # ── Step 3: re-grade per session ──────────────────────────────────
        grand_report = []

        for sid in SESSION_IDS:
            sess_result = await db.execute(select(Session).where(Session.id == sid))
            session = sess_result.scalar_one_or_none()
            if not session:
                print(f"  Session {sid} not found, skipping")
                continue

            quiz_result = await db.execute(
                select(StudentQuiz)
                .where(StudentQuiz.session_id == sid)
                .order_by(StudentQuiz.submitted_at.nulls_last())
            )
            quizzes = quiz_result.scalars().all()

            session_rows = []
            for quiz in quizzes:
                row = await regrade_quiz(db, quiz, questions_by_id)
                row["session_title"] = session.title
                row["session_id"] = sid
                session_rows.append(row)

            await db.commit()

            # Print session summary
            submitted = [r for r in session_rows if r["submitted"]]
            not_submitted = [r for r in session_rows if not r["submitted"]]
            if submitted:
                avg = sum(r["score"] for r in submitted) / len(submitted)
                scores = sorted(r["score"] for r in submitted)
                print(f"  ─── {session.title} ───────────────────────────────────")
                print(f"  Students: {len(quizzes)} total | {len(submitted)} submitted | {len(not_submitted)} not submitted")
                print(f"  Score:    avg {avg:.1f}% | min {scores[0]}% | max {scores[-1]}%")
                print()

                # Per-student table (submitted only)
                print(f"  {'#':<4} {'Quiz ID':<38} {'Correct':>8} {'Score':>7}")
                print(f"  {'─'*4} {'─'*38} {'─'*8} {'─'*7}")
                for rank, r in enumerate(sorted(submitted, key=lambda x: -x["score"]), 1):
                    print(f"  {rank:<4} {r['quiz_id']:<38} {r['total_correct']:>4}/{r['total_q']:<3} {r['score']:>6.1f}%")
                print()
            else:
                print(f"  ─── {session.title} — no submitted quizzes yet ───────")
                print()

            grand_report.extend(session_rows)

        # ── Step 4: overall summary ───────────────────────────────────────
        all_submitted = [r for r in grand_report if r["submitted"]]
        if all_submitted:
            overall_avg = sum(r["score"] for r in all_submitted) / len(all_submitted)
            print(f"═══ Overall ({len(all_submitted)} submitted across all 3 sessions) ═══")
            print(f"  Average score: {overall_avg:.1f}%")
            buckets = {"≥80%": 0, "60-79%": 0, "40-59%": 0, "<40%": 0}
            for r in all_submitted:
                if r["score"] >= 80:
                    buckets["≥80%"] += 1
                elif r["score"] >= 60:
                    buckets["60-79%"] += 1
                elif r["score"] >= 40:
                    buckets["40-59%"] += 1
                else:
                    buckets["<40%"] += 1
            for label, count in buckets.items():
                bar = "█" * count
                print(f"  {label:>7}: {bar} {count}")
        print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
