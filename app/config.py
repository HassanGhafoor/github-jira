# app/config.py
from dotenv import load_dotenv
import os

# load local .env if present (dev convenience)
load_dotenv()

# Import SSM helper (SSM function covers EC2/SSM usage)
from .utils.ssm import get_param

def _get_param_with_fallback(name: str, decrypt: bool = False, default: str | None = None) -> str | None:
    """
    Try SSM first (if available/accessible). If that fails, fall back to env var.
    This makes the app safe both for EC2+SSM and local dev (.env).
    """
    try:
        val = get_param(name, decrypt=decrypt)
        if val:
            return val
    except Exception:
        # likely no permission or not in SSM — fall back to env
        pass
    return os.getenv(name, default)

JIRA_BASE_URL = _get_param_with_fallback("JIRA_URL", decrypt=False, default=os.getenv("JIRA_BASE_URL", ""))
JIRA_EMAIL = _get_param_with_fallback("JIRA_EMAIL", decrypt=False, default=os.getenv("JIRA_EMAIL", ""))
JIRA_API_TOKEN = _get_param_with_fallback("JIRA_API_TOKEN", decrypt=True, default=os.getenv("JIRA_API_TOKEN", ""))
JIRA_PROJECT_KEY = _get_param_with_fallback("JIRA_PROJECT_KEY", decrypt=False, default=os.getenv("JIRA_PROJECT_KEY", ""))

def get_database_url() -> str:
    """Return the DATABASE_URL (RDS) or fallback to SQLite dev path."""
    db = _get_param_with_fallback("DATABASE_URL", decrypt=False, default=os.getenv("DATABASE_URL"))
    if db:
        return db
    # default local sqlite for dev
    return "sqlite:///app/dev.sqlite"

