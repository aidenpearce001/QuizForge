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

Docker ports: backend on `8100`, DB on `5434` (not the default 8000/5432).

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

No test suite exists in this project.

### Health check

```
GET /api/health
```

Default instructor login: `instructor` / `quizforge-admin`

## Architecture

**Backend**: FastAPI + SQLAlchemy 2.0 async + PostgreSQL 16 (asyncpg). JWT auth via httpOnly cookies.

**Frontend**: Next.js (App Router) + React 19 + Tailwind CSS 4 + TypeScript. API calls proxied via `next.config.ts` rewrite (`/api/*` → backend).

**LLM**: OpenRouter API (Gemini Flash) for PDF question extraction and explanation generation.

### Backend structure (`/backend/app/`)

- `main.py` — FastAPI app, CORS, router mounting
- `database.py` — async engine + session factory (`async_session` for background tasks, `get_db` for DI)
- `config.py` — pydantic-settings env config
- `models/` — SQLAlchemy models (users, subjects, domains, questions, sessions, student_quizzes, student_answers, pdf_uploads, domain_cheatsheets)
- `schemas/` — Pydantic request/response models, separate from ORM models
- `routers/` — API routes: auth, subjects, domains, questions, sessions, quiz, study, pdfs
- `services/` — Business logic: `quiz_engine.py` (proportional subset selection), `grading.py`, `pdf_parser.py`, `auth.py`
- `seed/` — DB seeding (instructor account, AWS domains/questions/cheatsheets); `generate_explanations.py` runs LLM batch explanations

### Frontend structure (`/frontend/src/`)

- `app/(student)/` — Quiz taking, results, study cards, leaderboard, practice, my-quizzes
- `app/(instructor)/` — Dashboard, session creation, question bank, uploads, session results
- `app/login/` — Instructor login (no self-registration)
- `app/student-login/` — Student login + self-registration
- `lib/auth.tsx` — AuthContext + useAuth hook
- `lib/api.ts` — Fetch wrapper with typed API methods
- `components/` — Shared components (AntiCopyPaste, Sidebar, StudentNav)

### Key patterns

**JSONB data shapes** — Know these before touching questions or quizzes:
- `Question.choices`: `[{"text": "...", "is_correct": bool}, ...]`
- `StudentQuiz.questions_order`: `[{"question_id": "uuid", "choices_order": [2,0,1,3]}, ...]` — `choices_order[i]` is the original index shown at display position `i`
- `Session.domain_ids`: list of UUID strings

**Quiz engine** — `services/quiz_engine.py` uses largest-remainder method for proportional domain representation in random subsets; choices are shuffled per-student at generation time, not display time.

**Practice quizzes** — There is no `is_practice` column. Practice quizzes are identified by their linked `Session.is_active == False` and `Session.title.startswith("Practice")`. The router creates a synthetic session on the fly and deletes it alongside the quiz on `DELETE /api/quiz/{id}`.

**PDF parsing** — Two-stage async background task: keyword-based domain categorization (150+ keywords/domain) → LLM fallback. `PdfUpload.status` cycles `pending → done/error`. The background task uses `async_session` directly (not DI), since it runs outside the request lifecycle.

**Auth** — `get_current_user` reads the `token` httpOnly cookie. `require_instructor` wraps it with role check. Self-registration (`POST /api/auth/register`) always creates `role="student"` — instructors must be seeded.

**Session QR flow** — `GET /api/sessions/{id}` returns a base64 PNG QR code linking to `{FRONTEND_URL}/session/{id}`. Students scan it and are redirected to join.

**Async throughout** — async ORM sessions, async PDF parsing, async LLM calls via httpx.

## Environment variables

Required in `.env`: `OPENROUTER_API_KEY`, `DATABASE_URL` (postgresql+asyncpg://...), `JWT_SECRET`, `FRONTEND_URL`
