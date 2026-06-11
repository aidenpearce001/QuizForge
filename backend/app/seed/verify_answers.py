"""Cross-check all bank questions: ask LLM to identify correct answers and fix mismatches."""
import asyncio
import json
import httpx
from sqlalchemy import select
from app.database import async_session
from app.models.question import Question
from app.config import settings

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
BATCH_SIZE = 15
MODEL = "google/gemini-2.0-flash-001"


def build_prompt(questions: list[dict]) -> str:
    q_list = ""
    for i, q in enumerate(questions):
        # Use English part only (before \n\n) so LLM isn't confused by Vietnamese
        en_text = q["question_text"].split("\n\n")[0]
        q_list += f'\n{i+1}. [{q["type"]}] {en_text[:400]}\n'
        for j, c in enumerate(q["choices"]):
            en_choice = c["text"].split("\n")[0]
            q_list += f'   {j}: {en_choice[:200]}\n'
        if q.get("explanation"):
            q_list += f'   Hint: {q["explanation"][:300]}\n'

    return f"""You are an AWS Cloud Practitioner exam expert. For each question, identify the correct answer choice index (0-based).

Questions marked [single] have exactly ONE correct answer.
Questions marked [multiple] have TWO or more correct answers.

{q_list}

Return ONLY a JSON array with one entry per question (in order).
- For [single]: a single integer (the index of the correct choice)
- For [multiple]: an array of integers (all correct choice indices), sorted ascending

Example for 3 questions (single, multiple, single):
[2, [0, 3], 1]

Return ONLY the JSON array, no other text."""


async def check_batch(client: httpx.AsyncClient, questions: list[dict]) -> list | None:
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
                "temperature": 0.0,
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
        print(f"    LLM error: {e}")
        return None


def get_stored_correct(choices: list[dict]) -> list[int]:
    return sorted(i for i, c in enumerate(choices) if c.get("is_correct"))


def get_llm_correct(answer, q_type: str) -> list[int]:
    if isinstance(answer, int):
        return [answer]
    if isinstance(answer, list):
        return sorted(int(x) for x in answer)
    return []


async def main():
    if not settings.openrouter_api_key:
        print("ERROR: OPENROUTER_API_KEY not set")
        return

    async with async_session() as db:
        result = await db.execute(
            select(Question)
            .where(Question.for_exam.is_(False))
            .order_by(Question.id)
        )
        questions = result.scalars().all()
        total = len(questions)
        print(f"Checking {total} bank questions in batches of {BATCH_SIZE}...")

        fixed = 0
        skipped = 0
        mismatches = 0
        total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE

        async with httpx.AsyncClient(timeout=120) as client:
            for i in range(0, total, BATCH_SIZE):
                batch = questions[i: i + BATCH_SIZE]
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

                print(f"  Batch {batch_num}/{total_batches} ({i+1}-{min(i+BATCH_SIZE, total)})...", end=" ", flush=True)

                answers = await check_batch(client, batch_data)
                if answers is None or len(answers) != len(batch):
                    print(f"SKIP (got {len(answers) if answers else 0} answers for {len(batch)} questions)")
                    skipped += len(batch)
                    continue

                batch_fixed = 0
                for q, answer in zip(batch, answers):
                    stored = get_stored_correct(q.choices)
                    llm = get_llm_correct(answer, q.question_type)

                    if not llm:
                        skipped += 1
                        continue

                    if stored != llm:
                        mismatches += 1
                        # Validate indices are in range
                        if any(idx >= len(q.choices) for idx in llm):
                            skipped += 1
                            continue

                        new_choices = [
                            {"text": c["text"], "is_correct": j in llm}
                            for j, c in enumerate(q.choices)
                        ]
                        q.choices = new_choices
                        fixed += 1
                        batch_fixed += 1

                await db.commit()
                print(f"fixed {batch_fixed} in this batch (total fixed: {fixed}, mismatches so far: {mismatches})")

    print(f"\nDone! Checked {total} questions.")
    print(f"  Mismatches found: {mismatches}")
    print(f"  Fixed:            {fixed}")
    print(f"  Skipped:          {skipped}")


if __name__ == "__main__":
    asyncio.run(main())
