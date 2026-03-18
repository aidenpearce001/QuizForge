import json
import pdfplumber
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.domain import Domain
from app.models.question import Question
from app.models.pdf_upload import PdfUpload

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def build_parsing_prompt(text: str, domains: list[dict]) -> str:
    domain_list = "\n".join(f"- {d['name']}: {d['description']}" for d in domains)
    return f"""You are a quiz question extractor. Parse the following text and extract all quiz questions.

For each question, determine:
1. The question text
2. The answer choices (each with text and whether it's correct)
3. The question type: "single" (one correct answer), "multiple" (multiple correct), or "true_false"
4. Which domain it belongs to from this list:
{domain_list}
5. A brief explanation of why the correct answer is correct

Return a JSON array of objects with this exact structure:
[
  {{
    "question_text": "...",
    "question_type": "single|multiple|true_false",
    "domain": "exact domain name from list above",
    "choices": [
      {{"text": "...", "is_correct": true}},
      {{"text": "...", "is_correct": false}}
    ],
    "explanation": "..."
  }}
]

Return ONLY the JSON array, no other text.

--- TEXT START ---
{text[:15000]}
--- TEXT END ---"""


async def parse_pdf_with_llm(
    db: AsyncSession, pdf_upload: PdfUpload, domains: list[Domain]
) -> int:
    """Extract text from PDF, send to LLM, store questions. Returns count."""
    pdf_upload.status = "processing"
    await db.commit()

    try:
        text = extract_text_from_pdf(pdf_upload.file_path)
        if not text.strip():
            raise ValueError("No text extracted from PDF")

        domain_info = [{"name": d.name, "description": d.description or ""} for d in domains]
        prompt = build_parsing_prompt(text, domain_info)

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {settings.openrouter_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "google/gemini-2.0-flash-001",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                },
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]

        # Parse JSON from response (handle markdown code blocks)
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            content = content.rsplit("```", 1)[0]

        questions_data = json.loads(content)

        # Build domain name->id mapping
        domain_map = {d.name: d.id for d in domains}

        count = 0
        for q in questions_data:
            domain_name = q.get("domain", "")
            domain_id = domain_map.get(domain_name)
            if not domain_id:
                # Try fuzzy match
                for name, did in domain_map.items():
                    if domain_name.lower() in name.lower() or name.lower() in domain_name.lower():
                        domain_id = did
                        break
            if not domain_id:
                domain_id = list(domain_map.values())[0]  # Fallback to first domain

            question = Question(
                domain_id=domain_id,
                source_pdf_id=pdf_upload.id,
                source="pdf",
                question_text=q["question_text"],
                question_type=q.get("question_type", "single"),
                choices=q["choices"],
                explanation=q.get("explanation"),
            )
            db.add(question)
            count += 1

        pdf_upload.status = "done"
        pdf_upload.questions_extracted = count
        await db.commit()
        return count

    except Exception as e:
        pdf_upload.status = "error"
        pdf_upload.error_message = str(e)[:500]
        await db.commit()
        raise
