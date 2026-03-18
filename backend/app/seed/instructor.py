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
