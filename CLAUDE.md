# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is QuizForge

Classroom quiz platform — generates unique, shuffled quizzes per student from uploaded PDFs and curated question banks. QR code sessions, auto-grading, anti-copy-paste, study cards.

## Commands

### Docker (recommended)

```bash
docker compose up -d db           # Start database only
docker compose up -d              # Start all services
docker compose exec backend python -m app.seed  # Seed DB (first time)
```

### Local development

```bash
# Backend (from /backend)
pip install -r requirements.txt
python -m app.seed                # Seed DB (first time)
uvicorn app.main:app --reload     # http://localhost:8000

# Frontend (from /frontend)
npm install
npm run dev                       # http://localhost:3000
npm run lint                      # ESLint
npm run build                     # Production build
```

### Database migrations (from /backend)

```bash
alembic upgrade head                              # Apply migrations
alembic revision --autogenerate -m "description"  # Generate migration
```

### Health check

```
GET /api/health
```

Default login: `instructor` / `quizforge-admin`

## Architecture

**Backend**: FastAPI + SQLAlchemy 2.0 async + PostgreSQL 16 (asyncpg). JWT auth via httpOnly cookies.

**Frontend**: Next.js (App Router) + React 19 + Tailwind CSS 4 + TypeScript. API calls proxied via `next.config.ts` rewrite (`/api/*` → backend).

**LLM**: OpenRouter API (Gemini Flash) for PDF question extraction and explanation generation.

### Backend structure (`/backend/app/`)

- `main.py` — FastAPI app, CORS, router mounting
- `database.py` — async engine + session factory
- `config.py` — pydantic-settings env config
- `models/` — SQLAlchemy models (users, subjects, domains, questions, sessions, student_quizzes, student_answers, pdf_uploads, domain_cheatsheets)
- `routers/` — API routes: auth, subjects, questions, sessions, quiz, study, pdfs, practice
- `services/` — Business logic: `quiz_engine.py` (proportional subset selection), `grading.py`, `pdf_parser.py`, `auth.py`
- `seed/` — DB seeding (instructor account, AWS domains/questions/cheatsheets)

### Frontend structure (`/frontend/src/`)

- `app/(student)/` — Quiz taking, results, study cards, leaderboard
- `app/(instructor)/` — Dashboard, session creation, question bank, uploads, session results
- `lib/auth.tsx` — AuthContext + useAuth hook
- `lib/api.ts` — Fetch wrapper with typed API methods
- `components/` — Shared components (AntiCopyPaste, Sidebar, etc.)

### Key patterns

- **JSONB columns** for choices, questions_order, domain_ids — not normalized tables
- **Quiz engine** uses largest-remainder method for proportional domain representation in random subsets
- **PDF parsing** is two-stage: keyword-based domain categorization (150+ keywords per domain) → LLM fallback for uncategorized questions
- **Async throughout** — async ORM sessions, async PDF parsing, async LLM calls via httpx
- **Role-based access** — `student` and `instructor` roles, enforced in route dependencies

## Environment variables

Required in `.env`: `OPENROUTER_API_KEY`, `DATABASE_URL` (postgresql+asyncpg://...), `JWT_SECRET`, `FRONTEND_URL`
