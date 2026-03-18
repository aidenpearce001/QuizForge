import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subject import Subject
from app.models.domain import Domain
from app.models.question import Question
from app.seed.parsers.ditectrev import parse_ditectrev_readme
from app.seed.parsers.kananinirav import parse_kananinirav_exam

# Keyword-based domain mapping — maps AWS service/concept keywords to domain names
DOMAIN_KEYWORDS = {
    "AWS Global Infrastructure & Cloud Economics": [
        "region", "availability zone", "edge location", "well-architected",
        "cloud economics", "capex", "opex", "capital expenditure", "operational expenditure",
        "total cost of ownership", "tco", "cloud adoption", "migration",
        "global infrastructure", "cloud benefits", "agility", "elasticity",
        "high availability", "fault tolerance", "disaster recovery", "scalability",
    ],
    "IAM — Identity, Access & Security Fundamentals": [
        "iam", "identity and access", "mfa", "multi-factor", "root account",
        "iam user", "iam group", "iam role", "iam policy", "least privilege",
        "access key", "secret key", "federation", "cognito", "sso",
        "single sign-on", "directory service", "organizations", "scp",
    ],
    "Core Compute — EC2, Lambda & Containers": [
        "ec2", "elastic compute", "lambda", "serverless", "container",
        "ecs", "eks", "fargate", "elastic beanstalk", "lightsail",
        "auto scaling", "launch template", "ami", "instance type",
        "spot instance", "reserved instance", "on-demand", "dedicated host",
        "placement group", "batch", "outposts",
    ],
    "Storage Services — S3, EBS, EFS & Glacier": [
        "s3", "simple storage", "ebs", "elastic block", "efs", "elastic file",
        "glacier", "storage gateway", "snowball", "snowmobile", "snowcone",
        "storage class", "lifecycle", "versioning", "bucket",
        "transfer acceleration", "fsx",
    ],
    "Databases & Analytics on AWS": [
        "rds", "relational database", "aurora", "dynamodb", "elasticache",
        "redshift", "athena", "emr", "kinesis", "glue", "neptune",
        "documentdb", "keyspaces", "timestream", "qldb", "database migration",
        "dms", "quicksight", "data pipeline",
    ],
    "Networking — VPC, CloudFront & Route 53": [
        "vpc", "virtual private cloud", "subnet", "security group", "nacl",
        "network acl", "nat gateway", "internet gateway", "cloudfront",
        "route 53", "direct connect", "vpn", "transit gateway",
        "elastic load balancing", "elb", "alb", "nlb", "api gateway",
        "privatelink", "global accelerator",
    ],
    "Security, Compliance & Governance": [
        "shared responsibility", "aws shield", "waf", "web application firewall",
        "kms", "key management", "cloudtrail", "aws config", "guardduty",
        "inspector", "macie", "artifact", "compliance", "governance",
        "encryption", "certificate manager", "acm", "secrets manager",
        "security hub", "detective", "firewall manager",
    ],
    "Billing, Pricing & AWS Support Plans": [
        "free tier", "pricing", "cost explorer", "budgets", "billing",
        "pricing calculator", "consolidated billing", "support plan",
        "basic support", "developer support", "business support", "enterprise support",
        "trusted advisor", "savings plan", "compute savings",
        "cost allocation", "tag", "cost and usage report",
    ],
}

def categorize_question(question_text: str, choices_text: str, domains: dict[str, Domain]) -> Domain | None:
    """Categorize question into a domain using keyword matching."""
    combined = (question_text + " " + choices_text).lower()
    scores = {}

    for domain_name, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in combined)
        if score > 0:
            scores[domain_name] = score

    if not scores:
        # Default to Cloud Economics (most general)
        return domains.get("AWS Global Infrastructure & Cloud Economics")

    best = max(scores, key=scores.get)
    return domains.get(best)

DITECTREV_URL = "https://raw.githubusercontent.com/Ditectrev/Amazon-Web-Services-AWS-Certified-Cloud-Practitioner-CLF-C02-Practice-Tests-Exams-Questions-Answers/main/README.md"

KANANINIRAV_BASE = "https://raw.githubusercontent.com/kananinirav/AWS-Certified-Cloud-Practitioner-Notes/master/practice-exam"
KANANINIRAV_FILES = [f"practice-exam-{i}.md" for i in range(1, 24)]

async def seed_aws_questions(
    db: AsyncSession, subject: Subject, domains: dict[str, Domain]
) -> int:
    # Check if already seeded
    result = await db.execute(
        select(Question).where(Question.source == "seed").limit(1)
    )
    if result.scalar_one_or_none():
        print("  Questions already seeded, skipping")
        return 0

    all_questions = []

    async with httpx.AsyncClient(timeout=60) as client:
        # Parse Ditectrev
        print("  Fetching Ditectrev README...")
        try:
            resp = await client.get(DITECTREV_URL)
            if resp.status_code == 200:
                parsed = parse_ditectrev_readme(resp.text)
                print(f"  Parsed {len(parsed)} questions from Ditectrev")
                all_questions.extend(parsed)
            else:
                print(f"  Ditectrev fetch failed with status {resp.status_code}")
        except Exception as e:
            print(f"  Ditectrev fetch error: {e}")

        # Parse Kananinirav practice exams
        for filename in KANANINIRAV_FILES:
            url = f"{KANANINIRAV_BASE}/{filename}"
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    parsed = parse_kananinirav_exam(resp.text)
                    all_questions.extend(parsed)
                    print(f"  Parsed {len(parsed)} from {filename}")
                else:
                    print(f"  {filename} fetch failed with status {resp.status_code}")
            except Exception as e:
                print(f"  {filename} fetch error: {e}")

    # Deduplicate by question_text (first 100 chars)
    seen = set()
    unique = []
    for q in all_questions:
        key = q["question_text"][:100].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(q)

    print(f"  {len(unique)} unique questions after dedup (from {len(all_questions)} total)")

    # Insert with domain categorization
    count = 0
    for q in unique:
        choices_text = " ".join(c["text"] for c in q["choices"])
        domain = categorize_question(q["question_text"], choices_text, domains)
        if not domain:
            continue

        question = Question(
            domain_id=domain.id,
            source="seed",
            question_text=q["question_text"],
            question_type=q["question_type"],
            choices=q["choices"],
            explanation=q.get("explanation"),
        )
        db.add(question)
        count += 1

    await db.commit()
    return count
