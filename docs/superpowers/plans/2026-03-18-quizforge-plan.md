# QuizForge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a classroom quiz platform where instructors upload PDFs, an LLM categorizes questions by domain, and students take unique shuffled quizzes via QR code.

**Architecture:** FastAPI backend + Next.js frontend + PostgreSQL. Monorepo with `backend/` and `frontend/` directories. Backend handles auth, PDF parsing, quiz generation, grading. Frontend has student quiz UI and instructor dashboard.

**Tech Stack:** FastAPI, SQLAlchemy (async), Alembic, PostgreSQL, Next.js 14 (App Router), Tailwind CSS, OpenRouter API, pdfplumber, PyJWT, bcrypt

**Spec:** `docs/superpowers/specs/2026-03-18-quizforge-design.md`

---

## Phase 1: Backend Foundation

### Task 1: Project Scaffolding & Docker Setup

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`
- Create: `backend/Dockerfile`
- Create: `docker-compose.yml`
- Create: `.env`

- [ ] **Step 1: Create backend requirements.txt**

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy[asyncio]==2.0.35
asyncpg==0.29.0
alembic==1.13.0
pyjwt==2.9.0
bcrypt==4.2.0
python-multipart==0.0.9
pdfplumber==0.11.0
httpx==0.27.0
qrcode[pil]==7.4.2
pydantic-settings==2.5.0
python-dotenv==1.0.1
```

- [ ] **Step 2: Create app/config.py**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://quizforge:quizforge@localhost:5432/quizforge"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24
    openrouter_api_key: str = ""
    frontend_url: str = "http://localhost:3000"

    class Config:
        env_file = ".env"

settings = Settings()
```

- [ ] **Step 3: Create app/database.py**

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with async_session() as session:
        yield session
```

- [ ] **Step 4: Create app/main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(title="QuizForge", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 5: Create docker-compose.yml**

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: quizforge
      POSTGRES_PASSWORD: quizforge
      POSTGRES_DB: quizforge
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      - db
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

volumes:
  pgdata:
```

- [ ] **Step 6: Create backend/Dockerfile**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 7: Create __init__.py files**

Create empty `__init__.py` in: `backend/app/`, `backend/app/models/`, `backend/app/routers/`, `backend/app/services/`, `backend/app/schemas/`, `backend/app/seed/`

- [ ] **Step 8: Start Docker and verify**

Run: `cd /home/aiden/Aiden/quizforge && docker compose up -d db`
Then: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload`
Verify: `curl http://localhost:8000/api/health` returns `{"status":"ok"}`

- [ ] **Step 9: Commit**

```bash
git add -A
git commit -m "feat: scaffold backend with FastAPI, Docker, and PostgreSQL config"
```

---

### Task 2: Database Models

**Files:**
- Create: `backend/app/models/user.py`
- Create: `backend/app/models/subject.py`
- Create: `backend/app/models/domain.py`
- Create: `backend/app/models/question.py`
- Create: `backend/app/models/pdf_upload.py`
- Create: `backend/app/models/session.py`
- Create: `backend/app/models/student_quiz.py`
- Create: `backend/app/models/student_answer.py`
- Create: `backend/app/models/domain_cheatsheet.py`

- [ ] **Step 1: Create user model**

```python
# backend/app/models/user.py
import uuid
from datetime import datetime
from sqlalchemy import String, Enum as SAEnum, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(255))
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(SAEnum("student", "instructor", name="user_role"), default="student")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

- [ ] **Step 2: Create subject model**

```python
# backend/app/models/subject.py
import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    domains = relationship("Domain", back_populates="subject", lazy="selectin")
```

- [ ] **Step 3: Create domain model**

```python
# backend/app/models/domain.py
import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class Domain(Base):
    __tablename__ = "domains"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("subjects.id"))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    subject = relationship("Subject", back_populates="domains")
    cheatsheet = relationship("DomainCheatsheet", back_populates="domain", uselist=False, lazy="selectin")
```

- [ ] **Step 4: Create question model**

```python
# backend/app/models/question.py
import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, func, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class Question(Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    domain_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("domains.id"))
    source_pdf_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("pdf_uploads.id"), nullable=True)
    source: Mapped[str] = mapped_column(SAEnum("pdf", "seed", "manual", name="question_source"), default="pdf")
    question_text: Mapped[str] = mapped_column(Text)
    question_type: Mapped[str] = mapped_column(SAEnum("single", "multiple", "true_false", name="question_type"))
    choices: Mapped[dict] = mapped_column(JSONB)  # [{text: str, is_correct: bool}]
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    domain = relationship("Domain")
```

- [ ] **Step 5: Create pdf_upload model**

```python
# backend/app/models/pdf_upload.py
import uuid
from datetime import datetime
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, func, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

class PdfUpload(Base):
    __tablename__ = "pdf_uploads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("subjects.id"))
    filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(SAEnum("pending", "processing", "done", "error", name="pdf_status"), default="pending")
    questions_extracted: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 6: Create session model**

```python
# backend/app/models/session.py
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("subjects.id"))
    title: Mapped[str] = mapped_column(String(255))
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    domain_ids: Mapped[list] = mapped_column(JSONB)  # [uuid strings]
    questions_per_quiz: Mapped[int] = mapped_column(Integer)
    time_limit_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    subject = relationship("Subject", lazy="selectin")
    session_questions = relationship("SessionQuestion", back_populates="session", lazy="selectin")


class SessionQuestion(Base):
    __tablename__ = "session_questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id"))
    question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("questions.id"))

    session = relationship("Session", back_populates="session_questions")
    question = relationship("Question", lazy="selectin")
```

- [ ] **Step 7: Create student_quiz model**

```python
# backend/app/models/student_quiz.py
import uuid
from datetime import datetime
from sqlalchemy import Integer, Float, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class StudentQuiz(Base):
    __tablename__ = "student_quizzes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id"))
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    questions_order: Mapped[list] = mapped_column(JSONB)  # [{question_id, choices_order: [int]}]
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_correct: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_questions: Mapped[int] = mapped_column(Integer)

    student = relationship("User", lazy="selectin")
    answers = relationship("StudentAnswer", back_populates="student_quiz", lazy="selectin")
```

- [ ] **Step 8: Create student_answer model**

```python
# backend/app/models/student_answer.py
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class StudentAnswer(Base):
    __tablename__ = "student_answers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_quiz_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("student_quizzes.id"))
    question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("questions.id"))
    selected_choices: Mapped[list] = mapped_column(JSONB)  # [int] — indices into original choices array
    is_correct: Mapped[bool] = mapped_column(Boolean)
    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    student_quiz = relationship("StudentQuiz", back_populates="answers")
    question = relationship("Question", lazy="selectin")
```

- [ ] **Step 9: Create domain_cheatsheet model**

```python
# backend/app/models/domain_cheatsheet.py
import uuid
from datetime import datetime
from sqlalchemy import Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class DomainCheatsheet(Base):
    __tablename__ = "domain_cheatsheets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    domain_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("domains.id"), unique=True)
    content: Mapped[str] = mapped_column(Text)  # Markdown content
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    domain = relationship("Domain", back_populates="cheatsheet")
```

- [ ] **Step 10: Set up Alembic and create initial migration**

Run:
```bash
cd /home/aiden/Aiden/quizforge/backend
alembic init alembic
```

Edit `alembic/env.py` to import all models and use async engine:
```python
# Key changes in alembic/env.py:
from app.database import Base, engine
from app.models.user import User
from app.models.subject import Subject
from app.models.domain import Domain
from app.models.question import Question
from app.models.pdf_upload import PdfUpload
from app.models.session import Session, SessionQuestion
from app.models.student_quiz import StudentQuiz
from app.models.student_answer import StudentAnswer
from app.models.domain_cheatsheet import DomainCheatsheet

target_metadata = Base.metadata
```

Edit `alembic.ini` to set: `sqlalchemy.url = postgresql+asyncpg://quizforge:quizforge@localhost:5432/quizforge`

Run:
```bash
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

- [ ] **Step 11: Commit**

```bash
git add -A
git commit -m "feat: add all database models and initial migration"
```

---

### Task 3: Auth System (JWT + Registration/Login)

**Files:**
- Create: `backend/app/schemas/auth.py`
- Create: `backend/app/routers/auth.py`
- Create: `backend/app/services/auth.py`
- Modify: `backend/app/main.py` (register router)

- [ ] **Step 1: Create auth schemas**

```python
# backend/app/schemas/auth.py
from pydantic import BaseModel

class RegisterRequest(BaseModel):
    full_name: str
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class AuthResponse(BaseModel):
    token: str
    user: "UserResponse"

class UserResponse(BaseModel):
    id: str
    full_name: str
    username: str
    role: str

    class Config:
        from_attributes = True
```

- [ ] **Step 2: Create auth service**

```python
# backend/app/services/auth.py
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())

def create_token(user_id: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiry_hours),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])

async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()

async def create_student(db: AsyncSession, full_name: str, username: str, password: str) -> User:
    user = User(
        full_name=full_name,
        username=username,
        password_hash=hash_password(password),
        role="student",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
```

- [ ] **Step 3: Create auth dependency for protected routes**

Add to `backend/app/services/auth.py`:

```python
from fastapi import Depends, HTTPException, Request

async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    token = request.cookies.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    result = await db.execute(select(User).where(User.id == uuid.UUID(payload["sub"])))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

async def require_instructor(user: User = Depends(get_current_user)) -> User:
    if user.role != "instructor":
        raise HTTPException(status_code=403, detail="Instructor access required")
    return user
```

Note: import `get_db` from `app.database`.

- [ ] **Step 4: Create auth router**

```python
# backend/app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import RegisterRequest, LoginRequest, AuthResponse, UserResponse
from app.services.auth import (
    get_user_by_username, create_student, verify_password, create_token, get_current_user
)
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=AuthResponse)
async def register(body: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)):
    existing = await get_user_by_username(db, body.username)
    if existing:
        raise HTTPException(status_code=409, detail="Username already taken")
    user = await create_student(db, body.full_name, body.username, body.password)
    token = create_token(str(user.id), user.role)
    response.set_cookie("token", token, httponly=True, samesite="lax", max_age=86400)
    return AuthResponse(token=token, user=UserResponse.model_validate(user))

@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_username(db, body.username)
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(str(user.id), user.role)
    response.set_cookie("token", token, httponly=True, samesite="lax", max_age=86400)
    return AuthResponse(token=token, user=UserResponse.model_validate(user))

@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return UserResponse.model_validate(user)

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("token")
    return {"ok": True}
```

- [ ] **Step 5: Register auth router in main.py**

```python
# Add to app/main.py
from app.routers import auth
app.include_router(auth.router)
```

- [ ] **Step 6: Test auth endpoints manually**

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Test Student","username":"test","password":"test123"}' -v

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123"}' -v

# Me (use cookie from login)
curl http://localhost:8000/api/auth/me -b "token=<jwt-from-response>"
```

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat: add JWT auth with register, login, logout endpoints"
```

---

### Task 4: Seed Script (Instructor + AWS Subject + Domains + Questions + Cheatsheets)

**Files:**
- Create: `backend/app/seed/__init__.py`
- Create: `backend/app/seed/__main__.py`
- Create: `backend/app/seed/instructor.py`
- Create: `backend/app/seed/aws_domains.py`
- Create: `backend/app/seed/aws_questions.py`
- Create: `backend/app/seed/aws_cheatsheets.py`
- Create: `backend/app/seed/parsers/__init__.py`
- Create: `backend/app/seed/parsers/ditectrev.py`
- Create: `backend/app/seed/parsers/kananinirav.py`

- [ ] **Step 1: Create seed entry point**

```python
# backend/app/seed/__main__.py
import asyncio
from app.database import engine, async_session, Base
from app.seed.instructor import seed_instructor
from app.seed.aws_domains import seed_aws_subject_and_domains
from app.seed.aws_questions import seed_aws_questions
from app.seed.aws_cheatsheets import seed_aws_cheatsheets

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        print("Seeding instructor...")
        instructor = await seed_instructor(db)
        print("Seeding AWS subject and domains...")
        subject, domains = await seed_aws_subject_and_domains(db, instructor.id)
        print("Seeding AWS questions from GitHub sources...")
        count = await seed_aws_questions(db, subject, domains)
        print(f"Seeded {count} questions")
        print("Seeding AWS cheatsheets...")
        await seed_aws_cheatsheets(db, domains)
        print("Done!")

asyncio.run(main())
```

Run: `cd /home/aiden/Aiden/quizforge/backend && python -m app.seed`

- [ ] **Step 2: Create instructor seed**

```python
# backend/app/seed/instructor.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.services.auth import hash_password

INSTRUCTOR_USERNAME = "instructor"
INSTRUCTOR_PASSWORD = "quizforge-admin"
INSTRUCTOR_FULLNAME = "QuizForge Instructor"

async def seed_instructor(db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.username == INSTRUCTOR_USERNAME))
    existing = result.scalar_one_or_none()
    if existing:
        print("  Instructor already exists, skipping")
        return existing

    user = User(
        full_name=INSTRUCTOR_FULLNAME,
        username=INSTRUCTOR_USERNAME,
        password_hash=hash_password(INSTRUCTOR_PASSWORD),
        role="instructor",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    print(f"  Created instructor: {INSTRUCTOR_USERNAME} / {INSTRUCTOR_PASSWORD}")
    return user
```

- [ ] **Step 3: Create AWS domains seed**

```python
# backend/app/seed/aws_domains.py
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
```

- [ ] **Step 4: Create Ditectrev markdown parser**

```python
# backend/app/seed/parsers/ditectrev.py
import re

def parse_ditectrev_readme(content: str) -> list[dict]:
    """Parse Ditectrev README.md format.

    Format:
    ### Question text
    - [x] Correct answer
    - [ ] Wrong answer
    """
    questions = []
    # Split by ### headers (questions)
    blocks = re.split(r'^### ', content, flags=re.MULTILINE)

    for block in blocks[1:]:  # Skip content before first ###
        lines = block.strip().split('\n')
        if not lines:
            continue

        question_text = lines[0].strip()
        if not question_text:
            continue

        # Skip "Back to Top" links and non-question headers
        if "Back to Top" in question_text or "Table of Contents" in question_text:
            continue

        choices = []
        for line in lines[1:]:
            line = line.strip()
            correct_match = re.match(r'^- \[x\]\s*(.+)', line)
            wrong_match = re.match(r'^- \[ \]\s*(.+)', line)
            if correct_match:
                choices.append({"text": correct_match.group(1).strip().rstrip('.'), "is_correct": True})
            elif wrong_match:
                choices.append({"text": wrong_match.group(1).strip().rstrip('.'), "is_correct": False})

        if len(choices) >= 2:
            correct_count = sum(1 for c in choices if c["is_correct"])
            if correct_count > 1:
                q_type = "multiple"
            else:
                q_type = "single"

            questions.append({
                "question_text": question_text,
                "question_type": q_type,
                "choices": choices,
                "explanation": None,
            })

    return questions
```

- [ ] **Step 5: Create Kananinirav markdown parser**

```python
# backend/app/seed/parsers/kananinirav.py
import re

def parse_kananinirav_exam(content: str) -> list[dict]:
    """Parse kananinirav practice exam format.

    Format:
    1. Question text
        - A. Choice A
        - B. Choice B
        <details><summary>Answer</summary>
          Correct answer: A
        </details>
    """
    questions = []
    # Split by numbered questions
    blocks = re.split(r'^\d+\.\s+', content, flags=re.MULTILINE)

    for block in blocks[1:]:  # Skip content before first question
        lines = block.strip().split('\n')
        if not lines:
            continue

        question_text = lines[0].strip()

        choices = []
        choice_map = {}  # letter -> index
        for line in lines[1:]:
            line = line.strip()
            choice_match = re.match(r'^-\s+([A-F])\.\s+(.+)', line)
            if choice_match:
                letter = choice_match.group(1)
                text = choice_match.group(2).strip().rstrip('.')
                choice_map[letter] = len(choices)
                choices.append({"text": text, "is_correct": False})

        # Find correct answer in <details>
        full_block = '\n'.join(lines)
        answer_match = re.search(r'Correct answer:\s*([A-F,\s]+)', full_block, re.IGNORECASE)
        if answer_match and choices:
            correct_letters = [l.strip() for l in answer_match.group(1).split(',')]
            for letter in correct_letters:
                if letter in choice_map:
                    choices[choice_map[letter]]["is_correct"] = True

            correct_count = sum(1 for c in choices if c["is_correct"])
            if correct_count > 1:
                q_type = "multiple"
            else:
                q_type = "single"

            questions.append({
                "question_text": question_text,
                "question_type": q_type,
                "choices": choices,
                "explanation": None,
            })

    return questions
```

- [ ] **Step 6: Create question seeder with domain categorization**

```python
# backend/app/seed/aws_questions.py
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
        resp = await client.get(DITECTREV_URL)
        if resp.status_code == 200:
            parsed = parse_ditectrev_readme(resp.text)
            print(f"  Parsed {len(parsed)} questions from Ditectrev")
            all_questions.extend(parsed)

        # Parse Kananinirav practice exams
        for filename in KANANINIRAV_FILES:
            url = f"{KANANINIRAV_BASE}/{filename}"
            resp = await client.get(url)
            if resp.status_code == 200:
                parsed = parse_kananinirav_exam(resp.text)
                all_questions.extend(parsed)
                print(f"  Parsed {len(parsed)} from {filename}")

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
```

- [ ] **Step 7: Create cheatsheets seed**

```python
# backend/app/seed/aws_cheatsheets.py
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
```

- [ ] **Step 8: Run the seed script**

```bash
cd /home/aiden/Aiden/quizforge/backend
docker compose up -d db  # ensure DB is running
python -m app.seed
```

Expected: Instructor created, 8 domains created, 500+ questions seeded, 8 cheatsheets created.

- [ ] **Step 9: Commit**

```bash
git add -A
git commit -m "feat: add seed script with instructor, AWS domains, questions from GitHub, and cheatsheets"
```

---

### Task 5: CRUD Routers (Subjects, Domains, Questions, PDFs, Study)

**Files:**
- Create: `backend/app/schemas/subject.py`
- Create: `backend/app/schemas/domain.py`
- Create: `backend/app/schemas/question.py`
- Create: `backend/app/routers/subjects.py`
- Create: `backend/app/routers/domains.py`
- Create: `backend/app/routers/questions.py`
- Create: `backend/app/routers/study.py`
- Modify: `backend/app/main.py` (register routers)

- [ ] **Step 1: Create subject schemas and router**

```python
# backend/app/schemas/subject.py
from pydantic import BaseModel

class SubjectCreate(BaseModel):
    name: str
    description: str | None = None

class SubjectResponse(BaseModel):
    id: str
    name: str
    description: str | None
    created_at: str

    class Config:
        from_attributes = True

class DomainInSubject(BaseModel):
    id: str
    name: str
    description: str | None
    question_count: int = 0

    class Config:
        from_attributes = True
```

```python
# backend/app/routers/subjects.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.subject import Subject
from app.models.domain import Domain
from app.models.question import Question
from app.models.user import User
from app.services.auth import require_instructor
from app.schemas.subject import SubjectCreate, SubjectResponse, DomainInSubject

router = APIRouter(prefix="/api/subjects", tags=["subjects"])

@router.get("", response_model=list[SubjectResponse])
async def list_subjects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Subject).order_by(Subject.created_at.desc()))
    return [SubjectResponse(
        id=str(s.id), name=s.name, description=s.description,
        created_at=s.created_at.isoformat()
    ) for s in result.scalars()]

@router.post("", response_model=SubjectResponse)
async def create_subject(
    body: SubjectCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_instructor),
):
    subject = Subject(name=body.name, description=body.description, created_by=user.id)
    db.add(subject)
    await db.commit()
    await db.refresh(subject)
    return SubjectResponse(
        id=str(subject.id), name=subject.name, description=subject.description,
        created_at=subject.created_at.isoformat()
    )

@router.get("/{subject_id}/domains", response_model=list[DomainInSubject])
async def list_domains(subject_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Domain, func.count(Question.id).label("qcount"))
        .outerjoin(Question, Question.domain_id == Domain.id)
        .where(Domain.subject_id == subject_id)
        .group_by(Domain.id)
        .order_by(Domain.name)
    )
    return [DomainInSubject(
        id=str(row[0].id), name=row[0].name, description=row[0].description,
        question_count=row[1]
    ) for row in result.all()]
```

- [ ] **Step 2: Create domain schemas and router**

```python
# backend/app/schemas/domain.py
from pydantic import BaseModel

class DomainCreate(BaseModel):
    name: str
    description: str | None = None

class DomainUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

class DomainResponse(BaseModel):
    id: str
    subject_id: str
    name: str
    description: str | None

    class Config:
        from_attributes = True
```

```python
# backend/app/routers/domains.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.domain import Domain
from app.models.question import Question
from app.models.user import User
from app.services.auth import require_instructor
from app.schemas.domain import DomainCreate, DomainUpdate, DomainResponse

router = APIRouter(prefix="/api", tags=["domains"])

@router.post("/subjects/{subject_id}/domains", response_model=DomainResponse)
async def create_domain(
    subject_id: str,
    body: DomainCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_instructor),
):
    domain = Domain(subject_id=subject_id, name=body.name, description=body.description)
    db.add(domain)
    await db.commit()
    await db.refresh(domain)
    return DomainResponse(id=str(domain.id), subject_id=str(domain.subject_id), name=domain.name, description=domain.description)

@router.put("/domains/{domain_id}", response_model=DomainResponse)
async def update_domain(
    domain_id: str,
    body: DomainUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_instructor),
):
    result = await db.execute(select(Domain).where(Domain.id == domain_id))
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(404, "Domain not found")
    if body.name is not None:
        domain.name = body.name
    if body.description is not None:
        domain.description = body.description
    await db.commit()
    await db.refresh(domain)
    return DomainResponse(id=str(domain.id), subject_id=str(domain.subject_id), name=domain.name, description=domain.description)

@router.delete("/domains/{domain_id}")
async def delete_domain(
    domain_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_instructor),
):
    result = await db.execute(select(Domain).where(Domain.id == domain_id))
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(404, "Domain not found")
    # Check if questions exist
    count_result = await db.execute(
        select(func.count(Question.id)).where(Question.domain_id == domain_id)
    )
    count = count_result.scalar()
    if count > 0:
        raise HTTPException(409, f"Domain has {count} questions. Delete or reassign questions first.")
    await db.delete(domain)
    await db.commit()
    return {"ok": True}
```

- [ ] **Step 3: Create question schemas and router**

```python
# backend/app/schemas/question.py
from pydantic import BaseModel

class ChoiceSchema(BaseModel):
    text: str
    is_correct: bool

class QuestionUpdate(BaseModel):
    question_text: str | None = None
    question_type: str | None = None
    choices: list[ChoiceSchema] | None = None
    explanation: str | None = None
    domain_id: str | None = None

class QuestionResponse(BaseModel):
    id: str
    domain_id: str
    domain_name: str
    question_text: str
    question_type: str
    choices: list[ChoiceSchema]
    explanation: str | None
    source: str
    created_at: str

    class Config:
        from_attributes = True
```

```python
# backend/app/routers/questions.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.question import Question
from app.models.session import SessionQuestion, Session
from app.models.user import User
from app.services.auth import require_instructor
from app.schemas.question import QuestionUpdate, QuestionResponse, ChoiceSchema

router = APIRouter(prefix="/api", tags=["questions"])

@router.get("/subjects/{subject_id}/questions", response_model=list[QuestionResponse])
async def list_questions(
    subject_id: str,
    domain_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_instructor),
):
    from app.models.domain import Domain
    query = (
        select(Question)
        .join(Domain, Question.domain_id == Domain.id)
        .where(Domain.subject_id == subject_id)
    )
    if domain_id:
        query = query.where(Question.domain_id == domain_id)
    query = query.order_by(Question.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    questions = result.scalars().all()
    return [QuestionResponse(
        id=str(q.id), domain_id=str(q.domain_id), domain_name=q.domain.name,
        question_text=q.question_text, question_type=q.question_type,
        choices=[ChoiceSchema(**c) for c in q.choices],
        explanation=q.explanation, source=q.source,
        created_at=q.created_at.isoformat()
    ) for q in questions]

@router.get("/questions/{question_id}", response_model=QuestionResponse)
async def get_question(question_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(require_instructor)):
    result = await db.execute(select(Question).where(Question.id == question_id))
    q = result.scalar_one_or_none()
    if not q:
        raise HTTPException(404, "Question not found")
    return QuestionResponse(
        id=str(q.id), domain_id=str(q.domain_id), domain_name=q.domain.name,
        question_text=q.question_text, question_type=q.question_type,
        choices=[ChoiceSchema(**c) for c in q.choices],
        explanation=q.explanation, source=q.source,
        created_at=q.created_at.isoformat()
    )

@router.put("/questions/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: str, body: QuestionUpdate,
    db: AsyncSession = Depends(get_db), user: User = Depends(require_instructor),
):
    result = await db.execute(select(Question).where(Question.id == question_id))
    q = result.scalar_one_or_none()
    if not q:
        raise HTTPException(404, "Question not found")
    if body.question_text is not None: q.question_text = body.question_text
    if body.question_type is not None: q.question_type = body.question_type
    if body.choices is not None: q.choices = [c.model_dump() for c in body.choices]
    if body.explanation is not None: q.explanation = body.explanation
    if body.domain_id is not None: q.domain_id = body.domain_id
    await db.commit()
    await db.refresh(q)
    return QuestionResponse(
        id=str(q.id), domain_id=str(q.domain_id), domain_name=q.domain.name,
        question_text=q.question_text, question_type=q.question_type,
        choices=[ChoiceSchema(**c) for c in q.choices],
        explanation=q.explanation, source=q.source,
        created_at=q.created_at.isoformat()
    )

@router.delete("/questions/{question_id}")
async def delete_question(
    question_id: str,
    db: AsyncSession = Depends(get_db), user: User = Depends(require_instructor),
):
    result = await db.execute(select(Question).where(Question.id == question_id))
    q = result.scalar_one_or_none()
    if not q:
        raise HTTPException(404, "Question not found")
    # Check if in active session
    active_result = await db.execute(
        select(SessionQuestion)
        .join(Session, SessionQuestion.session_id == Session.id)
        .where(SessionQuestion.question_id == question_id, Session.is_active == True)
        .limit(1)
    )
    if active_result.scalar_one_or_none():
        raise HTTPException(409, "Question is in an active session. Deactivate the session first.")
    await db.delete(q)
    await db.commit()
    return {"ok": True}
```

- [ ] **Step 4: Create study/cheatsheet router**

```python
# backend/app/routers/study.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.domain import Domain
from app.models.domain_cheatsheet import DomainCheatsheet
from app.schemas.domain import DomainResponse

router = APIRouter(prefix="/api/study", tags=["study"])

class CheatsheetResponse:
    pass

from pydantic import BaseModel

class StudyCardResponse(BaseModel):
    domain_id: str
    domain_name: str
    content: str

@router.get("/{subject_id}/cards", response_model=list[StudyCardResponse])
async def list_study_cards(subject_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Domain, DomainCheatsheet)
        .outerjoin(DomainCheatsheet, DomainCheatsheet.domain_id == Domain.id)
        .where(Domain.subject_id == subject_id)
        .order_by(Domain.name)
    )
    cards = []
    for domain, cheatsheet in result.all():
        if cheatsheet:
            cards.append(StudyCardResponse(
                domain_id=str(domain.id),
                domain_name=domain.name,
                content=cheatsheet.content,
            ))
    return cards

@router.get("/domain/{domain_id}", response_model=StudyCardResponse)
async def get_study_card(domain_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Domain, DomainCheatsheet)
        .outerjoin(DomainCheatsheet, DomainCheatsheet.domain_id == Domain.id)
        .where(Domain.id == domain_id)
    )
    row = result.one_or_none()
    if not row or not row[1]:
        raise HTTPException(404, "Study card not found")
    domain, cheatsheet = row
    return StudyCardResponse(
        domain_id=str(domain.id),
        domain_name=domain.name,
        content=cheatsheet.content,
    )
```

- [ ] **Step 5: Register all routers in main.py**

```python
# app/main.py — add these imports and registrations
from app.routers import auth, subjects, domains, questions, study

app.include_router(auth.router)
app.include_router(subjects.router)
app.include_router(domains.router)
app.include_router(questions.router)
app.include_router(study.router)
```

- [ ] **Step 6: Test CRUD endpoints**

```bash
# Login as instructor
curl -c cookies.txt -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"instructor","password":"quizforge-admin"}'

# List subjects
curl -b cookies.txt http://localhost:8000/api/subjects

# List domains for first subject
curl -b cookies.txt "http://localhost:8000/api/subjects/<subject-id>/domains"

# List questions
curl -b cookies.txt "http://localhost:8000/api/subjects/<subject-id>/questions?limit=5"

# Study cards
curl "http://localhost:8000/api/study/<subject-id>/cards"
```

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat: add CRUD routers for subjects, domains, questions, and study cards"
```

---

### Task 6: Session Management & Quiz Engine

**Files:**
- Create: `backend/app/schemas/session.py`
- Create: `backend/app/schemas/quiz.py`
- Create: `backend/app/routers/sessions.py`
- Create: `backend/app/routers/quiz.py`
- Create: `backend/app/services/quiz_engine.py`
- Create: `backend/app/services/grading.py`
- Modify: `backend/app/main.py` (register routers)

- [ ] **Step 1: Create quiz engine service**

```python
# backend/app/services/quiz_engine.py
import random
import math
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question import Question
from app.models.session import Session, SessionQuestion
from app.models.student_quiz import StudentQuiz


async def generate_quiz_for_student(
    db: AsyncSession, session: Session, student_id: str
) -> StudentQuiz:
    """Generate a unique shuffled quiz for a student.

    1. Fetch question pool grouped by domain
    2. Select proportional random subset
    3. Shuffle order and choices
    """
    # Check if student already has a quiz
    existing = await db.execute(
        select(StudentQuiz).where(
            StudentQuiz.session_id == session.id,
            StudentQuiz.student_id == student_id,
        )
    )
    existing_quiz = existing.scalar_one_or_none()
    if existing_quiz:
        return existing_quiz

    # Fetch pool grouped by domain
    result = await db.execute(
        select(Question)
        .join(SessionQuestion, SessionQuestion.question_id == Question.id)
        .where(SessionQuestion.session_id == session.id)
    )
    all_questions = result.scalars().all()

    by_domain = defaultdict(list)
    for q in all_questions:
        by_domain[str(q.domain_id)].append(q)

    total_pool = len(all_questions)
    target = min(session.questions_per_quiz, total_pool)

    # Proportional selection with largest-remainder method
    selected = []
    if total_pool > 0:
        allocations = {}
        remainders = {}
        allocated = 0

        for domain_id, questions in by_domain.items():
            proportion = len(questions) / total_pool
            exact = proportion * target
            floor_val = math.floor(exact)
            allocations[domain_id] = floor_val
            remainders[domain_id] = exact - floor_val
            allocated += floor_val

        # Distribute remaining slots
        remaining = target - allocated
        sorted_domains = sorted(remainders.keys(), key=lambda d: remainders[d], reverse=True)
        for i in range(remaining):
            allocations[sorted_domains[i % len(sorted_domains)]] += 1

        # Random sample from each domain
        for domain_id, count in allocations.items():
            pool = by_domain[domain_id]
            count = min(count, len(pool))
            selected.extend(random.sample(pool, count))

    # Shuffle question order
    random.shuffle(selected)

    # Generate shuffled choice indices for each question
    questions_order = []
    for q in selected:
        num_choices = len(q.choices)
        choices_order = list(range(num_choices))
        random.shuffle(choices_order)
        questions_order.append({
            "question_id": str(q.id),
            "choices_order": choices_order,
        })

    quiz = StudentQuiz(
        session_id=session.id,
        student_id=student_id,
        questions_order=questions_order,
        total_questions=len(selected),
    )
    db.add(quiz)
    await db.commit()
    await db.refresh(quiz)
    return quiz
```

- [ ] **Step 2: Create grading service**

```python
# backend/app/services/grading.py
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student_quiz import StudentQuiz
from app.models.student_answer import StudentAnswer
from app.models.question import Question


async def grade_quiz(db: AsyncSession, quiz: StudentQuiz) -> dict:
    """Grade a submitted quiz and return results."""
    result = await db.execute(
        select(StudentAnswer).where(StudentAnswer.student_quiz_id == quiz.id)
    )
    answers = result.scalars().all()

    total_correct = sum(1 for a in answers if a.is_correct)
    total_questions = quiz.total_questions
    score = (total_correct / total_questions * 100) if total_questions > 0 else 0

    quiz.submitted_at = datetime.now(timezone.utc)
    quiz.score = round(score, 1)
    quiz.total_correct = total_correct
    await db.commit()

    return {
        "score": quiz.score,
        "total_correct": total_correct,
        "total_questions": total_questions,
    }


def check_answer(question: Question, selected_choices: list[int]) -> bool:
    """Check if selected choices (original indices) are correct."""
    correct_indices = {i for i, c in enumerate(question.choices) if c.get("is_correct")}
    return set(selected_choices) == correct_indices
```

- [ ] **Step 3: Create session schemas**

```python
# backend/app/schemas/session.py
from pydantic import BaseModel

class SessionCreate(BaseModel):
    subject_id: str
    title: str
    domain_ids: list[str]
    questions_per_quiz: int
    time_limit_minutes: int | None = None

class SessionResponse(BaseModel):
    id: str
    subject_id: str
    title: str
    domain_ids: list[str]
    questions_per_quiz: int
    time_limit_minutes: int | None
    is_active: bool
    created_at: str
    question_pool_size: int = 0

class AttendanceEntry(BaseModel):
    student_id: str
    full_name: str
    status: str  # "joined", "in_progress", "completed"
    current_question: int | None = None
    total_questions: int = 0
    score: float | None = None

class SessionResultEntry(BaseModel):
    student_id: str
    full_name: str
    score: float
    total_correct: int
    total_questions: int
    time_taken_seconds: int | None
    domain_scores: dict[str, dict]  # {domain_name: {correct: int, total: int}}
```

- [ ] **Step 4: Create session router**

```python
# backend/app/routers/sessions.py
import io
import qrcode
import base64
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings
from app.models.user import User
from app.models.question import Question
from app.models.domain import Domain
from app.models.session import Session, SessionQuestion
from app.models.student_quiz import StudentQuiz
from app.models.student_answer import StudentAnswer
from app.services.auth import require_instructor
from app.schemas.session import SessionCreate, SessionResponse, AttendanceEntry, SessionResultEntry

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

def generate_qr_base64(url: str) -> str:
    qr = qrcode.make(url)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

@router.post("", response_model=SessionResponse)
async def create_session(
    body: SessionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_instructor),
):
    session = Session(
        subject_id=body.subject_id,
        title=body.title,
        created_by=user.id,
        domain_ids=body.domain_ids,
        questions_per_quiz=body.questions_per_quiz,
        time_limit_minutes=body.time_limit_minutes,
    )
    db.add(session)
    await db.flush()

    # Populate session_questions from selected domains
    result = await db.execute(
        select(Question).where(Question.domain_id.in_([d for d in body.domain_ids]))
    )
    questions = result.scalars().all()
    for q in questions:
        db.add(SessionQuestion(session_id=session.id, question_id=q.id))

    await db.commit()
    await db.refresh(session)

    return SessionResponse(
        id=str(session.id), subject_id=str(session.subject_id),
        title=session.title, domain_ids=session.domain_ids,
        questions_per_quiz=session.questions_per_quiz,
        time_limit_minutes=session.time_limit_minutes,
        is_active=session.is_active, created_at=session.created_at.isoformat(),
        question_pool_size=len(questions),
    )

@router.get("", response_model=list[SessionResponse])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_instructor),
):
    result = await db.execute(select(Session).order_by(Session.created_at.desc()))
    sessions = result.scalars().all()
    responses = []
    for s in sessions:
        pool_result = await db.execute(
            select(func.count(SessionQuestion.id)).where(SessionQuestion.session_id == s.id)
        )
        pool_size = pool_result.scalar()
        responses.append(SessionResponse(
            id=str(s.id), subject_id=str(s.subject_id),
            title=s.title, domain_ids=s.domain_ids or [],
            questions_per_quiz=s.questions_per_quiz,
            time_limit_minutes=s.time_limit_minutes,
            is_active=s.is_active, created_at=s.created_at.isoformat(),
            question_pool_size=pool_size,
        ))
    return responses

@router.get("/{session_id}")
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found")

    pool_result = await db.execute(
        select(func.count(SessionQuestion.id)).where(SessionQuestion.session_id == session.id)
    )
    pool_size = pool_result.scalar()

    qr_url = f"{settings.frontend_url}/session/{session_id}"
    qr_base64 = generate_qr_base64(qr_url)

    return {
        "id": str(session.id),
        "subject_id": str(session.subject_id),
        "subject_name": session.subject.name if session.subject else None,
        "title": session.title,
        "domain_ids": session.domain_ids or [],
        "questions_per_quiz": session.questions_per_quiz,
        "time_limit_minutes": session.time_limit_minutes,
        "is_active": session.is_active,
        "created_at": session.created_at.isoformat(),
        "question_pool_size": pool_size,
        "qr_code": qr_base64,
        "qr_url": qr_url,
    }

@router.put("/{session_id}/toggle")
async def toggle_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_instructor),
):
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found")
    session.is_active = not session.is_active
    await db.commit()
    return {"is_active": session.is_active}

@router.get("/{session_id}/attendance", response_model=list[AttendanceEntry])
async def get_attendance(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_instructor),
):
    result = await db.execute(
        select(StudentQuiz).where(StudentQuiz.session_id == session_id)
    )
    quizzes = result.scalars().all()
    entries = []
    for q in quizzes:
        # Count answered questions
        ans_result = await db.execute(
            select(func.count(StudentAnswer.id)).where(StudentAnswer.student_quiz_id == q.id)
        )
        answered = ans_result.scalar()

        if q.submitted_at:
            status = "completed"
        elif answered > 0:
            status = "in_progress"
        else:
            status = "joined"

        entries.append(AttendanceEntry(
            student_id=str(q.student_id),
            full_name=q.student.full_name,
            status=status,
            current_question=answered if status == "in_progress" else None,
            total_questions=q.total_questions,
            score=q.score,
        ))
    return entries

@router.get("/{session_id}/results", response_model=list[SessionResultEntry])
async def get_results(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_instructor),
):
    result = await db.execute(
        select(StudentQuiz).where(
            StudentQuiz.session_id == session_id,
            StudentQuiz.submitted_at.isnot(None),
        )
    )
    quizzes = result.scalars().all()
    entries = []
    for q in quizzes:
        time_taken = None
        if q.submitted_at and q.started_at:
            time_taken = int((q.submitted_at - q.started_at).total_seconds())

        # Domain breakdown
        domain_scores = {}
        for a in q.answers:
            domain_name = a.question.domain.name if a.question.domain else "Unknown"
            if domain_name not in domain_scores:
                domain_scores[domain_name] = {"correct": 0, "total": 0}
            domain_scores[domain_name]["total"] += 1
            if a.is_correct:
                domain_scores[domain_name]["correct"] += 1

        entries.append(SessionResultEntry(
            student_id=str(q.student_id),
            full_name=q.student.full_name,
            score=q.score or 0,
            total_correct=q.total_correct or 0,
            total_questions=q.total_questions,
            time_taken_seconds=time_taken,
            domain_scores=domain_scores,
        ))
    return sorted(entries, key=lambda e: e.score, reverse=True)
```

- [ ] **Step 5: Create quiz schemas**

```python
# backend/app/schemas/quiz.py
from pydantic import BaseModel

class QuizMetaResponse(BaseModel):
    quiz_id: str
    session_title: str
    total_questions: int
    time_limit_minutes: int | None
    started_at: str
    submitted_at: str | None

class QuizQuestionResponse(BaseModel):
    question_number: int
    total_questions: int
    question_text: str
    question_type: str
    domain_name: str
    choices: list[dict]  # [{index: int, text: str}] — shuffled order, no is_correct
    selected_choices: list[int] | None  # Previously saved answer (original indices)

class SubmitResponse(BaseModel):
    score: float
    total_correct: int
    total_questions: int
    results: list[dict]  # Per-question results
```

- [ ] **Step 6: Create quiz router (student-facing)**

```python
# backend/app/routers/quiz.py
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.session import Session
from app.models.question import Question
from app.models.student_quiz import StudentQuiz
from app.models.student_answer import StudentAnswer
from app.services.auth import get_current_user
from app.services.quiz_engine import generate_quiz_for_student
from app.services.grading import grade_quiz, check_answer
from app.schemas.quiz import QuizMetaResponse, QuizQuestionResponse, SubmitResponse

router = APIRouter(prefix="/api", tags=["quiz"])

class AnswerRequest(BaseModel):
    selected_choices: list[int]  # Original indices

@router.post("/sessions/{session_id}/join")
async def join_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role != "student":
        raise HTTPException(403, "Only students can join sessions")

    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found")
    if not session.is_active:
        raise HTTPException(400, "Session is not active")

    quiz = await generate_quiz_for_student(db, session, str(user.id))
    return {
        "quiz_id": str(quiz.id),
        "total_questions": quiz.total_questions,
    }

@router.get("/quiz/{quiz_id}", response_model=QuizMetaResponse)
async def get_quiz_meta(
    quiz_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(StudentQuiz).where(StudentQuiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    if not quiz or str(quiz.student_id) != str(user.id):
        raise HTTPException(404, "Quiz not found")

    session_result = await db.execute(select(Session).where(Session.id == quiz.session_id))
    session = session_result.scalar_one_or_none()

    return QuizMetaResponse(
        quiz_id=str(quiz.id),
        session_title=session.title if session else "",
        total_questions=quiz.total_questions,
        time_limit_minutes=session.time_limit_minutes if session else None,
        started_at=quiz.started_at.isoformat(),
        submitted_at=quiz.submitted_at.isoformat() if quiz.submitted_at else None,
    )

@router.get("/quiz/{quiz_id}/question/{n}", response_model=QuizQuestionResponse)
async def get_question(
    quiz_id: str, n: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(StudentQuiz).where(StudentQuiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    if not quiz or str(quiz.student_id) != str(user.id):
        raise HTTPException(404, "Quiz not found")
    if n < 1 or n > quiz.total_questions:
        raise HTTPException(400, f"Question number must be between 1 and {quiz.total_questions}")

    order_entry = quiz.questions_order[n - 1]
    question_id = order_entry["question_id"]
    choices_order = order_entry["choices_order"]

    q_result = await db.execute(select(Question).where(Question.id == question_id))
    question = q_result.scalar_one_or_none()
    if not question:
        raise HTTPException(500, "Question data missing")

    # Build shuffled choices (no is_correct)
    shuffled_choices = []
    for display_idx, original_idx in enumerate(choices_order):
        shuffled_choices.append({
            "index": original_idx,  # Original index for answer submission
            "text": question.choices[original_idx]["text"],
        })

    # Check for existing answer
    ans_result = await db.execute(
        select(StudentAnswer).where(
            StudentAnswer.student_quiz_id == quiz.id,
            StudentAnswer.question_id == question_id,
        )
    )
    existing_answer = ans_result.scalar_one_or_none()

    return QuizQuestionResponse(
        question_number=n,
        total_questions=quiz.total_questions,
        question_text=question.question_text,
        question_type=question.question_type,
        domain_name=question.domain.name if question.domain else "",
        choices=shuffled_choices,
        selected_choices=existing_answer.selected_choices if existing_answer else None,
    )

@router.post("/quiz/{quiz_id}/question/{n}/answer")
async def save_answer(
    quiz_id: str, n: int, body: AnswerRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(StudentQuiz).where(StudentQuiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    if not quiz or str(quiz.student_id) != str(user.id):
        raise HTTPException(404, "Quiz not found")
    if quiz.submitted_at:
        raise HTTPException(400, "Quiz already submitted")
    if n < 1 or n > quiz.total_questions:
        raise HTTPException(400, "Invalid question number")

    order_entry = quiz.questions_order[n - 1]
    question_id = order_entry["question_id"]

    q_result = await db.execute(select(Question).where(Question.id == question_id))
    question = q_result.scalar_one_or_none()

    is_correct = check_answer(question, body.selected_choices)

    # Upsert answer
    ans_result = await db.execute(
        select(StudentAnswer).where(
            StudentAnswer.student_quiz_id == quiz.id,
            StudentAnswer.question_id == question_id,
        )
    )
    existing = ans_result.scalar_one_or_none()
    if existing:
        existing.selected_choices = body.selected_choices
        existing.is_correct = is_correct
        existing.answered_at = datetime.now(timezone.utc)
    else:
        answer = StudentAnswer(
            student_quiz_id=quiz.id,
            question_id=question_id,
            selected_choices=body.selected_choices,
            is_correct=is_correct,
        )
        db.add(answer)

    await db.commit()
    return {"ok": True}

@router.post("/quiz/{quiz_id}/submit", response_model=SubmitResponse)
async def submit_quiz(
    quiz_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(StudentQuiz).where(StudentQuiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    if not quiz or str(quiz.student_id) != str(user.id):
        raise HTTPException(404, "Quiz not found")
    if quiz.submitted_at:
        raise HTTPException(400, "Quiz already submitted")

    grade_result = await grade_quiz(db, quiz)

    # Build per-question results for review
    results = []
    for i, order_entry in enumerate(quiz.questions_order):
        qid = order_entry["question_id"]
        q_result = await db.execute(select(Question).where(Question.id == qid))
        question = q_result.scalar_one_or_none()

        ans_result = await db.execute(
            select(StudentAnswer).where(
                StudentAnswer.student_quiz_id == quiz.id,
                StudentAnswer.question_id == qid,
            )
        )
        answer = ans_result.scalar_one_or_none()

        results.append({
            "question_number": i + 1,
            "question_text": question.question_text,
            "domain_name": question.domain.name if question.domain else "",
            "choices": question.choices,  # Full choices with is_correct
            "selected_choices": answer.selected_choices if answer else [],
            "is_correct": answer.is_correct if answer else False,
            "explanation": question.explanation,
        })

    return SubmitResponse(
        score=grade_result["score"],
        total_correct=grade_result["total_correct"],
        total_questions=grade_result["total_questions"],
        results=results,
    )
```

- [ ] **Step 7: Register session and quiz routers in main.py**

```python
from app.routers import auth, subjects, domains, questions, study, sessions, quiz

app.include_router(sessions.router)
app.include_router(quiz.router)
```

- [ ] **Step 8: Test the full quiz flow**

```bash
# 1. Login as instructor
curl -c inst.txt -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"instructor","password":"quizforge-admin"}'

# 2. Create session (use actual subject_id and domain_ids from /api/subjects)
curl -b inst.txt -X POST http://localhost:8000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"subject_id":"<id>","title":"Test Session","domain_ids":["<d1>","<d2>"],"questions_per_quiz":5}'

# 3. Register as student
curl -c stud.txt -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Test Student","username":"student1","password":"pass123"}'

# 4. Join session
curl -b stud.txt -X POST http://localhost:8000/api/sessions/<session-id>/join

# 5. Get question 1
curl -b stud.txt http://localhost:8000/api/quiz/<quiz-id>/question/1

# 6. Answer question 1
curl -b stud.txt -X POST http://localhost:8000/api/quiz/<quiz-id>/question/1/answer \
  -H "Content-Type: application/json" -d '{"selected_choices":[0]}'

# 7. Submit
curl -b stud.txt -X POST http://localhost:8000/api/quiz/<quiz-id>/submit
```

- [ ] **Step 9: Commit**

```bash
git add -A
git commit -m "feat: add session management, quiz engine with proportional shuffling, and auto-grading"
```

---

### Task 7: PDF Upload & LLM Parsing

**Files:**
- Create: `backend/app/schemas/pdf.py`
- Create: `backend/app/routers/pdfs.py`
- Create: `backend/app/services/pdf_parser.py`
- Modify: `backend/app/main.py` (register router)

- [ ] **Step 1: Create PDF parser service**

```python
# backend/app/services/pdf_parser.py
import json
import pdfplumber
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.domain import Domain
from app.models.question import Question
from app.models.pdf_upload import PdfUpload

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def build_parsing_prompt(text: str, domains: list[dict]) -> str:
    domain_list = "\n".join(f"- {d['name']}: {d['description']}" for d in domains)
    return f"""You are a quiz question extractor. Parse the following text and extract all quiz questions.

For each question, determine:
1. The question text
2. The answer choices (each with text and whether it's correct)
3. The question type: "single" (one correct answer), "multiple" (multiple correct), or "true_false"
4. Which domain it belongs to from this list:
{domain_list}
5. A brief explanation of why the correct answer is correct

Return a JSON array of objects with this exact structure:
[
  {{
    "question_text": "...",
    "question_type": "single|multiple|true_false",
    "domain": "exact domain name from list above",
    "choices": [
      {{"text": "...", "is_correct": true}},
      {{"text": "...", "is_correct": false}}
    ],
    "explanation": "..."
  }}
]

Return ONLY the JSON array, no other text.

--- TEXT START ---
{text[:15000]}
--- TEXT END ---"""


async def parse_pdf_with_llm(
    db: AsyncSession, pdf_upload: PdfUpload, domains: list[Domain]
) -> int:
    """Extract text from PDF, send to LLM, store questions. Returns count."""
    pdf_upload.status = "processing"
    await db.commit()

    try:
        text = extract_text_from_pdf(pdf_upload.file_path)
        if not text.strip():
            raise ValueError("No text extracted from PDF")

        domain_info = [{"name": d.name, "description": d.description or ""} for d in domains]
        prompt = build_parsing_prompt(text, domain_info)

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
                    "temperature": 0.1,
                },
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]

        # Parse JSON from response (handle markdown code blocks)
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            content = content.rsplit("```", 1)[0]

        questions_data = json.loads(content)

        # Build domain name->id mapping
        domain_map = {d.name: d.id for d in domains}

        count = 0
        for q in questions_data:
            domain_name = q.get("domain", "")
            domain_id = domain_map.get(domain_name)
            if not domain_id:
                # Try fuzzy match
                for name, did in domain_map.items():
                    if domain_name.lower() in name.lower() or name.lower() in domain_name.lower():
                        domain_id = did
                        break
            if not domain_id:
                domain_id = list(domain_map.values())[0]  # Fallback to first domain

            question = Question(
                domain_id=domain_id,
                source_pdf_id=pdf_upload.id,
                source="pdf",
                question_text=q["question_text"],
                question_type=q.get("question_type", "single"),
                choices=q["choices"],
                explanation=q.get("explanation"),
            )
            db.add(question)
            count += 1

        pdf_upload.status = "done"
        pdf_upload.questions_extracted = count
        await db.commit()
        return count

    except Exception as e:
        pdf_upload.status = "error"
        pdf_upload.error_message = str(e)[:500]
        await db.commit()
        raise
```

- [ ] **Step 2: Create PDF schemas and router**

```python
# backend/app/schemas/pdf.py
from pydantic import BaseModel

class PdfUploadResponse(BaseModel):
    id: str
    filename: str
    status: str
    questions_extracted: int
    error_message: str | None
    uploaded_at: str
```

```python
# backend/app/routers/pdfs.py
import os
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, async_session
from app.models.user import User
from app.models.domain import Domain
from app.models.pdf_upload import PdfUpload
from app.services.auth import require_instructor
from app.services.pdf_parser import parse_pdf_with_llm
from app.schemas.pdf import PdfUploadResponse

router = APIRouter(prefix="/api/subjects/{subject_id}/pdfs", tags=["pdfs"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

async def _process_pdf(pdf_id: str, subject_id: str):
    """Background task to parse PDF with LLM."""
    async with async_session() as db:
        result = await db.execute(select(PdfUpload).where(PdfUpload.id == pdf_id))
        pdf_upload = result.scalar_one()
        domain_result = await db.execute(
            select(Domain).where(Domain.subject_id == subject_id)
        )
        domains = list(domain_result.scalars())
        await parse_pdf_with_llm(db, pdf_upload, domains)

@router.post("", response_model=list[PdfUploadResponse])
async def upload_pdfs(
    subject_id: str,
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_instructor),
):
    responses = []
    for file in files:
        if not file.filename.endswith(".pdf"):
            raise HTTPException(400, f"File {file.filename} is not a PDF")

        file_id = str(uuid.uuid4())
        file_path = UPLOAD_DIR / f"{file_id}.pdf"
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        pdf_upload = PdfUpload(
            subject_id=subject_id,
            filename=file.filename,
            file_path=str(file_path),
            uploaded_by=user.id,
        )
        db.add(pdf_upload)
        await db.commit()
        await db.refresh(pdf_upload)

        background_tasks.add_task(_process_pdf, str(pdf_upload.id), subject_id)

        responses.append(PdfUploadResponse(
            id=str(pdf_upload.id),
            filename=pdf_upload.filename,
            status=pdf_upload.status,
            questions_extracted=pdf_upload.questions_extracted,
            error_message=pdf_upload.error_message,
            uploaded_at=pdf_upload.uploaded_at.isoformat(),
        ))
    return responses

@router.get("", response_model=list[PdfUploadResponse])
async def list_pdfs(
    subject_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_instructor),
):
    result = await db.execute(
        select(PdfUpload).where(PdfUpload.subject_id == subject_id).order_by(PdfUpload.uploaded_at.desc())
    )
    return [PdfUploadResponse(
        id=str(p.id), filename=p.filename, status=p.status,
        questions_extracted=p.questions_extracted,
        error_message=p.error_message,
        uploaded_at=p.uploaded_at.isoformat(),
    ) for p in result.scalars()]

@router.post("/{pdf_id}/reprocess")
async def reprocess_pdf(
    subject_id: str, pdf_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_instructor),
):
    result = await db.execute(select(PdfUpload).where(PdfUpload.id == pdf_id))
    pdf_upload = result.scalar_one_or_none()
    if not pdf_upload:
        raise HTTPException(404, "PDF not found")
    if pdf_upload.status not in ("error", "done"):
        raise HTTPException(400, "Can only reprocess errored or completed uploads")

    # Delete old questions from this PDF
    from app.models.question import Question
    await db.execute(
        select(Question).where(Question.source_pdf_id == pdf_id).execution_options(synchronize_session="fetch")
    )
    # Use delete statement
    from sqlalchemy import delete
    await db.execute(delete(Question).where(Question.source_pdf_id == pdf_id))

    pdf_upload.status = "pending"
    pdf_upload.questions_extracted = 0
    pdf_upload.error_message = None
    await db.commit()

    background_tasks.add_task(_process_pdf, pdf_id, subject_id)
    return {"ok": True}
```

- [ ] **Step 3: Register PDF router**

```python
# Add to app/main.py
from app.routers import pdfs
app.include_router(pdfs.router)
```

- [ ] **Step 4: Test PDF upload**

```bash
curl -b inst.txt -X POST "http://localhost:8000/api/subjects/<subject-id>/pdfs" \
  -F "files=@test.pdf"
```

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add PDF upload with async LLM parsing via OpenRouter"
```

---

## Phase 2: Frontend

### Task 8: Next.js Project Setup

**Files:**
- Create: `frontend/` (Next.js project via create-next-app)
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/lib/auth.tsx`

- [ ] **Step 1: Create Next.js project**

```bash
cd /home/aiden/Aiden/quizforge
npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir --no-import-alias
```

- [ ] **Step 2: Create API client**

```typescript
// frontend/src/lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function apiFetch(path: string, options: RequestInit = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || "API error");
  }
  return res.json();
}

export const api = {
  // Auth
  register: (data: { full_name: string; username: string; password: string }) =>
    apiFetch("/api/auth/register", { method: "POST", body: JSON.stringify(data) }),
  login: (data: { username: string; password: string }) =>
    apiFetch("/api/auth/login", { method: "POST", body: JSON.stringify(data) }),
  me: () => apiFetch("/api/auth/me"),
  logout: () => apiFetch("/api/auth/logout", { method: "POST" }),

  // Subjects & Domains
  getSubjects: () => apiFetch("/api/subjects"),
  getDomains: (subjectId: string) => apiFetch(`/api/subjects/${subjectId}/domains`),

  // Sessions
  getSessions: () => apiFetch("/api/sessions"),
  getSession: (id: string) => apiFetch(`/api/sessions/${id}`),
  createSession: (data: any) => apiFetch("/api/sessions", { method: "POST", body: JSON.stringify(data) }),
  toggleSession: (id: string) => apiFetch(`/api/sessions/${id}/toggle`, { method: "PUT" }),
  getAttendance: (id: string) => apiFetch(`/api/sessions/${id}/attendance`),
  getResults: (id: string) => apiFetch(`/api/sessions/${id}/results`),

  // Quiz (student)
  joinSession: (sessionId: string) => apiFetch(`/api/sessions/${sessionId}/join`, { method: "POST" }),
  getQuizMeta: (quizId: string) => apiFetch(`/api/quiz/${quizId}`),
  getQuestion: (quizId: string, n: number) => apiFetch(`/api/quiz/${quizId}/question/${n}`),
  saveAnswer: (quizId: string, n: number, data: { selected_choices: number[] }) =>
    apiFetch(`/api/quiz/${quizId}/question/${n}/answer`, { method: "POST", body: JSON.stringify(data) }),
  submitQuiz: (quizId: string) => apiFetch(`/api/quiz/${quizId}/submit`, { method: "POST" }),

  // Questions
  getQuestions: (subjectId: string, params?: string) => apiFetch(`/api/subjects/${subjectId}/questions${params ? `?${params}` : ""}`),
  updateQuestion: (id: string, data: any) => apiFetch(`/api/questions/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteQuestion: (id: string) => apiFetch(`/api/questions/${id}`, { method: "DELETE" }),

  // PDFs
  uploadPdfs: (subjectId: string, files: FileList) => {
    const formData = new FormData();
    Array.from(files).forEach(f => formData.append("files", f));
    return fetch(`${API_BASE}/api/subjects/${subjectId}/pdfs`, {
      method: "POST", credentials: "include", body: formData,
    }).then(r => r.json());
  },
  getPdfs: (subjectId: string) => apiFetch(`/api/subjects/${subjectId}/pdfs`),

  // Study
  getStudyCards: (subjectId: string) => apiFetch(`/api/study/${subjectId}/cards`),
  getStudyCard: (domainId: string) => apiFetch(`/api/study/domain/${domainId}`),
};
```

- [ ] **Step 3: Create auth context**

```typescript
// frontend/src/lib/auth.tsx
"use client";
import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { api } from "./api";

type User = { id: string; full_name: string; username: string; role: string } | null;

const AuthContext = createContext<{
  user: User;
  loading: boolean;
  refresh: () => Promise<void>;
}>({ user: null, loading: true, refresh: async () => {} });

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User>(null);
  const [loading, setLoading] = useState(true);

  const refresh = async () => {
    try {
      const data = await api.me();
      setUser(data);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { refresh(); }, []);

  return (
    <AuthContext.Provider value={{ user, loading, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
```

- [ ] **Step 4: Update root layout with AuthProvider**

```typescript
// frontend/src/app/layout.tsx
import type { Metadata } from "next";
import { AuthProvider } from "@/lib/auth";
import "./globals.css";

export const metadata: Metadata = {
  title: "QuizForge",
  description: "Classroom quiz platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
```

- [ ] **Step 5: Add .env.local**

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

- [ ] **Step 6: Verify**

```bash
cd frontend && npm run dev
# Open http://localhost:3000
```

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat: scaffold Next.js frontend with API client and auth context"
```

---

### Task 9: Student Pages (QR Login, Quiz, Results)

**Files:**
- Create: `frontend/src/app/(student)/session/[id]/page.tsx`
- Create: `frontend/src/app/(student)/quiz/[id]/page.tsx`
- Create: `frontend/src/app/(student)/results/[id]/page.tsx`
- Create: `frontend/src/app/(student)/study/page.tsx`
- Create: `frontend/src/app/(student)/study/[id]/page.tsx`
- Create: `frontend/src/components/AntiCopyPaste.tsx`

- [ ] **Step 1: Create AntiCopyPaste wrapper component**

```typescript
// frontend/src/components/AntiCopyPaste.tsx
"use client";
import { useEffect, ReactNode } from "react";

export default function AntiCopyPaste({ children }: { children: ReactNode }) {
  useEffect(() => {
    const preventCopy = (e: Event) => e.preventDefault();
    const preventKeys = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && ["c", "a", "v", "x"].includes(e.key.toLowerCase())) {
        e.preventDefault();
      }
    };
    document.addEventListener("copy", preventCopy);
    document.addEventListener("cut", preventCopy);
    document.addEventListener("paste", preventCopy);
    document.addEventListener("keydown", preventKeys);
    document.addEventListener("contextmenu", preventCopy);
    document.addEventListener("dragstart", preventCopy);

    return () => {
      document.removeEventListener("copy", preventCopy);
      document.removeEventListener("cut", preventCopy);
      document.removeEventListener("paste", preventCopy);
      document.removeEventListener("keydown", preventKeys);
      document.removeEventListener("contextmenu", preventCopy);
      document.removeEventListener("dragstart", preventCopy);
    };
  }, []);

  return <div style={{ userSelect: "none", WebkitUserSelect: "none" }}>{children}</div>;
}
```

- [ ] **Step 2: Create session login page**

Build `frontend/src/app/(student)/session/[id]/page.tsx` with:
- Fetch session info via `api.getSession(id)`
- Login / Register toggle tabs
- On submit: call `api.login()` or `api.register()`, then `api.joinSession(id)`, then redirect to `/quiz/{quizId}`
- Show session title, question count, time limit

- [ ] **Step 3: Create quiz page**

Build `frontend/src/app/(student)/quiz/[id]/page.tsx` with:
- Fetch quiz meta via `api.getQuizMeta(id)`
- Fetch current question via `api.getQuestion(quizId, n)`
- Progress dots at top (blue=answered, yellow=current, gray=unanswered)
- Timer countdown (if time limit exists)
- Choice selection with highlighted state
- Previous / Next buttons
- "Submit Quiz" on last question
- Save answer on choice selection via `api.saveAnswer()`
- Wrap in `<AntiCopyPaste>`
- Auto-submit when timer reaches 0

- [ ] **Step 4: Create results page**

Build `frontend/src/app/(student)/results/[id]/page.tsx` with:
- Call `api.submitQuiz()` if not already submitted (or fetch existing results)
- Big score percentage
- Domain breakdown bar
- Per-question review: question text, choices (green for correct, red for student's wrong answer), explanation

- [ ] **Step 5: Create study pages**

Build `frontend/src/app/(student)/study/page.tsx`:
- Grid of domain cards with name and preview
- Click to go to `/study/{domainId}`

Build `frontend/src/app/(student)/study/[id]/page.tsx`:
- Render markdown cheatsheet content
- Use a simple markdown renderer (install `react-markdown`)

```bash
cd frontend && npm install react-markdown
```

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: add student pages — session login, quiz, results, study cards"
```

---

### Task 10: Instructor Dashboard

**Files:**
- Create: `frontend/src/app/(instructor)/layout.tsx`
- Create: `frontend/src/app/(instructor)/dashboard/page.tsx`
- Create: `frontend/src/app/(instructor)/sessions/new/page.tsx`
- Create: `frontend/src/app/(instructor)/sessions/[id]/page.tsx`
- Create: `frontend/src/app/(instructor)/results/[id]/page.tsx`
- Create: `frontend/src/app/(instructor)/questions/page.tsx`
- Create: `frontend/src/app/(instructor)/uploads/page.tsx`
- Create: `frontend/src/components/Sidebar.tsx`

- [ ] **Step 1: Create instructor layout with sidebar**

```typescript
// frontend/src/components/Sidebar.tsx
"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/dashboard", label: "Sessions", icon: "📋" },
  { href: "/uploads", label: "PDF Uploads", icon: "📄" },
  { href: "/questions", label: "Question Bank", icon: "❓" },
];

export default function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="w-52 border-r border-gray-800 p-4 min-h-screen">
      <div className="text-xs uppercase tracking-wider text-gray-500 mb-4">QuizForge</div>
      <nav className="flex flex-col gap-1">
        {links.map(l => (
          <Link key={l.href} href={l.href}
            className={`px-3 py-2 rounded text-sm ${
              pathname.startsWith(l.href) ? "bg-blue-500/10 text-blue-400" : "text-gray-400 hover:text-gray-200"
            }`}>
            {l.icon} {l.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
```

```typescript
// frontend/src/app/(instructor)/layout.tsx
"use client";
import { useAuth } from "@/lib/auth";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import Sidebar from "@/components/Sidebar";

export default function InstructorLayout({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && (!user || user.role !== "instructor")) {
      router.push("/");
    }
  }, [user, loading, router]);

  if (loading || !user) return <div className="p-8">Loading...</div>;

  return (
    <div className="flex min-h-screen bg-gray-950 text-gray-100">
      <Sidebar />
      <main className="flex-1 p-6">{children}</main>
    </div>
  );
}
```

- [ ] **Step 2: Create dashboard page (session list)**

Build `frontend/src/app/(instructor)/dashboard/page.tsx`:
- Fetch sessions via `api.getSessions()`
- Show session cards with title, subject, question count, status badge (Active/Closed)
- "+ New Session" button linking to `/sessions/new`
- Click session → `/sessions/{id}`

- [ ] **Step 3: Create new session page**

Build `frontend/src/app/(instructor)/sessions/new/page.tsx`:
- Subject dropdown (fetch from `api.getSubjects()`)
- Domain chip selector (fetch from `api.getDomains(subjectId)`) — shows question count per domain
- Title input, questions per student, time limit
- "Create Session" button → `api.createSession()` → redirect to `/sessions/{id}`

- [ ] **Step 4: Create session detail page (QR + attendance)**

Build `frontend/src/app/(instructor)/sessions/[id]/page.tsx`:
- Fetch session detail via `api.getSession(id)` — includes `qr_code` base64
- Display QR code image (large, projectible)
- Copy link button
- Toggle active/inactive button
- Live attendance grid (poll `api.getAttendance(id)` every 10s)
- "View Results" button when students have completed

- [ ] **Step 5: Create results dashboard**

Build `frontend/src/app/(instructor)/results/[id]/page.tsx`:
- Fetch results via `api.getResults(id)`
- Summary stats: avg score, completed count, avg time, hardest question
- Student table: name, score, time, weakest domain
- Sortable by score

- [ ] **Step 6: Create question bank page**

Build `frontend/src/app/(instructor)/questions/page.tsx`:
- Domain filter dropdown
- Paginated question list
- Each question: text preview, domain badge, source, edit/delete buttons
- Edit modal for inline editing

- [ ] **Step 7: Create PDF uploads page**

Build `frontend/src/app/(instructor)/uploads/page.tsx`:
- File upload zone (drag and drop or click)
- Upload list with status (pending → processing → done / error)
- Poll status every 5s while processing
- Reprocess button for errored uploads

- [ ] **Step 8: Create instructor login page**

Build `frontend/src/app/page.tsx` (root page):
- Simple login form for instructor
- On success, redirect to `/dashboard`

- [ ] **Step 9: Commit**

```bash
git add -A
git commit -m "feat: add instructor dashboard — sessions, QR codes, results, question bank, PDF uploads"
```

---

### Task 11: Final Integration & Docker

**Files:**
- Create: `frontend/Dockerfile`
- Modify: `docker-compose.yml` (add frontend service)

- [ ] **Step 1: Create frontend Dockerfile**

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
CMD ["npm", "start"]
```

- [ ] **Step 2: Update docker-compose.yml with frontend**

```yaml
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend
```

- [ ] **Step 3: Full integration test**

```bash
docker compose up --build
# Visit http://localhost:3000
# Login as instructor (instructor / quizforge-admin)
# Create a session
# Open QR URL in incognito, register as student, take quiz
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat: add Docker setup for full-stack deployment"
```

---

## Review Fixes — MUST APPLY during implementation

The following issues were found during plan review and MUST be addressed by the implementer:

### Critical Fixes

**[C1] Add time limit enforcement to `submit_quiz` endpoint (Task 6)**

In `backend/app/routers/quiz.py`, the `submit_quiz` endpoint must validate time limits:

```python
# Add after checking quiz.submitted_at in submit_quiz:
session_result = await db.execute(select(Session).where(Session.id == quiz.session_id))
session = session_result.scalar_one_or_none()
if session and session.time_limit_minutes:
    from datetime import timedelta
    deadline = quiz.started_at + timedelta(minutes=session.time_limit_minutes, seconds=30)  # 30s grace
    if datetime.now(timezone.utc) > deadline:
        # Still accept but flag
        pass  # Quiz is accepted; the submitted_at will show it was late
```

**[C2] Add pagination to ALL list endpoints (Tasks 5, 6)**

Every list endpoint must accept `page: int = Query(1, ge=1)` and `limit: int = Query(20, ge=1, le=100)` and apply `.offset((page-1)*limit).limit(limit)`. This applies to:
- `list_subjects`
- `list_domains`
- `list_sessions`
- `list_pdfs`
- `get_attendance`
- `get_results`

**[C3] Fix UUID string handling in `create_session` (Task 6)**

In `backend/app/routers/sessions.py`, `create_session` must convert domain_id strings to UUIDs:

```python
import uuid as uuid_module
# Change the query to:
domain_uuids = [uuid_module.UUID(d) for d in body.domain_ids]
result = await db.execute(
    select(Question).where(Question.domain_id.in_(domain_uuids))
)
```

**[C4] Fix UserResponse UUID serialization (Task 3)**

In `backend/app/schemas/auth.py`, change `UserResponse` to explicitly handle UUID:

```python
class UserResponse(BaseModel):
    id: str
    full_name: str
    username: str
    role: str

    @classmethod
    def from_user(cls, user):
        return cls(id=str(user.id), full_name=user.full_name, username=user.username, role=user.role)
```

Then use `UserResponse.from_user(user)` instead of `UserResponse.model_validate(user)` in the auth router.

### Important Fixes

**[I1] Add Subjects & Domains management pages to instructor dashboard (Task 10)**

Add to sidebar:
- `/subjects` — list, create, edit subjects
- `/domains` — list domains per subject, create, edit, delete, edit cheat sheet content

**[I2] Add cheatsheet update endpoint (Task 5)**

Add to `backend/app/routers/study.py`:

```python
from pydantic import BaseModel

class CheatsheetUpdate(BaseModel):
    content: str

@router.put("/domain/{domain_id}", response_model=StudyCardResponse)
async def update_cheatsheet(
    domain_id: str, body: CheatsheetUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_instructor),
):
    result = await db.execute(
        select(DomainCheatsheet).where(DomainCheatsheet.domain_id == domain_id)
    )
    cheatsheet = result.scalar_one_or_none()
    if cheatsheet:
        cheatsheet.content = body.content
    else:
        cheatsheet = DomainCheatsheet(domain_id=domain_id, content=body.content)
        db.add(cheatsheet)
    await db.commit()

    domain_result = await db.execute(select(Domain).where(Domain.id == domain_id))
    domain = domain_result.scalar_one()
    return StudyCardResponse(domain_id=str(domain.id), domain_name=domain.name, content=cheatsheet.content)
```

Import `require_instructor` from `app.services.auth` and `User` from `app.models.user`.

**[I3] Fix `uploadPdfs` error handling in API client (Task 8)**

```typescript
uploadPdfs: async (subjectId: string, files: FileList) => {
    const formData = new FormData();
    Array.from(files).forEach(f => formData.append("files", f));
    const res = await fetch(`${API_BASE}/api/subjects/${subjectId}/pdfs`, {
      method: "POST", credentials: "include", body: formData,
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(error.detail || "Upload failed");
    }
    return res.json();
  },
```

**[I4] Add "hardest question" metric to results endpoint (Task 6)**

In `get_results` in `sessions.py`, compute the question with the lowest correct rate from all student answers and include it in the response.

**[I5] Remove dead `select` from reprocess endpoint (Task 7)**

In `backend/app/routers/pdfs.py`, the `reprocess_pdf` endpoint has a useless select before the delete. Remove it:

```python
# Remove this line:
# await db.execute(select(Question).where(Question.source_pdf_id == pdf_id).execution_options(...))
# Keep only:
from sqlalchemy import delete
await db.execute(delete(Question).where(Question.source_pdf_id == pdf_id))
```

**[I6] Add `git init` before first commit (Task 1)**

Add to Task 1 Step 9:
```bash
cd /home/aiden/Aiden/quizforge
git init
git add -A
git commit -m "feat: scaffold backend with FastAPI, Docker, and PostgreSQL config"
```

**[I7] Add `.env` contents to Task 1**

The `.env` file already exists at `/home/aiden/Aiden/quizforge/.env` with the correct content. Task 1 should reference it rather than create it.

**[I8] Docker frontend NEXT_PUBLIC env var issue (Task 11)**

`NEXT_PUBLIC_*` vars are baked at build time. For Docker, either:
- Use a reverse proxy (nginx) that routes `/api` to the backend — frontend calls same origin
- Or use Next.js API route rewrites in `next.config.js`:

```javascript
// frontend/next.config.js
module.exports = {
  async rewrites() {
    return [{ source: "/api/:path*", destination: "http://backend:8000/api/:path*" }];
  },
};
```

Then the frontend API client uses relative paths (`/api/...`) instead of absolute URLs.

**[I9] Create `models/__init__.py` with all model imports (Task 2)**

```python
# backend/app/models/__init__.py
from app.models.user import User
from app.models.subject import Subject
from app.models.domain import Domain
from app.models.question import Question
from app.models.pdf_upload import PdfUpload
from app.models.session import Session, SessionQuestion
from app.models.student_quiz import StudentQuiz
from app.models.student_answer import StudentAnswer
from app.models.domain_cheatsheet import DomainCheatsheet

__all__ = [
    "User", "Subject", "Domain", "Question", "PdfUpload",
    "Session", "SessionQuestion", "StudentQuiz", "StudentAnswer",
    "DomainCheatsheet",
]
```

Then simplify `alembic/env.py` to: `from app.models import *`
