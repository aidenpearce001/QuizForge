# QuizForge — Design Specification

## Overview

QuizForge is a quiz platform for classroom use. Instructors upload PDFs containing questions, an LLM (via OpenRouter) extracts and categorizes questions by domain, and the system generates unique shuffled quizzes per student per session. Students scan a QR code to join, register/login, and take the quiz with instant auto-graded results.

Built for expansion beyond AWS — supports any subject with configurable domains.

## Architecture

Monorepo with two services + a database:

```
quizforge/
├── backend/     # FastAPI — API, auth, PDF parsing, quiz engine, grading
├── frontend/    # Next.js — student quiz UI, instructor dashboard
└── docker-compose.yml  # FastAPI + Next.js + PostgreSQL
```

- **FastAPI backend**: Handles all server-side logic. Communicates with OpenRouter for LLM-based question extraction. Serves REST API consumed by the frontend.
- **Next.js frontend**: Two interfaces — student-facing quiz pages and instructor dashboard. Uses App Router with route groups `(student)` and `(instructor)`.
- **PostgreSQL**: Single database for all data. Accessed via SQLAlchemy (async) with Alembic migrations.

## Data Model

### users
| Column | Type | Notes |
|--------|------|-------|
| id | uuid | PK |
| full_name | varchar | Required for attendance mapping |
| username | varchar | Unique |
| password_hash | varchar | bcrypt |
| role | enum | `student`, `instructor` |
| created_at | timestamp | |
| updated_at | timestamp | |

Only one instructor account exists, created via seed (`python -m app.seed`). The `/api/auth/register` endpoint only creates `student` accounts — there is no way for students to register as an instructor. This prevents students from accessing the dashboard and seeing answers.

### subjects
| Column | Type | Notes |
|--------|------|-------|
| id | uuid | PK |
| name | varchar | e.g., "AWS Cloud Practitioner" |
| description | text | |
| created_by | uuid | FK → users.id |
| created_at | timestamp | |

### domains
| Column | Type | Notes |
|--------|------|-------|
| id | uuid | PK |
| subject_id | uuid | FK → subjects.id |
| name | varchar | e.g., "EC2", "S3", "VPC" |
| description | text | Used in LLM prompt for categorization |
| updated_at | timestamp | |

Domains are instructor-managed configuration. The LLM receives the domain list in its prompt when parsing PDFs and categorizes each question accordingly.

**Seeded AWS domains:**
1. AWS Global Infrastructure & Cloud Economics
2. IAM — Identity, Access & Security Fundamentals
3. Core Compute — EC2, Lambda & Containers
4. Storage Services — S3, EBS, EFS & Glacier
5. Databases & Analytics on AWS
6. Networking — VPC, CloudFront & Route 53
7. Security, Compliance & Governance
8. Billing, Pricing & AWS Support Plans

### domain_cheatsheets
| Column | Type | Notes |
|--------|------|-------|
| id | uuid | PK |
| domain_id | uuid | FK → domains.id |
| content | text | Markdown content — key concepts, tips, summaries |
| updated_at | timestamp | |

Study card / cheat sheet content per domain. Students can view these as flashcard-style reference cards to review what they've learned. Seeded with initial content for AWS domains.

### pdf_uploads
| Column | Type | Notes |
|--------|------|-------|
| id | uuid | PK |
| subject_id | uuid | FK → subjects.id |
| filename | varchar | Original filename |
| file_path | varchar | Server storage path |
| status | enum | `pending`, `processing`, `done`, `error` |
| questions_extracted | int | Count after processing |
| error_message | text | Nullable — error details if parsing failed |
| uploaded_by | uuid | FK → users.id |
| uploaded_at | timestamp | |

PDFs contain mixed questions across all domains. A single PDF may produce questions for EC2, S3, IAM, etc.

### questions
| Column | Type | Notes |
|--------|------|-------|
| id | uuid | PK |
| domain_id | uuid | FK → domains.id |
| source_pdf_id | uuid | FK → pdf_uploads.id, nullable (null for seeded questions) |
| source | enum | `pdf`, `seed`, `manual` — where the question came from |
| question_text | text | The question body |
| question_type | enum | `single`, `multiple`, `true_false` |
| choices | jsonb | `[{text: string, is_correct: boolean}]` |
| explanation | text | Shown after grading |
| created_at | timestamp | |
| updated_at | timestamp | |

Choices stored as JSONB on the question row — simpler than a separate table, and choices only make sense alongside their question.

### sessions
| Column | Type | Notes |
|--------|------|-------|
| id | uuid | PK |
| subject_id | uuid | FK → subjects.id |
| title | varchar | e.g., "Day 3 — EC2 & S3" |
| created_by | uuid | FK → users.id |
| domain_ids | jsonb | Selected domain IDs for this session |
| questions_per_quiz | int | How many questions each student gets |
| time_limit_minutes | int | Nullable — optional time limit |
| is_active | boolean | Instructor can toggle |
| created_at | timestamp | |
| updated_at | timestamp | |

QR codes are generated on the fly from the session URL (`/session/{id}`) — not stored in the database. The `domain_ids` column preserves which domains the instructor selected, so the session's intent is always visible.

### session_questions
| Column | Type | Notes |
|--------|------|-------|
| id | uuid | PK |
| session_id | uuid | FK → sessions.id |
| question_id | uuid | FK → questions.id |

Junction table. When instructor creates a session and selects domains, all questions from those domains are linked here. This is the pool from which student quizzes are drawn.

### student_quizzes
| Column | Type | Notes |
|--------|------|-------|
| id | uuid | PK |
| session_id | uuid | FK → sessions.id |
| student_id | uuid | FK → users.id |
| questions_order | jsonb | `[{question_id, choices_order: [int]}]` |
| started_at | timestamp | |
| submitted_at | timestamp | Nullable — null until submitted |
| score | float | Nullable — calculated on submit |
| total_correct | int | Nullable |
| total_questions | int | |

`questions_order` stores the student's unique shuffled quiz: which questions (random subset) and in what order, plus the shuffled choice indices for each question. This ensures page reloads preserve the exact quiz state.

### student_answers
| Column | Type | Notes |
|--------|------|-------|
| id | uuid | PK |
| student_quiz_id | uuid | FK → student_quizzes.id |
| question_id | uuid | FK → questions.id |
| selected_choices | jsonb | `[int]` — indices into the **original** `choices` array on the question |
| is_correct | boolean | |
| answered_at | timestamp | |

Answers saved as the student progresses (not just on final submit), so progress survives page refresh.

## API Design

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | `{full_name, username, password}` → JWT |
| POST | `/api/auth/login` | `{username, password}` → JWT |
| GET | `/api/auth/me` | Current user profile |

JWT stored in httpOnly cookies.

### Subjects & Domains (Instructor only)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/subjects` | Create subject |
| GET | `/api/subjects` | List subjects |
| POST | `/api/subjects/{id}/domains` | Add domain to subject |
| GET | `/api/subjects/{id}/domains` | List domains for subject |
| PUT | `/api/domains/{id}` | Update domain |
| DELETE | `/api/domains/{id}` | Delete domain |

### PDF Upload & Questions (Instructor only)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/subjects/{id}/pdfs` | Upload PDF(s), triggers async LLM parsing |
| GET | `/api/subjects/{id}/pdfs` | List uploads with processing status |
| GET | `/api/subjects/{id}/questions` | List questions, filterable by domain |
| GET | `/api/questions/{id}` | Question detail |
| PUT | `/api/questions/{id}` | Edit question (fix LLM errors) |
| DELETE | `/api/questions/{id}` | Delete bad question |

### Sessions (Instructor only)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/sessions` | `{subject_id, domain_ids[], questions_per_quiz, title, time_limit?}` |
| GET | `/api/sessions` | List sessions |
| GET | `/api/sessions/{id}` | Session detail + QR code |
| PUT | `/api/sessions/{id}/toggle` | Activate/deactivate session |
| GET | `/api/sessions/{id}/attendance` | Live attendance + progress |
| GET | `/api/sessions/{id}/results` | All student scores + stats |

### Student Quiz
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/sessions/{id}/join` | Join session → generates unique quiz → returns quiz_id |
| GET | `/api/quiz/{quiz_id}` | Quiz metadata (total questions, time remaining) |
| GET | `/api/quiz/{quiz_id}/question/{n}` | Get question N (shuffled choices, no correct answer exposed) |
| POST | `/api/quiz/{quiz_id}/question/{n}/answer` | Save answer for question N |
| POST | `/api/quiz/{quiz_id}/submit` | Submit quiz → returns score + full results |

## User Flows

### Instructor Flow
1. **Setup (one-time):** Create subject → configure domains
2. **Upload PDFs:** Upload one or more PDFs → system extracts text, sends to OpenRouter with domain list → LLM categorizes questions → stored in DB
3. **Create session:** Pick subject → select domains for today → set questions per student and optional time limit → QR code generated
4. **During class:** Display QR code → monitor live attendance and progress
5. **After class:** View results — per-student scores, per-question stats, domain breakdown

### Student Flow
1. **Scan QR code** → lands on session page with session info
2. **First time:** Register with full name, username, password → auto-logged in
3. **Returning:** Login with username/password
4. **Quiz starts:** System generates unique shuffled quiz from session question pool
5. **Take quiz:** One question per page, anti-copy-paste active, navigate forward/back
6. **Submit:** Instant results — score, correct/incorrect per question with explanations, domain breakdown

### PDF Parsing Flow
1. Instructor uploads PDF(s) to a subject
2. Backend extracts text using pdfplumber
3. Extracted text sent to OpenRouter LLM with prompt including the subject's configured domain list
4. LLM returns structured JSON: array of questions with `{question_text, question_type, choices[], correct_answers[], domain, explanation}`
5. Questions stored in DB linked to their domain and source PDF
6. Status updated from `processing` → `done` (or `error`)

**Error handling:** If LLM parsing fails or returns malformed JSON, status is set to `error` with a `error_message` stored on the `pdf_uploads` row. Instructor can retry via a "Reprocess" button which resets status to `pending`. Partial results are discarded — it's all-or-nothing per PDF to keep the question bank clean. The LLM response is validated against a JSON schema before inserting questions.

### Quiz Generation Flow (on student join)
1. Fetch session's question pool (from `session_questions`), grouped by domain
2. Select a **proportional random subset**: if the session has 60% EC2 and 40% S3 questions in the pool, the student's quiz reflects that ratio (e.g., 12 EC2 + 8 S3 for a 20-question quiz). Rounding handled by distributing remainders to the largest-remainder domains.
3. Shuffle question order (across domains, not grouped)
4. For each question, generate a random permutation of choice indices
5. Store the full shuffle state in `student_quizzes.questions_order`
6. Return `quiz_id` to the student

**Rejoin behavior:** If a student who already has a quiz for this session calls `/join` again (e.g., rescanning QR), return the existing `quiz_id` instead of generating a new one.

### Choice Index Convention
All `selected_choices` in `student_answers` store indices into the **original** `choices` array on the question (not the shuffled order). The frontend maps the student's visual selection back to original indices using `choices_order` from `questions_order` before saving. This makes grading straightforward — compare `selected_choices` against `choices[i].is_correct` directly.

## Frontend Pages

### Student Pages (Next.js App Router — `(student)` route group)
- `/session/[id]` — QR landing page with session info + Login/Register toggle
- `/quiz/[id]` — Quiz question page (one question at a time, progress dots, timer, prev/next navigation)
- `/results/[id]` — Score display, domain breakdown, question review with explanations
- `/study` — Domain study cards grid
- `/study/[domain-id]` — Full cheat sheet for a domain

### Instructor Pages (`(instructor)` route group)
- `/dashboard` — Session list with status and completion counts
- `/subjects` — CRUD for subjects
- `/domains` — CRUD for domains per subject
- `/uploads` — PDF upload and processing status
- `/questions` — Question bank browser, filterable by subject/domain, editable
- `/sessions/new` — Create session form (title, subject, domain selection, questions per student, time limit)
- `/sessions/[id]` — Session detail with QR code display, live attendance grid
- `/results/[id]` — Results dashboard (avg score, completion count, avg time, hardest question, student table with scores and weak domains)

## Anti-Copy-Paste Measures

Applied on the student quiz page to deter casual GPT copy-pasting:
- Disable right-click context menu (`oncontextmenu`)
- Disable text selection via CSS (`user-select: none`)
- Block keyboard shortcuts: Ctrl+C, Ctrl+A, Ctrl+V, Ctrl+X
- Disable drag events
- These are deterrents, not bulletproof — sufficient for the classroom use case

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, SQLAlchemy (async), Alembic, PyJWT, bcrypt |
| PDF parsing | pdfplumber |
| LLM integration | httpx → OpenRouter API |
| QR generation | `qrcode` Python library (server-side) |
| Frontend | Next.js 14 (App Router), Tailwind CSS |
| Auth | JWT in httpOnly cookies |
| Database | PostgreSQL via asyncpg |
| Dev environment | Docker Compose (FastAPI + Next.js + PostgreSQL) |

## Project Structure

```
quizforge/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── subject.py
│   │   │   ├── domain.py
│   │   │   ├── question.py
│   │   │   ├── pdf_upload.py
│   │   │   ├── session.py
│   │   │   ├── student_quiz.py
│   │   │   ├── student_answer.py
│   │   │   └── domain_cheatsheet.py
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── subjects.py
│   │   │   ├── domains.py
│   │   │   ├── pdfs.py
│   │   │   ├── questions.py
│   │   │   ├── sessions.py
│   │   │   ├── quiz.py
│   │   │   └── study.py
│   │   ├── services/
│   │   │   ├── pdf_parser.py
│   │   │   ├── quiz_engine.py
│   │   │   └── grading.py
│   │   ├── seed/
│   │   │   ├── __main__.py       # Entry point: python -m app.seed
│   │   │   ├── instructor.py     # Seed instructor account
│   │   │   ├── aws_domains.py    # Seed AWS subject + 8 domains
│   │   │   ├── aws_questions.py  # Parse GitHub sources into questions
│   │   │   └── aws_cheatsheets.py # Seed study card content
│   │   └── schemas/
│   ├── alembic/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/app/
│   │   ├── (student)/
│   │   │   ├── session/[id]/
│   │   │   ├── quiz/[id]/
│   │   │   └── results/[id]/
│   │   └── (instructor)/
│   │       ├── dashboard/
│   │       ├── subjects/
│   │       ├── domains/
│   │       ├── uploads/
│   │       ├── questions/
│   │       ├── sessions/
│   │       └── results/
│   ├── src/components/
│   ├── src/lib/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Seed Data

The seed script (`python -m app.seed`) creates:

1. **Instructor account** — single admin user (hardcoded credentials in seed)
2. **AWS Cloud Practitioner subject** with 8 domains listed above
3. **Base questions** scraped/parsed from GitHub sources:
   - https://github.com/Ditectrev/Amazon-Web-Services-AWS-Certified-Cloud-Practitioner-CLF-C02-Practice-Tests-Exams-Questions-Answers — markdown-based Q&A with answers
   - https://github.com/kananinirav/AWS-Certified-Cloud-Practitioner-Notes/blob/master/practice-exam/ — all practice exam files
4. **Domain cheat sheets** — study card content for each of the 8 AWS domains

The GitHub sources have different formats (markdown with Q&A). The seed script parses these formats directly (no LLM needed — the answers are already marked). Questions are categorized into domains using keyword matching or LLM-assisted categorization during seed.

## Study Cards (Cheat Sheets)

Students can access domain-based study cards — concise reference material for each domain. These are viewable before, during (optional), or after quizzes.

### Student Pages (addition)
- `/study` — Grid of domain cards for the current subject
- `/study/[domain-id]` — Full cheat sheet for a domain, rendered from markdown

### Instructor Pages (addition)
- Cheat sheet content is editable from the domain management page

## Scope & Constraints

- **Target class size:** Under 30 students — no need for websockets or heavy concurrency optimization. Simple REST polling is sufficient for live attendance.
- **Question types:** Flexible — whatever the LLM extracts from PDFs (single choice, multiple select, true/false). The `question_type` enum and JSONB `choices` handle all variants.
- **Multi-subject ready:** Subject → Domain hierarchy supports any subject, not just AWS.
- **No real-time sync needed:** Students work at their own pace. Instructor polls attendance endpoint for updates.

## Time Limit Enforcement

- The frontend displays a countdown timer based on `started_at + time_limit_minutes`.
- On submit, the backend validates `submitted_at - started_at <= time_limit_minutes + 30s grace period`. If exceeded, the quiz is still accepted but flagged as late.
- The frontend auto-submits when the timer hits zero (submitting whatever answers have been saved so far).
- Server-side is the authority — client timer is for UX only.

## Deletion Behavior

- **Deleting a domain** that has questions: blocked — return 409 with message "Domain has N questions. Delete or reassign questions first."
- **Deleting a question** that is in an active session's pool: blocked — return 409. Allowed if the question is only in closed sessions.
- **Deactivating a session**: soft operation — sets `is_active = false`. Students with in-progress quizzes can still submit. No new students can join.

## CORS & Infrastructure

- FastAPI backend configures CORS middleware allowing the frontend origin (configurable via env var `FRONTEND_URL`).
- List endpoints support `?page=1&limit=20` pagination. Default limit is 20, max 100.
- All list endpoints support `?sort=created_at&order=desc` for sorting.
