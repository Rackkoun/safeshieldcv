# file safeshieldcv/backend/app/configs/config.py
# @author: Rackkoun
# v2 requires pydantic-settings package
# src: https://docs.pydantic.dev/latest/migration/#moved-in-pydantic-v2
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# load env
SSCV_ROOT = Path(__file__).resolve().parents[3]
CONFIG_DIR = SSCV_ROOT / "configs"
BACKEND_ENV_FILE = os.path.join(CONFIG_DIR, "backend_config.env")

if os.path.exists(BACKEND_ENV_FILE):
    load_dotenv(BACKEND_ENV_FILE)

class Settings(BaseSettings):
    # Database settings
    DB_USER: str = os.getenv("DB_USER")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT"))
    DB_NAME: str = os.getenv("DB_NAME")

    # Ollama settings
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL")

    # Email settings (for backend email sending)
    EMAIL_SENDER: str = os.getenv("EMAIL_SENDER", "")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")
    EMAIL_SMTP_SERVER: str = os.getenv("EMAIL_SMTP_SERVER")
    EMAIL_SMTP_PORT: int = int(os.getenv("EMAIL_SMTP_PORT"))

    # Evidence directory (where frontend saves images)
    EVIDENCE_BASE_DIR: Path = Path(os.getenv("EVIDENCE_BASE_DIR", 
        str(SSCV_ROOT.parent / "frontend" / "sscv-desktop-app")))
    
     # API settings
    SSCV_API_HOST: str = os.getenv("SSCV_API_HOST")
    SSCV_API_PORT: int = int(os.getenv("SSCV_API_PORT"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

settings = Settings()

if __name__ == "__main__":
    print(f"[SETTINGS] Root patht: {SSCV_ROOT}")
    print(f"[SETTINGS] pwd: {settings.DB_PASSWORD}")