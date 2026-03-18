# QuizForge

Classroom quiz platform that generates unique, shuffled quizzes per student from uploaded PDFs and curated question banks.

## Features

- **PDF Question Extraction** — Upload PDFs, LLM (via OpenRouter) extracts and categorizes questions by domain
- **Unique Quizzes Per Student** — Proportional random subset from question pool + shuffled order and answer choices
- **QR Code Sessions** — Instructor creates a session, students scan QR to join and take the quiz
- **Auto-Grading** — Instant results with score, domain breakdown, and per-question review
- **Anti-Copy-Paste** — Prevents casual GPT copy-pasting during quizzes
- **Study Cards** — Domain-based cheat sheets for students to review
- **Multi-Subject Ready** — Supports any subject with configurable domains (not just AWS)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, SQLAlchemy (async), Alembic, PostgreSQL |
| Frontend | Next.js 14 (App Router), Tailwind CSS |
| LLM | OpenRouter API (Gemini Flash) |
| Auth | JWT (httpOnly cookies) |
| Infrastructure | Docker Compose |

## Quick Start

### Prerequisites

- Docker & Docker Compose
- An OpenRouter API key (for PDF parsing)

### Setup

```bash
# Clone
git clone git@github.com:aidenpearce001/QuizForge.git
cd QuizForge

# Create .env
cat > .env <<EOF
OPENROUTER_API_KEY=your-openrouter-key
DATABASE_URL=postgresql+asyncpg://quizforge:quizforge@localhost:5432/quizforge
JWT_SECRET=change-me-in-production
FRONTEND_URL=http://localhost:3000
EOF

# Start everything
docker compose up -d

# Seed the database (instructor account + AWS questions)
docker compose exec backend python -m app.seed
```

### Access

| | URL |
|-|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8100 |

**Instructor login:** `instructor` / `quizforge-admin`

### Local Development

```bash
# Start DB
docker compose up -d db

# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.seed          # First time only
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Architecture

```
quizforge/
├── backend/
│   ├── app/
│   │   ├── models/       # SQLAlchemy models (10 tables)
│   │   ├── routers/      # FastAPI endpoints
│   │   ├── services/     # Business logic (quiz engine, grading, PDF parser)
│   │   ├── schemas/      # Pydantic request/response models
│   │   └── seed/         # Database seeding (instructor, AWS questions, cheatsheets)
│   └── alembic/          # Database migrations
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── (student)/    # Quiz, results, study cards
│       │   └── (instructor)/ # Dashboard, sessions, question bank
│       ├── components/       # Shared UI components
│       └── lib/              # API client, auth context
└── docker-compose.yml
```

## Seeded Data

The seed script populates:
- **1 instructor account**
- **AWS Cloud Practitioner** subject with 8 domains
- **1,000+ questions** parsed from open-source GitHub repos
- **8 study cheat sheets** (one per domain)

## How It Works

1. **Instructor** creates a subject, configures domains, uploads PDFs (or uses seeded questions)
2. **Instructor** creates a session — selects domains for today, sets questions per student
3. **QR code** is generated — students scan to join
4. **Each student** gets a unique quiz: random subset from the pool, shuffled question order, shuffled answer choices
5. **Auto-graded** on submit with instant results and domain breakdown
