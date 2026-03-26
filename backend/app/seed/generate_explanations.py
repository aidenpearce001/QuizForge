"""Generate explanations for questions that don't have one, using OpenRouter LLM."""
import asyncio
import json
import httpx
from sqlalchemy import select, or_
from app.database import async_session
from app.models.question import Question
from app.config import settings

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
BATCH_SIZE = 20  # questions per LLM call
MODEL = "google/gemini-2.0-flash-001"


def build_prompt(questions: list[dict]) -> str:
    q_list = ""
    for i, q in enumerate(questions):
        correct = [c["text"] for c in q["choices"] if c.get("is_correct")]
        q_list += f'\n{i+1}. Q: {q["question_text"][:300]}\n   Correct: {", ".join(correct)}\n'

    return f"""You are an AWS Cloud Practitioner exam tutor. For each question below, write a brief explanation (2-4 sentences) of WHY the correct answer is correct. Be concise and educational. Focus on the key concept being tested.

{q_list}

Return a JSON array of strings, one explanation per question, in the same order.
Example: ["Explanation for Q1...", "Explanation for Q2...", ...]
Return ONLY the JSON array, no other text."""


async def generate_batch(client: httpx.AsyncClient, questions: list[dict]) -> list[str]:
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
                "temperature": 0.2,
            },
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"].strip()

        # Handle markdown code blocks
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            content = content.rsplit("```", 1)[0]

        return json.loads(content)
    except Exception as e:
        print(f"  LLM error: {e}")
        return []


async def main():
    async with async_session() as db:
        # Fetch all questions without explanations
        result = await db.execute(
            select(Question)
            .where(or_(Question.explanation.is_(None), Question.explanation == ""))
            .order_by(Question.id)
        )
        questions = result.scalars().all()
        print(f"Found {len(questions)} questions without explanations")

        if not questions:
            print("Nothing to do!")
            return

        updated = 0
        async with httpx.AsyncClient(timeout=120) as client:
            for i in range(0, len(questions), BATCH_SIZE):
                batch = questions[i:i + BATCH_SIZE]
                batch_data = [
                    {
                        "question_text": q.question_text,
                        "choices": q.choices,
                    }
                    for q in batch
                ]

                print(f"  Processing batch {i // BATCH_SIZE + 1} ({i+1}-{min(i+BATCH_SIZE, len(questions))})...")
                explanations = await generate_batch(client, batch_data)

                if len(explanations) != len(batch):
                    print(f"  Warning: got {len(explanations)} explanations for {len(batch)} questions, skipping batch")
                    continue

                for q, explanation in zip(batch, explanations):
                    if explanation and isinstance(explanation, str) and len(explanation) > 10:
                        q.explanation = explanation
                        updated += 1

                await db.commit()
                print(f"  Updated {updated} so far")

        print(f"\nDone! Updated {updated} questions with explanations.")


if __name__ == "__main__":
    asyncio.run(main())
