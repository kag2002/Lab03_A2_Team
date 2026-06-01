import os
from pathlib import Path
from dotenv import load_dotenv

# Load from .env file
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()  # Fallback to standard search

class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://token-plan-sgp.xiaomimimo.com/v1")
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "mimo-v2.5-pro")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()
