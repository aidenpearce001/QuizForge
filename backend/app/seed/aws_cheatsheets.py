from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.domain import Domain
from app.models.domain_cheatsheet import DomainCheatsheet

CHEATSHEETS = {
    "AWS Global Infrastructure & Cloud Economics": """
## Key Concepts
- **Regions**: Geographic areas with 2+ Availability Zones (AZs)
- **AZs**: Isolated data centers within a region — use multiple for high availability
- **Edge Locations**: CDN endpoints for CloudFront — more locations than regions
- **Well-Architected Framework**: 6 pillars — Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, Sustainability

## Cloud Benefits
- **Agility**: Spin up resources in minutes, not weeks
- **Elasticity**: Scale up/down automatically based on demand
- **CapEx → OpEx**: No upfront hardware investment, pay-as-you-go
- **Global reach**: Deploy globally in minutes
- **Economies of scale**: AWS passes savings from massive scale to customers

## Remember
- Minimum 3 AZs per region (most have 3)
- Data does NOT leave a region unless you explicitly move it
- Choose region based on: compliance, latency, service availability, pricing
""",
    "IAM — Identity, Access & Security Fundamentals": """
## Core Components
- **Users**: Individual people/services — have credentials
- **Groups**: Collection of users — attach policies to groups, not individual users
- **Roles**: Temporary credentials for AWS services or cross-account access
- **Policies**: JSON documents that define permissions (Allow/Deny)

## Key Rules
- **Root account**: Has full access — use only for initial setup, enable MFA immediately
- **Least Privilege**: Grant only the permissions needed, nothing more
- **MFA**: Always enable on root and privileged accounts
- **Access Keys**: For programmatic access (CLI/SDK) — never share or commit to code

## Remember
- IAM is **global** — not region-specific
- New users have **zero permissions** by default
- **Explicit Deny** always wins over Allow
- Use **IAM Roles** for EC2 instances (not access keys)
- **AWS Organizations** + **SCPs** to manage multiple accounts
""",
    "Core Compute — EC2, Lambda & Containers": """
## EC2 Instance Types
- **On-Demand**: Pay per hour/second — no commitment
- **Reserved (1 or 3 year)**: Up to 72% discount — know your steady-state usage
- **Spot**: Up to 90% discount — can be interrupted, use for fault-tolerant workloads
- **Dedicated Hosts**: Physical server for you — compliance/licensing requirements
- **Savings Plans**: Flexible pricing for consistent usage across instance families

## Lambda (Serverless)
- Run code without provisioning servers
- Pay per invocation + compute time (ms)
- Max 15-minute execution time
- Auto-scales from 0 to thousands of concurrent executions

## Containers
- **ECS**: AWS-managed container orchestration
- **EKS**: Managed Kubernetes
- **Fargate**: Serverless containers — no EC2 to manage

## Remember
- Auto Scaling: automatically adjust EC2 count based on demand
- ELB (Elastic Load Balancing): distributes traffic across instances
- AMI: template for launching EC2 instances
- Elastic Beanstalk: PaaS — just upload code, AWS handles the rest
""",
    "Storage Services — S3, EBS, EFS & Glacier": """
## S3 (Simple Storage Service)
- **Object storage** — files up to 5TB, unlimited total
- **Storage Classes**: Standard → Standard-IA → One Zone-IA → Glacier Instant → Glacier Flexible → Glacier Deep Archive
- **Lifecycle Policies**: Auto-transition objects between classes
- **Versioning**: Keep all versions of an object
- **Bucket Policies**: Control access at bucket level

## EBS (Elastic Block Store)
- **Block storage** for EC2 — like a hard drive
- Attached to ONE EC2 instance at a time (same AZ)
- Persists independently of the EC2 instance lifecycle
- Snapshots for backup (stored in S3)

## EFS (Elastic File System)
- **File storage** — shared across multiple EC2 instances
- Automatically grows/shrinks
- Works across AZs in a region

## Remember
- S3 is for **objects** (files), EBS is for **blocks** (disks), EFS is for **shared files**
- S3 is **regional** but bucket names are **globally unique**
- Glacier: cheapest but retrieval takes minutes to hours
- Snowball/Snowcone: physical devices for large data migration
""",
    "Databases & Analytics on AWS": """
## Relational (SQL)
- **RDS**: Managed MySQL, PostgreSQL, MariaDB, Oracle, SQL Server
- **Aurora**: AWS-built, MySQL/PostgreSQL compatible, 5x faster, auto-scales storage

## NoSQL
- **DynamoDB**: Key-value + document, single-digit ms latency, serverless
- **ElastiCache**: In-memory (Redis/Memcached) — caching layer

## Analytics
- **Redshift**: Data warehouse — complex queries on huge datasets
- **Athena**: Query S3 data with SQL — serverless, pay per query
- **EMR**: Managed Hadoop/Spark for big data processing
- **Kinesis**: Real-time streaming data

## Remember
- RDS handles backups, patching, scaling — you DON'T manage the OS
- DynamoDB: serverless, auto-scales, great for key-value lookups
- Read Replicas: improve read performance (RDS/Aurora)
- Multi-AZ: automatic failover for high availability (RDS/Aurora)
- DMS (Database Migration Service): migrate databases to AWS
""",
    "Networking — VPC, CloudFront & Route 53": """
## VPC (Virtual Private Cloud)
- Your isolated network in AWS — you control IP ranges, subnets, routing
- **Public Subnet**: Has route to Internet Gateway — for web servers
- **Private Subnet**: No direct internet — for databases, app servers
- **NAT Gateway**: Lets private subnet access internet (outbound only)

## Security Layers
- **Security Groups**: Instance-level firewall — **stateful**, allow rules only
- **NACLs**: Subnet-level firewall — **stateless**, allow AND deny rules

## Content Delivery & DNS
- **CloudFront**: CDN — caches content at edge locations globally
- **Route 53**: DNS service — domain registration, routing policies

## Connectivity
- **VPN**: Encrypted connection over public internet to your VPC
- **Direct Connect**: Dedicated private connection from your data center to AWS
- **Transit Gateway**: Hub to connect multiple VPCs and on-premises networks

## Remember
- Default VPC exists in every region — has public subnets
- Security Groups: default DENY inbound, ALLOW outbound
- NACLs: default ALLOW all — must add deny rules explicitly
- VPC Peering: connect two VPCs (no transitive routing)
""",
    "Security, Compliance & Governance": """
## Shared Responsibility Model
- **AWS**: Security OF the cloud (hardware, network, facilities, managed services)
- **Customer**: Security IN the cloud (data, access, OS patching on EC2, firewall rules)
- Key: if you can configure/touch it, it's YOUR responsibility

## Protection Services
- **AWS Shield**: DDoS protection (Standard = free, Advanced = paid)
- **WAF**: Web Application Firewall — filter HTTP traffic, block SQL injection/XSS
- **GuardDuty**: Threat detection — analyzes CloudTrail, VPC Flow Logs, DNS
- **Inspector**: Automated security assessment of EC2 and containers
- **Macie**: Discover and protect sensitive data (PII) in S3

## Encryption & Key Management
- **KMS**: Create and manage encryption keys
- **CloudHSM**: Hardware security module — you control the keys
- **ACM**: Free SSL/TLS certificates for AWS services

## Audit & Compliance
- **CloudTrail**: Logs ALL API calls — who did what, when
- **AWS Config**: Track resource configuration changes over time
- **Artifact**: Access AWS compliance reports (SOC, PCI, ISO)

## Remember
- CloudTrail = WHO did what (API audit)
- Config = WHAT changed (resource tracking)
- GuardDuty = intelligent THREAT detection
- Enable CloudTrail in ALL regions
""",
    "Billing, Pricing & AWS Support Plans": """
## Pricing Principles
- **Pay-as-you-go**: No upfront costs for most services
- **Pay less when you reserve**: 1 or 3-year commitments for discounts
- **Pay less per unit at scale**: Volume discounts (S3, data transfer)
- **Inbound data**: FREE — outbound data costs money

## Cost Tools
- **Cost Explorer**: Visualize and forecast spending
- **Budgets**: Set alerts when spending exceeds thresholds
- **Pricing Calculator**: Estimate costs before deploying
- **Cost & Usage Report**: Most detailed billing data (CSV)
- **Consolidated Billing**: One bill for multiple accounts — volume discounts shared

## Free Tier
- **Always Free**: Lambda 1M requests/month, DynamoDB 25GB, etc.
- **12 Months Free**: EC2 t2.micro 750hrs/month, S3 5GB, RDS 750hrs
- **Trials**: Short-term free trials for specific services

## Support Plans
| Plan | Price | TAM | Response Time |
|------|-------|-----|---------------|
| Basic | Free | No | — |
| Developer | $29+ | No | 12hr general, 12hr system impaired |
| Business | $100+ | No | 1hr production down |
| Enterprise On-Ramp | $5,500+ | Pool | 30min business-critical |
| Enterprise | $15,000+ | Dedicated | 15min business-critical |

## Remember
- **Trusted Advisor**: Best practice checks (cost, performance, security, fault tolerance)
  - Basic/Developer: 7 core checks
  - Business/Enterprise: ALL checks
- **AWS Organizations**: Centrally manage multiple accounts + consolidated billing
""",
}

async def seed_aws_cheatsheets(db: AsyncSession, domains: dict[str, "Domain"]):
    for domain_name, content in CHEATSHEETS.items():
        domain = domains.get(domain_name)
        if not domain:
            continue

        result = await db.execute(
            select(DomainCheatsheet).where(DomainCheatsheet.domain_id == domain.id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            print(f"  Cheatsheet for {domain_name} already exists, skipping")
            continue

        cheatsheet = DomainCheatsheet(
            domain_id=domain.id,
            content=content.strip(),
        )
        db.add(cheatsheet)
        print(f"  Created cheatsheet: {domain_name}")

    await db.commit()
