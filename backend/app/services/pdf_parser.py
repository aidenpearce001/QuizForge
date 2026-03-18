import json
import re
import pdfplumber
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.domain import Domain
from app.models.question import Question
from app.models.pdf_upload import PdfUpload

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# ---------------------------------------------------------------------------
# Keyword-based domain mapping — derived from session HTML syllabi (S01-S09).
# Must stay in sync with app/seed/aws_questions.py DOMAIN_KEYWORDS.
# ---------------------------------------------------------------------------
DOMAIN_KEYWORDS = {
    # S01 + S02 — Cloud Concepts & Global Infrastructure
    "AWS Global Infrastructure & Cloud Economics": [
        "cloud computing", "nist", "iaas", "paas", "saas",
        "public cloud", "private cloud", "hybrid cloud", "multi-cloud",
        "deployment model", "service model",
        "six advantages", "6 advantages", "cloud advantages",
        "aws management console",
        "region", "availability zone", "edge location",
        "global infrastructure", "aws region",
        "high availability", "fault tolerance", "disaster recovery",
        "capex", "opex", "capital expenditure", "operational expenditure",
        "total cost of ownership", "tco",
        "cloud economics", "cloud adoption",
        "well-architected", "six pillars", "6 pillars",
        "cloud adoption framework", "caf",
        "agility", "elasticity", "scalability",
        "aws pricing model",
    ],
    # S03 — IAM & Identity Fundamentals
    "IAM — Identity, Access & Security Fundamentals": [
        "iam", "identity and access",
        "iam user", "iam group", "iam role", "iam policy",
        "managed policy", "inline policy",
        "least privilege", "deny by default",
        "mfa", "multi-factor authentication",
        "root account", "root user",
        "access key", "secret key", "password policy",
        "shared responsibility",
        "aws organizations", "organizational unit", "scp",
        "service control polic",
        "iam identity center", "sso", "single sign-on",
        "federation", "cognito", "directory service",
        "instance profile", "cross-account",
        "cloudtrail",
    ],
    # S04 — Core Compute
    "Core Compute — EC2, Lambda & Containers": [
        "ec2", "elastic compute",
        "instance type", "instance family",
        "t2", "t3", "m5", "c5", "r5",
        "spot instance", "reserved instance", "on-demand",
        "dedicated host", "dedicated instance",
        "placement group",
        "ebs volume", "instance store", "ebs snapshot",
        "user data", "ami", "amazon machine image",
        "launch template",
        "auto scaling", "scaling policy", "scaling group",
        "elastic load balancing", "elb", "alb", "nlb", "glb",
        "application load balancer", "network load balancer",
        "lambda", "serverless",
        "container", "docker",
        "ecs", "eks", "fargate",
        "elastic beanstalk", "lightsail",
        "batch", "outposts",
    ],
    # S05 — Storage Services
    "Storage Services — S3, EBS, EFS & Glacier": [
        "s3 ", "s3,", "s3.", "amazon s3", "simple storage service",
        "s3 bucket", "bucket policy", "bucket",
        "storage class", "intelligent-tiering", "standard-ia", "one zone-ia",
        "glacier", "glacier instant", "deep archive",
        "lifecycle policy", "lifecycle rule",
        "s3 versioning", "versioning",
        "s3 replication", "cross-region replication", "crr", "srr",
        "transfer acceleration",
        "block public access",
        "ebs", "elastic block store", "gp2", "gp3", "io1", "io2", "st1", "sc1",
        "ebs snapshot",
        "efs", "elastic file system",
        "fsx", "fsx for lustre", "fsx for windows",
        "snow family", "snowcone", "snowball", "snowmobile",
        "storage gateway",
        "object storage", "block storage", "file storage",
    ],
    # S06 — Databases & Analytics
    "Databases & Analytics on AWS": [
        "rds", "relational database service",
        "multi-az", "read replica",
        "aurora", "aurora serverless",
        "dynamodb", "key-value", "nosql",
        "elasticache", "redis", "memcached",
        "redshift", "data warehouse", "olap",
        "athena", "serverless sql",
        "kinesis", "real-time streaming", "data streaming",
        "glue", "etl", "data catalog",
        "emr", "elastic mapreduce",
        "quicksight", "business intelligence",
        "neptune", "graph database",
        "documentdb", "document database",
        "keyspaces", "cassandra",
        "timestream", "time series",
        "qldb", "quantum ledger",
        "dms", "database migration",
        "data pipeline",
    ],
    # S07 — Networking
    "Networking — VPC, CloudFront & Route 53": [
        "vpc", "virtual private cloud",
        "subnet", "public subnet", "private subnet",
        "cidr", "ip address",
        "internet gateway", "igw",
        "nat gateway", "nat instance",
        "security group", "nacl", "network acl",
        "route table",
        "vpc peering",
        "transit gateway",
        "privatelink", "vpc endpoint",
        "cloudfront", "cdn", "content delivery",
        "route 53", "dns", "routing policy",
        "direct connect",
        "site-to-site vpn", "vpn",
        "global accelerator",
        "api gateway",
    ],
    # S08 — Security, Compliance & Governance (beyond IAM)
    "Security, Compliance & Governance": [
        "kms", "key management", "envelope encryption", "cmk",
        "customer managed key", "aws managed key",
        "certificate manager", "acm", "ssl", "tls",
        "secrets manager", "rotate credential",
        "guardduty", "threat detection",
        "security hub",
        "inspector", "vulnerability scan",
        "macie", "pii detection",
        "detective",
        "aws shield", "ddos",
        "waf", "web application firewall",
        "firewall manager",
        "aws config", "config rule",
        "compliance", "soc", "pci dss", "hipaa", "iso 27001", "gdpr",
        "aws artifact",
        "governance",
        "encryption at rest", "encryption in transit",
    ],
    # S09 — Billing, Pricing & Support
    "Billing, Pricing & AWS Support Plans": [
        "free tier",
        "pricing calculator",
        "cost explorer", "cost analysis",
        "aws budgets", "budget alert",
        "billing console", "billing dashboard",
        "consolidated billing", "volume discount",
        "savings plan", "compute savings plan",
        "cost allocation", "cost and usage report",
        "support plan",
        "basic support", "developer support",
        "business support", "enterprise support", "enterprise on-ramp",
        "trusted advisor",
        "technical account manager", "tam",
        "concierge", "aws marketplace",
        "aws iq", "aws professional services",
    ],
}


def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def parse_exam_pdf_text(text: str) -> list[dict]:
    """Parse structured exam PDF format directly (no LLM needed).

    Handles format:
        NEW QUESTION N
        - (Exam Topic 1)
        Question text...

        A. Choice A
        B. Choice B

        Answer: B

        Explanation:
        ...
    """
    questions = []

    # Split by NEW QUESTION markers
    blocks = re.split(r'NEW QUESTION\s+\d+', text)

    for block in blocks[1:]:  # Skip content before first question
        lines = block.strip().split('\n')
        if not lines:
            continue

        # Skip topic marker line(s)
        question_lines = []
        choices = []
        answer_str = ""
        explanation_lines = []
        in_explanation = False
        in_question = True

        for line in lines:
            stripped = line.strip()

            # Skip noise
            if not stripped:
                continue
            if stripped.startswith("- (Exam Topic"):
                continue
            if "Passing Certification Exams Made Easy" in stripped:
                continue
            if "visit - http" in stripped:
                continue
            if stripped.startswith("Recommend!!"):
                continue
            if stripped.startswith("Welcome to download"):
                continue
            if stripped.startswith("https://www."):
                if not in_explanation:
                    continue

            # Check for answer line
            answer_match = re.match(r'^Answer:\s*([A-K,\s]+)$', stripped)
            if answer_match:
                answer_str = answer_match.group(1).strip()
                in_question = False
                continue

            # Check for explanation
            if stripped == "Explanation:":
                in_explanation = True
                continue

            if in_explanation:
                explanation_lines.append(stripped)
                continue

            # Check for choice line (A. through K.)
            choice_match = re.match(r'^([A-K])\.\s+(.+)', stripped)
            if choice_match:
                in_question = False
                choices.append({
                    "letter": choice_match.group(1),
                    "text": choice_match.group(2).strip(),
                })
                continue

            # Must be question text
            if in_question:
                question_lines.append(stripped)

        question_text = ' '.join(question_lines).strip()
        if not question_text or len(choices) < 2 or not answer_str:
            continue

        # Parse correct answers
        correct_letters = set()
        for letter in re.findall(r'[A-K]', answer_str):
            correct_letters.add(letter)

        # Build choices with is_correct
        parsed_choices = []
        for c in choices:
            parsed_choices.append({
                "text": c["text"],
                "is_correct": c["letter"] in correct_letters,
            })

        # Determine question type
        if len(correct_letters) > 1:
            q_type = "multiple"
        else:
            q_type = "single"

        explanation = '\n'.join(explanation_lines).strip() if explanation_lines else None

        questions.append({
            "question_text": question_text,
            "question_type": q_type,
            "choices": parsed_choices,
            "explanation": explanation,
        })

    return questions


def categorize_by_keywords(question_text: str, choices_text: str, domains: dict[str, "Domain"]) -> "Domain | None":
    """Fast keyword-based domain categorization."""
    combined = (question_text + " " + choices_text).lower()
    scores = {}
    for domain_name, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in combined)
        if score > 0:
            scores[domain_name] = score
    if not scores:
        return None
    best = max(scores, key=scores.get)
    return domains.get(best)


async def categorize_batch_with_llm(
    questions: list[dict], domains: list[dict]
) -> list[str]:
    """Use LLM to categorize questions that keyword matching couldn't handle.
    Send a batch of question texts and get domain assignments back."""
    domain_list = "\n".join(f"- {d['name']}" for d in domains)
    q_list = "\n".join(
        f"{i+1}. {q['question_text'][:200]}"
        for i, q in enumerate(questions)
    )

    prompt = f"""Categorize each question into exactly one of these AWS domains:
{domain_list}

Questions:
{q_list}

Return a JSON array of domain names, one per question, in the same order.
Example: ["Domain A", "Domain B", ...]
Return ONLY the JSON array."""

    try:
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
                    "temperature": 0,
                },
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]

        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            content = content.rsplit("```", 1)[0]

        return json.loads(content)
    except Exception as e:
        print(f"  LLM categorization failed: {e}")
        return []


async def parse_pdf_with_llm(
    db: AsyncSession, pdf_upload: PdfUpload, domains: list[Domain]
) -> int:
    """Extract questions from PDF, categorize by domain, store in DB."""
    pdf_upload.status = "processing"
    await db.commit()

    try:
        # Step 1: Extract text
        text = extract_text_from_pdf(pdf_upload.file_path)
        if not text.strip():
            raise ValueError("No text extracted from PDF")

        # Step 2: Parse questions directly (no LLM needed for extraction)
        parsed = parse_exam_pdf_text(text)
        print(f"  Parsed {len(parsed)} questions from PDF text")

        if not parsed:
            raise ValueError("No questions found in PDF. The format may not be supported.")

        # Step 3: Categorize — try keywords first, LLM for the rest
        domain_map = {d.name: d for d in domains}
        categorized = []
        uncategorized = []

        for q in parsed:
            choices_text = " ".join(c["text"] for c in q["choices"])
            domain = categorize_by_keywords(q["question_text"], choices_text, domain_map)
            if domain:
                categorized.append((q, domain))
            else:
                uncategorized.append(q)

        print(f"  Keyword-categorized: {len(categorized)}, need LLM: {len(uncategorized)}")

        # LLM categorization for uncategorized questions (in batches of 50)
        if uncategorized:
            domain_info = [{"name": d.name} for d in domains]
            batch_size = 50
            for i in range(0, len(uncategorized), batch_size):
                batch = uncategorized[i:i + batch_size]
                results = await categorize_batch_with_llm(batch, domain_info)
                for j, q in enumerate(batch):
                    if j < len(results) and results[j] in domain_map:
                        categorized.append((q, domain_map[results[j]]))
                    else:
                        # Fallback to first domain
                        fallback = list(domain_map.values())[0]
                        categorized.append((q, fallback))

        # Step 4: Insert questions
        count = 0
        for q, domain in categorized:
            question = Question(
                domain_id=domain.id,
                source_pdf_id=pdf_upload.id,
                source="pdf",
                question_text=q["question_text"],
                question_type=q["question_type"],
                choices=q["choices"],
                explanation=q.get("explanation"),
            )
            db.add(question)
            count += 1

        pdf_upload.status = "done"
        pdf_upload.questions_extracted = count
        await db.commit()
        print(f"  Stored {count} questions")
        return count

    except Exception as e:
        pdf_upload.status = "error"
        pdf_upload.error_message = str(e)[:500]
        await db.commit()
        raise
