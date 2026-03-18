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

from app.routers import auth, subjects, domains, questions, study, sessions, quiz, pdfs
app.include_router(auth.router)
app.include_router(subjects.router)
app.include_router(domains.router)
app.include_router(questions.router)
app.include_router(study.router)
app.include_router(sessions.router)
app.include_router(quiz.router)
app.include_router(pdfs.router)

@app.get("/api/health")
async def health():
    return {"status": "ok"}
