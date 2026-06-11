"""Fix questions where all choices have is_correct=False by using LLM to identify correct answers."""
import asyncio
import json
import httpx
from sqlalchemy import select, text
from app.database import async_session
from app.models.question import Question
from app.config import settings

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
BATCH_SIZE = 15
MODEL = "google/gemini-2.0-flash-001"


def build_prompt(questions: list[dict]) -> str:
    q_list = ""
    for i, q in enumerate(questions):
        q_list += f'\n{i+1}. [{q["type"]}] {q["question_text"][:400]}\n'
        for j, c in enumerate(q["choices"]):
            q_list += f'   {j}: {c["text"][:200]}\n'
        if q.get("explanation"):
            q_list += f'   Explanation hint: {q["explanation"][:300]}\n'

    return f"""You are an AWS Cloud Practitioner exam expert. For each question below, identify the correct answer choice index (0-based).

Questions marked [single] have exactly ONE correct answer.
Questions marked [multiple] have TWO or more correct answers.

{q_list}

Return ONLY a JSON array with one entry per question.
- For [single]: a single integer (the index of the correct choice)
- For [multiple]: an array of integers (all correct choice indices)

Example for 3 questions (single, multiple, single):
[2, [0, 3], 1]

Return ONLY the JSON array, no other text."""


async def fix_batch(client: httpx.AsyncClient, questions: list[dict]) -> list:
    prompt = build_prompt(questions)
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
                "temperature": 0.1,
            },
            timeout=120,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"].strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            content = content.rsplit("```", 1)[0]
        return json.loads(content)
    except Exception as e:
        print(f"  LLM error: {e}")
        return []


async def main():
    async with async_session() as db:
        # Fetch all questions with no correct answers
        result = await db.execute(
            text("""
                SELECT id FROM questions
                WHERE NOT EXISTS (
                    SELECT 1 FROM jsonb_array_elements(choices) AS c
                    WHERE (c->>'is_correct')::boolean = true
                )
                ORDER BY id
            """)
        )
        broken_ids = [str(r[0]) for r in result.fetchall()]
        print(f"Found {len(broken_ids)} questions with no correct answer")

        if not broken_ids:
            print("Nothing to fix!")
            return

        # Load full question objects
        q_result = await db.execute(
            select(Question).where(Question.id.in_(broken_ids))
        )
        questions = q_result.scalars().all()

        fixed = 0
        skipped = 0
        async with httpx.AsyncClient(timeout=120) as client:
            for i in range(0, len(questions), BATCH_SIZE):
                batch = questions[i : i + BATCH_SIZE]
                batch_data = [
                    {
                        "question_text": q.question_text,
                        "choices": q.choices,
                        "type": q.question_type,
                        "explanation": q.explanation or "",
                    }
                    for q in batch
                ]

                batch_num = i // BATCH_SIZE + 1
                total_batches = (len(questions) + BATCH_SIZE - 1) // BATCH_SIZE
                print(f"  Batch {batch_num}/{total_batches} ({i+1}-{min(i+BATCH_SIZE, len(questions))})...")

                answers = await fix_batch(client, batch_data)

                if len(answers) != len(batch):
                    print(f"  Warning: got {len(answers)} answers for {len(batch)} questions, skipping")
                    skipped += len(batch)
                    continue

                for q, answer in zip(batch, answers):
                    try:
                        # Normalize to list of indices
                        correct_indices = [answer] if isinstance(answer, int) else list(answer)
                        if not correct_indices:
                            skipped += 1
                            continue

                        # Update choices with correct is_correct flags
                        new_choices = []
                        for j, choice in enumerate(q.choices):
                            new_choices.append({
                                "text": choice["text"],
                                "is_correct": j in correct_indices,
                            })
                        q.choices = new_choices
                        fixed += 1
                    except Exception as e:
                        print(f"  Error updating question {q.id}: {e}")
                        skipped += 1

                await db.commit()
                print(f"  Fixed {fixed} so far, skipped {skipped}")

        print(f"\nDone! Fixed {fixed} questions, skipped {skipped}.")


if __name__ == "__main__":
    asyncio.run(main())
