import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

import secrets

# Prevent session forgery via default/weak secret keys
_raw_secret = os.environ.get("SECRET_KEY", "").strip()
_WEAK_SECRETS = {"", "change-me", "dev-secret-key-please-change-in-production", "secret", "flask", "admin"}
_ACTIVE_SECRET_KEY = secrets.token_hex(32) if _raw_secret in _WEAK_SECRETS else _raw_secret

class Config:
    """Base configuration loaded from environment variables."""
    SECRET_KEY = _ACTIVE_SECRET_KEY
    
    # Explicitly disable debug mode by default
    DEBUG = os.environ.get("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")
    TESTING = False

    # Database configuration
    DATABASE_PATH = os.environ.get(
        "DATABASE_PATH",
        str(PROJECT_ROOT / "data" / "analytics.db")
    )

    # Logging directory
    LOG_DIR = os.environ.get(
        "LOG_DIR",
        str(PROJECT_ROOT / "logs")
    )

    # CTF Flag variable (for later challenge phases - never exposed in current routes)
    CTF_FLAG = os.environ.get("CTF_FLAG", "CTF{development_flag_replace_me}")

    # Session cookie security settings
    SESSION_COOKIE_NAME = "analytics_session"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_SECURE", "0").lower() in ("1", "true", "yes")
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour in seconds


class TestConfig(Config):
    """Configuration for automated testing."""
    TESTING = True
    DEBUG = False
    SECRET_KEY = "test-secret-key"
    DATABASE_PATH = ":memory:"
