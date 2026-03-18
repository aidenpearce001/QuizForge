import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subject import Subject
from app.models.domain import Domain
from app.models.question import Question
from app.seed.parsers.ditectrev import parse_ditectrev_readme
from app.seed.parsers.kananinirav import parse_kananinirav_exam

# ---------------------------------------------------------------------------
# Keyword-based domain mapping — derived from session HTML syllabi (S01-S09).
# Each list contains ONLY the services/concepts explicitly covered in that
# session so that questions land in the correct domain.
# ---------------------------------------------------------------------------
DOMAIN_KEYWORDS = {
    # S01 + S02 — Cloud Concepts & Global Infrastructure
    "AWS Global Infrastructure & Cloud Economics": [
        # S01 – Intro to Cloud
        "cloud computing", "nist", "iaas", "paas", "saas",
        "public cloud", "private cloud", "hybrid cloud", "multi-cloud",
        "deployment model", "service model",
        "six advantages", "6 advantages", "cloud advantages",
        "aws management console",
        # S02 – Global Infrastructure & Economics
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
