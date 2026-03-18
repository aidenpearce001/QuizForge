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
