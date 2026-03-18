import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.subject import Subject
from app.models.domain import Domain

AWS_DOMAINS = [
    {
        "name": "AWS Global Infrastructure & Cloud Economics",
        "description": "Regions, AZs, Edge Locations, cloud benefits, CapEx vs OpEx, Well-Architected Framework",
    },
    {
        "name": "IAM — Identity, Access & Security Fundamentals",
        "description": "IAM users, groups, roles, policies, MFA, root account, least privilege",
    },
    {
        "name": "Core Compute — EC2, Lambda & Containers",
        "description": "EC2 instance types, pricing models, Auto Scaling, Lambda, ECS, EKS, Fargate, Elastic Beanstalk",
    },
    {
        "name": "Storage Services — S3, EBS, EFS & Glacier",
        "description": "S3 storage classes, lifecycle policies, EBS volumes, EFS, Glacier, Storage Gateway, Snowball",
    },
    {
        "name": "Databases & Analytics on AWS",
        "description": "RDS, Aurora, DynamoDB, ElastiCache, Redshift, Athena, EMR, Kinesis",
    },
    {
        "name": "Networking — VPC, CloudFront & Route 53",
        "description": "VPC, subnets, security groups, NACLs, NAT Gateway, CloudFront, Route 53, Direct Connect, VPN",
    },
    {
        "name": "Security, Compliance & Governance",
        "description": "Shared Responsibility Model, AWS Shield, WAF, KMS, CloudTrail, Config, GuardDuty, Inspector, Artifact",
    },
    {
        "name": "Billing, Pricing & AWS Support Plans",
        "description": "Free Tier, pricing models, Cost Explorer, Budgets, TCO Calculator, consolidated billing, Support plans",
    },
]

async def seed_aws_subject_and_domains(
    db: AsyncSession, instructor_id: uuid.UUID
) -> tuple[Subject, dict[str, Domain]]:
    # Check if subject exists
    result = await db.execute(select(Subject).where(Subject.name == "AWS Cloud Practitioner"))
    subject = result.scalar_one_or_none()

    if not subject:
        subject = Subject(
            name="AWS Cloud Practitioner",
            description="AWS Certified Cloud Practitioner (CLF-C02) exam preparation",
            created_by=instructor_id,
        )
        db.add(subject)
        await db.commit()
        await db.refresh(subject)
        print(f"  Created subject: {subject.name}")

    domains = {}
    for d in AWS_DOMAINS:
        result = await db.execute(
            select(Domain).where(Domain.subject_id == subject.id, Domain.name == d["name"])
        )
        existing = result.scalar_one_or_none()
        if existing:
            domains[d["name"]] = existing
        else:
            domain = Domain(subject_id=subject.id, name=d["name"], description=d["description"])
            db.add(domain)
            await db.commit()
            await db.refresh(domain)
            domains[d["name"]] = domain
            print(f"  Created domain: {d['name']}")

    return subject, domains
