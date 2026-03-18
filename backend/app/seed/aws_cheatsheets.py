from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.domain import Domain
from app.models.domain_cheatsheet import DomainCheatsheet

CHEATSHEETS = {
    "AWS Global Infrastructure & Cloud Economics": """
## What is Cloud Computing?

🔑 **Cloud computing** = on-demand delivery of IT resources (compute, storage, networking, databases) over the internet with **pay-as-you-go pricing**.

- AWS (Amazon Web Services) is the leading cloud provider
- **Service** vs **Product**: a service is ongoing (pay while you use), a product is a one-time purchase
- Cloud eliminates the need to own and maintain physical data centers

### AWS Cloud Pricing Model

| Pricing Fundamental | What You Pay For |
|---|---|
| **Compute** | Pay for compute time (per second/hour) |
| **Storage** | Pay for data stored in AWS |
| **Network OUT** | Pay for data transferred OUT of AWS |
| **Network IN** | FREE — inbound data transfer costs nothing |

💡 **Three pricing strategies**: (1) Pay-as-you-go, (2) Save when you reserve, (3) Pay less per unit at scale

---

## AWS Global Infrastructure

### Regions
🔑 A **Region** is a geographical area with full AWS infrastructure (compute, storage, DB, AI, analytics, etc.)

- Regions are **interconnected** via high-speed private networking
- Each region has a **name** (e.g., "US East (N. Virginia)") and a **code** (e.g., `us-east-1`)
- Data does **NOT** leave a region unless you explicitly configure it to

**Choosing a Region — 4 factors:**
1. **Compliance** — data governance and legal requirements
2. **Latency** — proximity to end users
3. **Service availability** — not all services exist in all regions
4. **Pricing** — costs can vary by region

### Availability Zones (AZs)
🔑 Each region is divided into **3–6 AZs**, each with one or more isolated data centers.

- AZs have redundant power, networking, and connectivity
- AZs are connected with **high-speed, low-latency links**
- ⚠️ An AZ is **NOT** the same as a single data center — an AZ can have multiple DCs
- Deploying across multiple AZs = **high availability**

### Edge Locations (Points of Presence)
- Smaller infrastructure for **caching content** closer to users
- Used by **CloudFront** (CDN) and other edge services
- There are **far more** edge locations than regions

### AWS Service Resilience Levels

| Level | Description | Example |
|---|---|---|
| **Global** | Data replicated across regions, survives region failure | IAM, Route 53 |
| **Regional** | Data replicated across AZs in one region | S3, VPC |
| **AZ** | Runs in a single AZ, prone to AZ failure | EC2, RDS (single-AZ) |

---

## AWS Public vs. Private Services

🔑 This distinction is about **networking**, NOT access permissions.

- **AWS Public Zone**: AWS-managed network connected to the internet. Services like IAM, S3, Route 53 run here with public endpoints.
- **AWS Private Zone**: Customer-managed VPCs. Private services like EC2, RDS deploy here.
- **Public Internet**: The regular internet — separate from the AWS public zone.

⚠️ Public services still require **authentication and authorization** — "public" just means they have public network endpoints.

---

## Cloud Benefits (The 6 Advantages)

| Benefit | Description |
|---|---|
| **Agility** | Spin up resources in minutes, not weeks |
| **Elasticity** | Scale up/down automatically based on demand |
| **Cost Savings** | CapEx → OpEx: no upfront hardware investment |
| **Global Reach** | Deploy worldwide in minutes |
| **Economies of Scale** | AWS passes massive-scale savings to customers |
| **Stop Guessing Capacity** | Use autoscaling instead of over/under-provisioning |

---

## Well-Architected Framework — 6 Pillars

🔑 The pillars are **synergistic**, not trade-offs. Improving one often improves others.

1. **Operational Excellence** — run/monitor systems, IaC, small reversible changes
2. **Security** — strong identity, encrypt data, least privilege, traceability
3. **Reliability** — auto-recover, horizontal scaling, test recovery
4. **Performance Efficiency** — use right resources, go global, serverless
5. **Cost Optimization** — pay only for what you use, right-size, measure ROI
6. **Sustainability** — minimize environmental impact, maximize utilization

💡 Use the **AWS Well-Architected Tool** (free) to review your architecture against all 6 pillars.

---

## Cloud Adoption Framework (CAF)

🔑 AWS whitepaper/guide for **digital transformation** to AWS. The exam regularly asks 5–6 questions about CAF.

### 6 CAF Perspectives (3 Business + 3 Technical)

| Business Perspectives | Technical Perspectives |
|---|---|
| **Business** — align cloud investments with business outcomes | **Platform** — build scalable hybrid cloud |
| **People** — bridge between tech and business, culture/leadership | **Security** — confidentiality, integrity, availability |
| **Governance** — maximize benefits, minimize risk | **Operations** — deliver cloud services meeting business needs |

### 4 Transformation Domains
1. **Technology** — migrate and modernize legacy infra
2. **Process** — digitize/automate operations, leverage data/ML
3. **Organization** — agile methods, product-oriented teams
4. **Product** — new value propositions and revenue models

### 4 Transformation Phases
1. **Envision** — identify opportunities, demonstrate value
2. **Align** — identify capability gaps, create action plan
3. **Launch** — build and deliver pilot initiatives
4. **Scale** — expand pilots to desired scale

---

## Exam Tips

- 🔑 Know the **4 factors** for choosing a region (compliance, latency, services, pricing)
- 🔑 Minimum **3 AZs** per region; AZ ≠ data center
- 🔑 **Data stays in a region** unless you explicitly move it
- 🔑 **Inbound data is FREE**, outbound costs money
- 🔑 Memorize the **6 pillars** of the Well-Architected Framework
- 🔑 Memorize the **6 CAF perspectives** and which are business vs. technical
- ⚠️ "Public vs. private services" = networking only, NOT about permissions
- 💡 Edge locations > Regions in quantity — they are used for **content caching**
""",

    "IAM — Identity, Access & Security Fundamentals": """
## AWS Accounts — The Foundation

🔑 An **AWS account** = container for identities (users) and AWS resources.

- An AWS account is **NOT** a human user — it is a container
- Each account has a **root user** (the account owner identity)
- Accounts provide an **isolation boundary** — everything inside is isolated by default
- ⚠️ Never put all your business in a single account — use multiple accounts for isolation

### Account Root User
🔑 The root user has **full, unrestricted access** and **cannot be restricted**.

- Created automatically with the account (email + password)
- **NOT** an IAM identity — IAM has no power over it

**Root user exclusive privileges (memorize!):**
- Change account settings (name, email, root password, access keys)
- Close/delete the AWS account
- Change or cancel the AWS Support Plan
- Register as a seller in the Reserved Instance Marketplace

⚠️ **Best practice**: Only use root for initial setup and emergency tasks. Create an `iamadmin` IAM user for daily admin work. Always enable MFA on root.

---

## IAM — Identity and Access Management

🔑 IAM is a **free, global** service that manages identities within an AWS account.

Three main jobs:
1. **Manage identities** (IAM is an Identity Provider)
2. **Authenticate** identities (prove who you are)
3. **Authorize** identities based on policies (allow/deny access)

⚠️ IAM only controls **local identities** in that account — not external accounts.

### IAM Identities

| Identity | Credentials | Use Case |
|---|---|---|
| **Users** | Long-term (username + password, access keys) | Individual people or applications |
| **Groups** | None — containers for users | Attach policies to groups, not individual users |
| **Roles** | Short-term (temporary via STS) | AWS services, cross-account access, federation |

🔑 **Key Rules:**
- New IAM users have **zero permissions** by default
- IAM is **global** — not region-specific
- Groups **cannot log in** to an AWS account
- **Hard limit**: 5,000 IAM users per account

### IAM Policies
- **JSON documents** that define permissions (Allow/Deny)
- **Identity policies**: attached to users, groups, or roles
- **Resource policies**: attached to AWS resources (e.g., S3 bucket policy)
- 🔑 **Explicit Deny always wins** over any Allow

---

## MFA (Multi-Factor Authentication)

🔑 MFA = using **more than one factor** to prove identity.

| Factor Type | Example |
|---|---|
| **Knowledge** | Password, PIN |
| **Possession** | MFA device/app, bank card, hardware key |
| **Inherent** | Fingerprint, face scan |
| **Location** | IP address, GPS coordinates |

- Always enable MFA on **root account** and **privileged IAM users**
- AWS supports authenticator apps, passkeys, and hardware keys

---

## Accessing AWS

| Method | How | Authentication |
|---|---|---|
| **Management Console** | Web browser (UI) | Password + MFA |
| **AWS CLI** | Terminal commands | Access Keys |
| **AWS SDK** | Code libraries (Python, JS, etc.) | Access Keys |

- **Access Keys** = Access Key ID + Secret Access Key (for programmatic access)
- ⚠️ Never share or commit access keys to code repositories
- **AWS CloudShell** = browser-based terminal with CLI pre-installed

💡 Use **IAM Roles** for EC2 instances instead of storing access keys on them.

---

## IAM Security Best Practices

- Use **root only** for initial setup and account closure
- Enforce **strong password policies** and rotation
- Enable **MFA** on all accounts
- Follow **least privilege** — grant only needed permissions
- Never share IAM users or access keys
- Use **IAM Roles** for services (EC2, Lambda)

### IAM Audit Tools

| Tool | Level | Purpose |
|---|---|---|
| **IAM Credential Reports** | Account-level | CSV listing all users and credential status |
| **IAM Access Advisor** | User-level | Shows when services were last accessed |

---

## Advanced Identity Services

- **AWS STS** — issues temporary credentials when roles are assumed (`sts:AssumeRole`)
- **Amazon Cognito** — manage user databases for mobile/web apps (millions of users)
- **AWS Directory Service** — integrate Microsoft Active Directory in AWS
- **IAM Identity Center** (formerly AWS SSO) — one login for multiple AWS accounts and apps

💡 IAM Identity Center is used by **AWS Organizations** to manage identities across many accounts.

---

## Shared Responsibility Model for IAM

| AWS Responsibility | Customer Responsibility |
|---|---|
| Infrastructure (global network security) | Manage Users, Groups, Roles, Policies |
| Configuration and vulnerability analysis | Enable and enforce MFA |
| Compliance validation | Rotate access keys regularly |
| | Apply appropriate permissions (least privilege) |
| | Analyze access patterns and review permissions |

---

## Exam Tips

- 🔑 IAM is **global** and **free**
- 🔑 New users have **no permissions** by default
- 🔑 **Explicit Deny > Allow** — always
- 🔑 Root user **cannot be restricted** and should only be used for specific tasks
- 🔑 Use **Roles** for EC2/Lambda, not access keys
- 🔑 **STS** provides temporary credentials whenever a role is assumed
- 🔑 **Cognito** handles millions of app users (IAM limited to 5,000)
- ⚠️ IAM groups **cannot** log in — they are just policy containers
- 💡 **IAM Identity Center** = the new name for AWS SSO
""",

    "Core Compute — EC2, Lambda & Containers": """
## Amazon EC2 (Elastic Compute Cloud)

🔑 EC2 is AWS's **default compute service** — IaaS providing virtual servers (instances).

### Key Concepts
- **Instance** = Virtual Machine (VM) = Virtual Server
- Hosted on physical **EC2 hosts**, deployed in a **VPC subnet** (single AZ)
- You have **OS-level control** (Linux, Windows, macOS)
- EC2 is **private by default** and **AZ-resilient**

### Instance Configuration
- **Type**: General purpose, compute optimized, memory optimized, storage optimized, accelerated computing
- **Size**: CPU + RAM allocation
- **Storage**: Instance Store (ephemeral, super fast) or EBS (persistent, network-attached)
- **User Data**: Bootstrap script that runs once at launch
- **Instance Role**: IAM role granting permissions to the instance
- **Security Groups**: Instance-level firewalls

---

### EC2 Purchasing Options

| Option | Discount | Commitment | Best For |
|---|---|---|---|
| **On-Demand** | None (full price) | None | Short, uninterrupted workloads |
| **Reserved** | Up to 72% | 1 or 3 years | Steady-state, long-running workloads |
| **Spot** | Up to 90% | None (can be interrupted!) | Fault-tolerant, flexible workloads |
| **Savings Plans** | Up to 72% | 1 or 3 years ($/hour commitment) | Flexible compute usage |
| **Dedicated Instances** | Varies | Varies | Compliance / security requirements |
| **Dedicated Hosts** | Varies | Varies | Server-bound licensing (socket/core) |
| **Capacity Reservations** | None | None | Guaranteed capacity in an AZ |

⚠️ **Spot instances can be terminated at any time** — never use them for databases or web servers!

💡 **Savings Plans**: you commit to X $/hour for compute. Usage beyond the plan is billed at on-demand rates.

---

### EC2 Instance States

| State | Billing | Notes |
|---|---|---|
| **Running** | Compute + Storage + Network | Fully operational |
| **Stopped** | Storage only | Can be restarted |
| **Terminated** | Nothing | Permanently deleted, non-reversible |

---

### Connecting to EC2

- **SSH** (port 22) — for Linux instances; uses key pairs (private + public key)
- **RDP** (port 3389) — for Windows instances
- **EC2 Instance Connect** — SSH from browser (Amazon Linux 2 out of the box)
- **SSM Session Manager** — no SSH/port 22 needed, enhanced security and auditing

---

## Resilience & Scaling

### Key Concepts

| Term | Definition |
|---|---|
| **High Availability (HA)** | Minimize downtime, auto-recover fast (some brief outage OK) |
| **Fault Tolerance (FT)** | Zero downtime — continues operating despite failures |
| **Vertical Scaling** | Scale UP/DOWN — increase/decrease size of one server |
| **Horizontal Scaling** | Scale OUT/IN — add/remove identical servers |
| **Elasticity** | **Automated** scaling based on demand |
| **Right-sizing** | Match instance type and size to workload (never over/under-provision) |

### Elastic Load Balancing (ELB)
🔑 Distributes incoming traffic across multiple EC2 instances.

| Type | Layer | Use Case |
|---|---|---|
| **Application (ALB)** | Layer 7 | HTTP/HTTPS traffic |
| **Network (NLB)** | Layer 4 | TCP/UDP, ultra-high performance |
| **Gateway (GWLB)** | Layer 3 | Security appliances (GENEVE protocol) |
| ~~Classic (CLB)~~ | Legacy | Do NOT use — migrate away |

- Supports **health checks** — only routes to healthy instances
- Can be **multi-AZ** for high availability

### EC2 Auto Scaling Groups (ASGs)
🔑 **Horizontal auto-scaling** for EC2 instances.

- Configuration: `MIN` / `DESIRED` / `MAX` capacity
- **Replaces unhealthy instances** automatically
- Scaling policies: Manual, Dynamic (simple/step/target tracking/scheduled), Predictive
- Integrates with ELB — set ELB target group to your ASG

---

## AWS Lambda (Serverless Compute)

🔑 **Function-as-a-Service (FaaS)** — run code without provisioning servers.

- Write a **Lambda function** in Python, Node.js, Java, Go, etc.
- **Billed per invocation + compute time** (in milliseconds)
- Memory is directly configured; **vCPU scales indirectly** with memory
- Max execution time: **15 minutes**
- Auto-scales from 0 to thousands of concurrent executions
- First **1 million invocations/month are free** (Free Tier)

💡 Lambda is a cornerstone of **serverless and event-driven architectures** (with API Gateway, S3, EventBridge, DynamoDB).

---

## Containers on AWS

| Service | Description |
|---|---|
| **Amazon ECS** | AWS-managed Docker container orchestration |
| **Amazon EKS** | Managed Kubernetes (K8s) — cloud-agnostic |
| **AWS Fargate** | Serverless containers — no EC2 management |
| **Amazon ECR** | Docker image repository (like Docker Hub) |
| **AWS Batch** | Run batch jobs in Docker containers |

💡 **Fargate** = serverless containers. **ECS/EKS on EC2** = you manage the instances.

---

## Other Compute Services

- **Elastic Beanstalk** — PaaS: upload code, AWS handles infrastructure (EC2, ASG, ALB, RDS)
- **Amazon Lightsail** — simple, low-cost virtual servers for beginners (predictable pricing, limited scaling)
- **Amazon Machine Image (AMI)** — instance template/snapshot for launching pre-configured EC2 instances
- **EC2 Image Builder** — automate AMI creation, testing, and distribution

---

## Shared Responsibility for EC2

| AWS | Customer |
|---|---|
| Physical infrastructure and host isolation | OS patches and updates |
| Replacing faulty hardware | Software installed on instances |
| Compliance validation | Security Group configuration |
| | IAM Roles and user access management |

---

## Exam Tips

- 🔑 **On-Demand** = default, no commitment; **Reserved** = steady-state; **Spot** = cheapest but interruptible
- 🔑 **Lambda max runtime** = 15 minutes; billed per ms of compute
- 🔑 **Fargate** = serverless containers (no EC2 to manage)
- 🔑 **Elastic Beanstalk** = PaaS (just upload code)
- 🔑 **ASG** provides horizontal scaling + auto-replacement of unhealthy instances
- 🔑 **ALB** = Layer 7 (HTTP), **NLB** = Layer 4 (TCP/UDP)
- ⚠️ Spot instances are **unreliable** — never for critical workloads
- ⚠️ **Instance Store** = ephemeral (data lost on stop/terminate)
- 💡 Use **SSM Session Manager** instead of SSH for better security (no port 22)
""",

    "Storage Services — S3, EBS, EFS & Glacier": """
## Amazon S3 (Simple Storage Service)

🔑 S3 is AWS's **default storage service** — object storage with unlimited scalability.

### Key Concepts
- **Object storage** — stores objects (like files) in **buckets** (containers)
- Objects can be **0 bytes to 5 TB** each; unlimited total storage
- S3 is a **public service** (has public endpoints) but **buckets are private by default**
- S3 is **regionally resilient** — data replicated across AZs within a region

⚠️ S3 is **NOT** file storage (can't browse like a filesystem) and **NOT** block storage (can't mount as a drive).

### S3 Objects
- **Key** = object identifier (like a filename), e.g., `photos/cat.jpg`
- **Value** = the actual data/content
- **Version ID**, **metadata**, and **ACL** are additional components
- S3 has a **flat structure** — "folders" in the UI are actually key **prefixes**

### S3 Buckets
- Bucket names must be **globally unique** (across ALL AWS accounts and regions)
- Naming rules: 3–63 chars, lowercase, no underscores, can't look like IP addresses
- Soft limit: **10,000 buckets** per account
- Data stored in a **region** — never leaves unless you configure it to

---

### S3 Security

| Layer | Description |
|---|---|
| **IAM Policies** | User-based: allow/deny S3 operations for identities |
| **Bucket Policies** | Resource-based: control who can access the bucket (including cross-account/public) |
| **Block Public Access** | ON by default — overrides all other configs for public access |
| **ACLs** | Legacy, simple permissions at object/bucket level — avoid if possible |
| **Encryption (at rest)** | Server-side (SSE) or client-side encryption |
| **Encryption (in transit)** | HTTPS (HTTP + SSL/TLS) |

💡 **IAM Access Analyzer** helps determine if S3 buckets are shared outside your trust zone.

---

### S3 Storage Classes

| Class | Use Case | Retrieval |
|---|---|---|
| **Standard** | Frequently accessed data | Immediate |
| **Standard-IA** | Infrequent access, lower storage cost | Immediate (access fee) |
| **One Zone-IA** | Infrequent, non-critical (1 AZ only) | Immediate (access fee) |
| **Glacier Instant Retrieval** | Archive, immediate access | Milliseconds |
| **Glacier Flexible Retrieval** | Archive | Minutes to hours |
| **Glacier Deep Archive** | Long-term archive, cheapest | 12–48 hours |
| **Intelligent-Tiering** | Auto-moves objects based on usage | Automatic |

- **Lifecycle Policies**: auto-transition objects between classes on a **schedule** (not usage-based)
- **Intelligent-Tiering**: moves objects based on **actual access patterns**

---

### Other S3 Features
- **Versioning**: keeps all versions of an object; deleting creates a deletion marker
- **Replication**: SRR (same-region) or CRR (cross-region) — async, requires versioning
- **Static Website Hosting**: host HTML/CSS/JS files directly from S3
- **S3 Transfer Acceleration**: uses edge locations for faster uploads/downloads globally

---

## EBS (Elastic Block Store)

🔑 **Persistent block storage** for EC2 instances — like a virtual hard drive.

- Attached to **one EC2 instance** at a time, in the **same AZ**
- **Persists** independently of instance lifecycle (by default, non-boot volumes survive termination)
- **EBS Snapshots** = backups stored in S3; can restore cross-AZ and cross-region
- ⚠️ EBS is **network-attached** — some latency compared to Instance Store

### EC2 Instance Store
- **Local, hardware-attached** storage inside the EC2 host
- **Extremely fast** (highest IOPS/throughput)
- ⚠️ **Ephemeral** — data lost if instance is stopped or terminated
- Not all instance types support Instance Store

---

## EFS (Elastic File System)

🔑 **Shared file storage** accessible from multiple EC2 instances.

- Implements **NFS protocol** — Linux EC2 instances only
- Automatically grows and shrinks
- Works **across AZs** in a region
- **EFS-IA** (Infrequent Access) for cost optimization
- More expensive than EBS/S3

---

## Amazon FSx

| Variant | Protocol | Use Case |
|---|---|---|
| **FSx for Windows** | SMB | Windows file servers |
| **FSx for Lustre** | Lustre | High Performance Computing (HPC), ML, Big Data |

---

## Storage Comparison

| Service | Type | Scope | Shared? | Persistence |
|---|---|---|---|---|
| **S3** | Object | Regional | Yes (via URL/API) | Yes |
| **EBS** | Block | Single AZ | No (1 instance) | Yes |
| **Instance Store** | Block | Single host | No (1 instance) | No (ephemeral) |
| **EFS** | File (NFS) | Regional | Yes (multi-instance) | Yes |
| **FSx** | File (SMB/Lustre) | Regional | Yes (multi-instance) | Yes |

---

## Data Migration — Physical Devices

- **AWS Snow Family**: physical devices for large-scale offline data migration
  - **Snowcone** — smallest, 8–14 TB
  - **Snowball Edge** — petabyte-scale, compute capabilities
  - **Snowmobile** — exabyte-scale (literal truck)

---

## Shared Responsibility for S3 / Storage

| AWS | Customer |
|---|---|
| Infrastructure, durability, availability | Bucket policies and public access settings |
| Data replication across AZs | Data encryption (at rest and in transit) |
| Replace faulty hardware | Versioning, replication, lifecycle setup |
| Ensure separation between customers | Logging and monitoring access |

---

## Exam Tips

- 🔑 S3 = **objects** (files), EBS = **blocks** (disks), EFS = **shared files** (NFS)
- 🔑 S3 bucket names are **globally unique**; data stays in the **region**
- 🔑 **Glacier Deep Archive** = cheapest storage but slowest retrieval (12–48 hrs)
- 🔑 **Lifecycle Policies** = schedule-based; **Intelligent-Tiering** = usage-based
- 🔑 EBS is tied to **one AZ**; use **snapshots** for cross-AZ/cross-region backups
- 🔑 **Instance Store** = fastest but ephemeral
- ⚠️ S3 max object size = **5 TB** (hard limit)
- ⚠️ EFS is **Linux only** (NFS); use FSx for Windows
- 💡 **Block Public Access** is ON by default — overrides everything for public access
""",

    "Databases & Analytics on AWS": """
## Databases 101

🔑 Databases give **structure** to stored data, making it easily searchable and queryable.

### Relational (SQL) Databases
- **Rigid schemas**: defined rows (items) and columns (attributes)
- Use **SQL** (Structured Query Language) for queries
- Two optimization types:
  - **OLTP** (Online Transactional Processing) — row-based, optimized for transactions
  - **OLAP** (Online Analytical Processing) — column-based, optimized for analytics

### Non-Relational (NoSQL) Databases
- **Flexible schemas** — less rigid than SQL
- Cannot use pure SQL (some support SQL-like languages)
- **Scale better** than SQL DBs but have less consistency
- Types: Document DBs, Graph DBs, Key-Value DBs, Time-Series DBs

💡 **Use AWS-managed DB services** instead of running databases on EC2 — automated backups, patching, scaling, and monitoring with less admin overhead.

---

## AWS SQL Database Services

### Amazon RDS (Relational Database Service)
🔑 **Managed SQL database** — OLTP, row-based, free-tier eligible.

- Supports: **MySQL, PostgreSQL, MariaDB, Oracle, SQL Server**
- Deployed as RDS instances in your **VPC** (private service)
- **Read Replicas (RR)** — distribute read operations across multiple instances
- **Multi-AZ deployments** — automatic failover for high availability
- You do NOT manage the OS — AWS handles patching and backups

### Amazon Aurora
🔑 **AWS-proprietary SQL engine** — MySQL/PostgreSQL compatible, **5x faster**.

- Row-based, OLTP (not free-tier eligible)
- Auto-scales storage up to 128 TB
- **Serverless option** available for variable workloads

### Amazon Redshift
🔑 **Data Warehouse** — column-based, OLAP, optimized for **analytics**.

- Complex queries on massive datasets
- Deploys clusters in your VPC; serverless option available
- Best for questions like "How much revenue in Q2?"

### AWS DMS (Database Migration Service)
- Migrate databases **to/from AWS** — fast and secure
- Source DB can continue operating during migration
- Supports cross-engine migration (e.g., Oracle → PostgreSQL on RDS)
- ⚠️ **Mostly SQL-to-SQL**; DynamoDB is the only supported NoSQL target

---

## AWS NoSQL Database Services

### Amazon DynamoDB
🔑 **Key-value database** — serverless, single-digit millisecond latency.

- Scales massively, highly available
- **DAX (DynamoDB Accelerator)** = in-memory cache exclusively for DynamoDB
- Great for key-value lookups, gaming, IoT, mobile backends

### Amazon ElastiCache
- **In-memory cache** — managed Redis or Memcached
- Greatly improves **read performance** as a caching layer

### Other NoSQL Services

| Service | Type | Use Case |
|---|---|---|
| **DocumentDB** | JSON documents | Managed MongoDB engine |
| **Neptune** | Graph DB | Social networks, fraud detection, knowledge graphs |
| **Timestream** | Time-series | IoT telemetry, stock prices, vehicle data |
| **QLDB** | Ledger (immutable) | Financial transactions ⚠️ Discontinued July 2025 |
| **Managed Blockchain** | Decentralized blockchain | Multi-party transactions without central authority |

---

## Data Analytics & Engineering Services

| Service | What It Does |
|---|---|
| **Amazon Athena** | Query S3 data with SQL — serverless, pay per query |
| **Amazon EMR** | Managed Hadoop/Spark clusters for big data processing |
| **AWS Glue** | Serverless ETL (Extract, Transform, Load) + Data Catalog |
| **Amazon Kinesis** | Real-time data streaming (Data Streams, Video Streams, Firehose) |
| **Amazon QuickSight** | Business Intelligence — dashboards & reports (serverless, ML-powered) |
| **Amazon Redshift** | Data warehouse for complex analytics queries (OLAP) |

### Kinesis Family

| Product | Purpose |
|---|---|
| **Kinesis Data Streams** | Ingest real-time data messages |
| **Kinesis Video Streams** | Ingest video/video-like data |
| **Amazon Data Firehose** | Load streams into S3, Redshift, etc. (now independent from Kinesis) |
| **Apache Flink (managed)** | Analyze/enrich streams in real-time (formerly Kinesis Analytics) |

---

## Shared Responsibility for RDS

| AWS | Customer |
|---|---|
| Manage underlying EC2 (no SSH access) | Port, IP, Security Group rules |
| Automated DB and OS patching | In-database user creation and permissions |
| Audit underlying infrastructure | Enable/disable public access |
| | Encryption settings (at rest, SSL in transit) |

---

## Exam Tips

- 🔑 **RDS** = managed SQL (MySQL, PostgreSQL, etc.); **Aurora** = AWS-native, 5x faster
- 🔑 **DynamoDB** = serverless key-value, single-digit ms latency
- 🔑 **Redshift** = data warehouse (OLAP / analytics), NOT for transactions
- 🔑 **Athena** = query S3 with SQL, serverless, pay per query
- 🔑 **Read Replicas** = improve read performance; **Multi-AZ** = high availability (failover)
- 🔑 **DMS** = migrate databases to AWS (supports cross-engine)
- 🔑 **ElastiCache** = in-memory caching (Redis/Memcached); **DAX** = cache for DynamoDB only
- ⚠️ **Neptune** = graph DB (social networks); **Timestream** = time-series; don't mix them up
- 💡 **Glue** does ETL + Data Catalog; **Athena** does schema-on-read (ELT)
""",

    "Networking — VPC, CloudFront & Route 53": """
## Amazon VPC (Virtual Private Cloud)

🔑 A VPC is your **isolated private network** inside AWS — you control IP ranges, subnets, and routing.

### Key Concepts
- VPC is within **1 account** and **1 region** — regionally resilient
- **VPC CIDR** = range of IP addresses for the VPC (e.g., `10.0.0.0/16`)
- Custom VPCs are **100% private and isolated by default** — no external communication without configuration
- **Default VPC**: auto-created per region, CIDR always `172.31.0.0/16`, pre-configured with IGW

⚠️ The Default VPC assigns **public IPv4** addresses to resources by default — unlike Custom VPCs which are private by default.

---

### VPC Components

| Component | Purpose |
|---|---|
| **Subnet** | Partition of VPC tied to one AZ; can be public or private |
| **Route Table (RT)** | Configures routing within subnet and outbound |
| **Internet Gateway (IGW)** | Allows access to internet and AWS public services |
| **NAT Gateway** | Allows private subnet outbound internet access (no inbound) |
| **NAT Instance** | Same as NAT Gateway but customer-managed EC2 |

### IP Addresses in AWS

| Type | Behavior | Cost |
|---|---|---|
| **Private IPv4** | Static, auto-assigned in subnet | Free |
| **Public IPv4** | Dynamic — changes on stop/start | **$0.005/hour** |
| **Elastic IP (EIP)** | Static public IPv4 | **$0.005/hour** (even when unused!) |
| **IPv6** | All publicly routable | Free |

⚠️ **All public IPv4 costs money** ($0.005/hr) — including EIPs! Free tier: 750 hrs/month.

---

### VPC Security

| Feature | Level | Stateful? | Rules |
|---|---|---|---|
| **Security Groups (SGs)** | Instance/ENI | Yes (stateful) | Allow rules only |
| **NACLs** | Subnet | No (stateless) | Allow AND Deny rules |
| **AWS Network Firewall** | VPC | — | Full VPC protection |

🔑 **Security Groups**: default **deny inbound**, allow outbound. Stateful = return traffic auto-allowed.
🔑 **NACLs**: default **allow all** — must add deny rules explicitly. Stateless = must define both directions.

- **VPC Flow Logs**: capture network traffic metadata (not content) for monitoring

---

## Hybrid & Cross-VPC Networking

| Service | Description |
|---|---|
| **VPC Peering** | Private connection between 2 VPCs — ⚠️ non-transitive |
| **VPC Endpoints (VPCE)** | Private access to public AWS services from within VPC |
| **AWS PrivateLink** | Private connection to services in 3rd-party VPCs |
| **Site-to-Site VPN** | Encrypted connection over public internet to your VPC |
| **Client VPN** | OpenVPN from your computer into your VPC |
| **Direct Connect (DX)** | Physical private cable from your DC to AWS (takes ~1 month) |
| **Transit Gateway (TGW)** | Hub connecting many VPCs and on-prem networks — transitive and scalable |

💡 **VPC Peering** = point-to-point, non-transitive. **Transit Gateway** = hub-and-spoke, transitive.

---

## Amazon Route 53

🔑 **Global DNS service** — domain registration and traffic routing.

### Routing Policies

| Policy | Behavior |
|---|---|
| **Simple** | No health checks, always routes to same resource |
| **Failover** | Routes to secondary if primary fails health check |
| **Weighted** | Distributes traffic by weight (e.g., 70/20/10) |
| **Latency** | Routes to region with lowest latency for the user |

---

## Amazon CloudFront

🔑 **Global Content Delivery Network (CDN)** — caches content at edge locations.

- Improves **read performance** and reduces latency globally
- Caches content (HTML, images, videos) at **edge locations**
- Integrates with S3, ALB, EC2, and custom origins

### Related Global Services

| Service | What It Does |
|---|---|
| **S3 Transfer Acceleration** | S3 uploads/downloads use AWS global network via edge locations |
| **AWS Global Accelerator** | Routes traffic through AWS global network for better TCP/UDP performance (no caching) |

---

## Edge & Extended Infrastructure

| Service | Description |
|---|---|
| **AWS Outposts** | AWS racks in YOUR data center — hybrid cloud |
| **AWS Local Zones** | AWS infrastructure in a nearby city — lower latency |
| **AWS Wavelength** | AWS resources in 5G networks — ultra-low latency |

---

## Exam Tips

- 🔑 **VPC** = private isolated network; **Custom VPCs** are fully private by default
- 🔑 **Default VPC CIDR** = `172.31.0.0/16` (always!)
- 🔑 **Security Groups** = stateful, allow only; **NACLs** = stateless, allow AND deny
- 🔑 **NAT Gateway** = private → internet (outbound only); **IGW** = public internet access
- 🔑 **Direct Connect** = dedicated physical connection (fastest, but takes weeks to set up)
- 🔑 **Transit Gateway** = transitive hub for many VPCs; **VPC Peering** = non-transitive, point-to-point
- 🔑 **CloudFront** = CDN at edge locations; **Global Accelerator** = TCP/UDP optimization (no caching)
- ⚠️ All **public IPv4** addresses cost money — including unused Elastic IPs
- ⚠️ **VPC Peering** has no transitive routing — A↔B and B↔C does NOT mean A↔C
- 💡 **Route 53 Failover** routing = simple disaster recovery strategy
""",

    "Security, Compliance & Governance": """
## AWS Shared Responsibility Model

🔑 The #1 security concept for the exam. AWS and the customer **share** security responsibilities.

| AWS — Security **OF** the Cloud | Customer — Security **IN** the Cloud |
|---|---|
| Physical facilities, hardware, network | Data classification and encryption |
| Host operating system, virtualization | IAM: users, groups, roles, policies |
| Managed service infrastructure | OS patching on EC2 instances |
| Global network security | Firewall rules (SGs, NACLs) |
| Compliance validation | Application security |

🔑 **Rule of thumb**: If you can configure or touch it, it's YOUR responsibility.

### Shared Responsibility by Service Type

| Service Model | AWS Manages | Customer Manages |
|---|---|---|
| **IaaS (EC2)** | Hardware, host OS | Guest OS, patching, SGs, data |
| **Managed (RDS)** | Hardware, host OS, DB engine patching | DB users, encryption settings, SG rules |
| **Serverless (Lambda, S3)** | Almost everything | Code, data, IAM permissions |

---

## AWS Acceptable Use Policy
- No illegal, harmful, or offensive use
- No security violations (unauthorized access, port scanning without approval)
- No network abuse (DDoS, flooding)
- No email/message abuse (spam)

---

## Network Protection Services

| Service | What It Does |
|---|---|
| **AWS Shield Standard** | Free, automatic DDoS protection for all AWS accounts |
| **AWS Shield Advanced** | Paid, 24/7 premium DDoS protection + cost protection |
| **AWS WAF** | Layer 7 firewall — filter HTTP traffic, block SQL injection, XSS |
| **AWS Network Firewall** | Protect entire VPC against network attacks |
| **AWS Firewall Manager** | Centralize security rules across multiple accounts |

💡 **Shield Standard** is always on and free. **Shield Advanced** adds response team access and cost protection during attacks.

### Penetration Testing
- **Allowed** on: EC2, NAT Gateways, ELB, RDS, CloudFront, Aurora, API Gateway, Lambda, Lightsail, Elastic Beanstalk
- **Prohibited**: DNS zone walking, DoS/DDoS attacks (real or simulated)

---

## Encryption Services

| Service | Purpose |
|---|---|
| **AWS KMS** | Manage encryption keys for data at rest (used by many services behind the scenes) |
| **AWS CloudHSM** | Dedicated hardware security module — YOU control the keys entirely |
| **AWS Certificate Manager (ACM)** | Free SSL/TLS certificates for encrypting data in transit |
| **AWS Secrets Manager** | Store and auto-rotate application secrets (DB passwords, API keys) |

🔑 **KMS** = AWS manages hardware, you or AWS manage keys. **CloudHSM** = AWS provides hardware, you fully manage keys.

---

## Threat Detection & Vulnerability Services

| Service | What It Finds | Where It Looks |
|---|---|---|
| **Amazon GuardDuty** | Threats and anomalies (ML-powered) | CloudTrail, VPC Flow Logs, DNS |
| **Amazon Inspector** | Software vulnerabilities | EC2, ECR images, Lambda functions |
| **Amazon Macie** | Sensitive data (PII) | S3 buckets |
| **Amazon Detective** | Root cause of security issues | Aggregates findings from other services |
| **IAM Access Analyzer** | Resources shared outside trust zone | S3 buckets, IAM roles, KMS keys |

🔑 Memory aids:
- **GuardDuty** = intelligent THREAT detection
- **Inspector** = SOFTWARE vulnerability scanning
- **Macie** = SENSITIVE DATA (PII) in S3
- **Detective** = ROOT CAUSE analysis

---

## Audit & Compliance Services

| Service | What It Does |
|---|---|
| **AWS CloudTrail** | Logs ALL API calls — who did what, when (audit trail) |
| **AWS Config** | Tracks resource configuration changes over time + compliance rules |
| **AWS Artifact** | Access AWS compliance reports and agreements (SOC, PCI, ISO, HIPAA) |
| **AWS Security Hub** | Central security dashboard — aggregates findings across accounts |
| **AWS Audit Manager** | Automate evidence collection for audits |

🔑 **CloudTrail** = WHO did what (API audit). **Config** = WHAT changed (resource configuration tracking).

💡 Enable **CloudTrail in ALL regions** for complete API audit coverage.

---

## Account Governance

### AWS Organizations
🔑 **Manage multiple AWS accounts** centrally.

- **Master account** + **member accounts**
- **Consolidated Billing** — one bill, volume discounts shared
- **Organizational Units (OUs)** — group accounts logically
- **Service Control Policies (SCPs)** — restrict permissions across accounts
  - ⚠️ SCPs cannot restrict the **master account**
  - ⚠️ SCPs **CAN** restrict root users of member accounts

### Other Governance Services

| Service | Purpose |
|---|---|
| **AWS Control Tower** | Set up and govern a secure multi-account environment |
| **AWS Service Catalog** | Self-service portal for launching only authorized CloudFormation stacks |
| **AWS RAM** | Share resources across accounts (VPC subnets, Transit Gateways) |

---

## Monitoring & Operational Security

| Service | Role |
|---|---|
| **Amazon CloudWatch** | Metrics, logs, alarms — default monitoring service |
| **Amazon EventBridge** | React to events in AWS / trigger scheduled actions (replaced CW Events) |
| **AWS X-Ray** | Trace requests through distributed applications |
| **AWS Health Dashboard** | Monitor AWS service health and events affecting your infrastructure |

### CloudWatch Components
- **CW Metrics** — performance data (CPU, network I/O, etc.)
- **CW Logs** — collect logs from AWS services, apps, on-prem servers
- **CW Alarms** — trigger notifications (SNS) or actions based on metric thresholds
- Namespaces, Dimensions, and Datapoints organize the data

---

## Exam Tips

- 🔑 **Shared Responsibility**: if you can touch/configure it = YOUR responsibility
- 🔑 **CloudTrail** = API audit (who/what/when); **Config** = resource change tracking
- 🔑 **GuardDuty** = threat detection; **Inspector** = vulnerability scanning; **Macie** = PII in S3
- 🔑 **Shield Standard** = free DDoS protection; **WAF** = Layer 7 HTTP filtering
- 🔑 **KMS** = managed encryption keys; **CloudHSM** = you control the hardware keys
- 🔑 **SCPs** restrict member accounts (including their root users) but NOT the master account
- 🔑 **Artifact** = compliance reports (SOC, PCI, ISO)
- ⚠️ Don't confuse **CloudTrail** (API calls) with **Config** (resource configuration)
- ⚠️ Don't confuse **GuardDuty** (threats) with **Inspector** (vulnerabilities) with **Macie** (PII)
- 💡 **Security Hub** aggregates findings from GuardDuty, Inspector, Macie, Config into one dashboard
""",

    "Billing, Pricing & AWS Support Plans": """
## AWS Pricing Principles

🔑 Understand the 4 pricing models — they appear frequently on the exam.

| Model | Description |
|---|---|
| **Pay-as-you-go** | Pay for what you use, no upfront costs (default) |
| **Save when you reserve** | 1 or 3 year commitments for significant discounts |
| **Pay less per unit at scale** | Volume discounts (more usage = lower unit cost) |
| **Pay less as AWS grows** | AWS passes savings from scale to all customers |

🔑 **Inbound data transfer is FREE.** You only pay for **outbound** data transfer.

---

## AWS Free Tier

| Type | Description | Examples |
|---|---|---|
| **Always Free** | No time limit, ongoing free usage | Lambda: 1M requests/mo, DynamoDB: 25GB |
| **12 Months Free** | Free for 12 months after account creation | EC2 t2.micro: 750 hrs/mo, S3: 5GB, RDS: 750 hrs |
| **Free Trials** | Short-term trials for specific services | Varies by service |

💡 Free services: **IAM, VPC** (the service itself), **CloudFormation** (you pay for created resources), **Elastic Beanstalk** (you pay for infrastructure), **Auto Scaling Groups** (you pay for instances).

### Free vs. Paid AWS Accounts (since 2025)
- **Free accounts**: 6 months, up to $200 credits, limited services/features
- **Paid accounts**: full access to all services, no time limit on workloads
- ⚠️ Free account conditions are very strict — one per customer, credentials cannot be shared
- 💡 Recommendation: use a Paid account even when learning

---

## Savings Plans

| Plan | Scope | Flexibility |
|---|---|---|
| **EC2 Savings Plan** | Specific EC2 instance family + region | Can change size, AZ, OS, tenancy |
| **Compute Savings Plan** | EC2, Fargate, and Lambda | Can change everything including compute service |
| **ML Savings Plan** | SageMaker instances | SageMaker-specific |

🔑 You commit to spend **X $/hour** on compute for 1 or 3 years. Usage beyond the plan is billed at on-demand rates.

---

## Cost Tracking Tools

| Tool | Purpose |
|---|---|
| **Billing Dashboard** | High-level overview of costs, includes Free Tier Dashboard |
| **Cost Explorer** | Visualize costs over time, forecast up to 12 months ahead |
| **Cost and Usage Reports** | Most detailed billing data (CSV) — integrates with Athena, Redshift, QuickSight |
| **Cost Allocation Tags** | Tag resources to track costs and create detailed reports |
| **AWS Resource Groups** | Group resources by tags for easier querying |

---

## Cost Optimization Tools

| Tool | Purpose |
|---|---|
| **AWS Budgets** | Set spending thresholds and get SNS alerts (4 types: Usage, Cost, Reservation, Savings Plans) |
| **AWS Pricing Calculator** | Estimate costs before deploying (calculator.aws) |
| **CloudWatch Billing Alarms** | Simple alarm when ACTUAL cost exceeds threshold |
| **Cost Anomaly Detection** | ML-powered detection of unusual spending |
| **AWS Compute Optimizer** | ML-powered recommendations for right-sizing compute resources |
| **AWS Service Quotas** | Monitor and get alerts before hitting service limits |

💡 **Budgets** can alert on projected AND actual costs. **CW Billing Alarms** only alert on actual costs.

---

## AWS Trusted Advisor

🔑 **Best-practice checks** across 5 categories: Cost Optimization, Performance, Security, Fault Tolerance, Service Limits.

| Support Plan | Trusted Advisor Access |
|---|---|
| **Basic / Developer** | 7 core checks only |
| **Business / Enterprise** | ALL checks + API access |

---

## AWS Organizations & Consolidated Billing

- **One bill** for all accounts in the organization — single payment method
- **Volume discounts shared** across all member accounts
- **Pooled Reserved Instances** — cost-effective across accounts
- Master account pays for all member accounts

---

## AWS Support Plans

| Plan | Price | TAM | Key Response Times |
|---|---|---|---|
| **Basic** | Free | No | 24/7 customer service, 7 core Trusted Advisor checks |
| **Developer** | $29+/mo | No | Business hours email; General: <24h, System impaired: <12h |
| **Business** | $100+/mo | No | 24/7 phone/email/chat; Prod impaired: <4h, Prod down: <1h |
| **Enterprise On-Ramp** | $5,500+/mo | Pool of TAMs | Business-critical down: <30 min |
| **Enterprise** | $15,000+/mo | Dedicated TAM | Business-critical down: <15 min |

### Support Plan Features Breakdown

| Feature | Basic | Developer | Business | Ent. On-Ramp | Enterprise |
|---|---|---|---|---|---|
| Customer Service | 24/7 | 24/7 | 24/7 | 24/7 | 24/7 |
| Trusted Advisor | 7 core | 7 core | **All checks** | **All checks** | **All checks** |
| Phone/Chat Support | No | No | **24/7** | **24/7** | **24/7** |
| TAM | No | No | No | **Pool** | **Dedicated** |
| Concierge | No | No | No | **Yes** | **Yes** |
| Infrastructure Event Mgmt | No | No | Extra fee | **Included** | **Included** |
| Incident Detection & Response | No | No | No | No | Extra fee |

---

## Migration & DR Cost Considerations

### 7 Migration Strategies (7 Rs)
1. **Retire** — turn off what you don't need
2. **Retain** — keep as-is (don't migrate yet)
3. **Relocate** — move within/between cloud environments
4. **Rehost** — "lift and shift" (no optimization)
5. **Replatform** — "lift and reshape" (some cloud optimization)
6. **Repurchase** — "drop and shop" (switch to SaaS)
7. **Refactor** — rearchitect with cloud-native features (most expensive, most benefit)

### Disaster Recovery Strategies (cheapest → most expensive)
1. **Backup & Restore** — just keep backups
2. **Pilot Light** — core functions ready, minimal setup
3. **Warm Standby** — full app ready at minimum size
4. **Multi-Site / Hot Site** — full app at full size (active/active)

---

## AWS Ecosystem Resources

| Resource | Description |
|---|---|
| **AWS re:Post** | Community Q&A portal (like StackOverflow for AWS) |
| **AWS Knowledge Center** | FAQ section within re:Post |
| **AWS Marketplace** | Digital catalog of 3rd-party software (AMIs, CFN templates, SaaS) |
| **AWS Managed Services (AMS)** | AWS experts who manage your infrastructure 24/7 |
| **AWS Professional Services** | AWS global team of experts |
| **AWS Partner Network (APN)** | External companies partnered with AWS (consulting, technology, training) |
| **AWS IQ** | Freelance marketplace for AWS projects |

---

## IaC & Deployment Services

| Service | Purpose |
|---|---|
| **CloudFormation (CFN)** | IaC with YAML/JSON templates — create/update/delete infrastructure |
| **AWS CDK** | Define infrastructure in code (Python, TypeScript, Java, .NET) → compiles to CFN |
| **Elastic Beanstalk** | PaaS — deploy code, AWS manages infrastructure |
| **AWS Systems Manager (SSM)** | Manage systems at scale (patching, commands, secrets, SSH replacement) |

---

## Exam Tips

- 🔑 **Inbound data = FREE**; outbound data costs money
- 🔑 **Trusted Advisor**: Basic/Developer = 7 checks; Business/Enterprise = ALL checks
- 🔑 **Enterprise** = dedicated TAM, 15-min response; **Enterprise On-Ramp** = TAM pool, 30-min response
- 🔑 **Cost Explorer** = visualize and forecast costs; **Budgets** = set alerts; **Pricing Calculator** = estimate before deploying
- 🔑 **Consolidated Billing** = one bill + shared volume discounts across Organization accounts
- 🔑 **Savings Plans** = $/hour commitment; **Reserved Instances** = specific instance commitment
- ⚠️ Don't confuse **Business** (no TAM) with **Enterprise On-Ramp** (pool TAM) and **Enterprise** (dedicated TAM)
- ⚠️ Don't confuse **AWS Managed Services** (AMS team) with general "managed services" (like RDS, Aurora)
- 💡 **CW Billing Alarms** = actual costs only; **Budgets** = actual AND projected costs
- 💡 Type "AWS <service> pricing" in a search engine to quickly find pricing details
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
            existing.content = content.strip()
            print(f"  Updated cheatsheet: {domain_name}")
            continue

        cheatsheet = DomainCheatsheet(
            domain_id=domain.id,
            content=content.strip(),
        )
        db.add(cheatsheet)
        print(f"  Created cheatsheet: {domain_name}")

    await db.commit()
