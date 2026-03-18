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
