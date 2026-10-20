import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "EduGenie AI"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./edugenie.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "949f2b347209ae84d2938e21a293b4aef9e2819cd30ef30aee4919cbcd3f39a0")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2")
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "ollama")

settings = Settings()
