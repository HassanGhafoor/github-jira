# app/config.py
from dotenv import load_dotenv
import os
from typing import Optional, Dict

# load local .env if present
load_dotenv()

def _get_param_from_ssm(name: str, decrypt: bool = False) -> Optional[str]:
    """
    Try to fetch from SSM. Import boto3/ssm helper lazily so imports don't fail
    if boto3/SSM isn't available or the instance role can't access SSM.
    """
    try:
        from .utils.ssm import get_param
        return get_param(name, decrypt=decrypt)
    except Exception:
        return None

def _get_param_with_fallback(name: str, decrypt: bool = False, default: Optional[str] = None) -> Optional[str]:
    val = _get_param_from_ssm(name, decrypt=decrypt)
    if val:
        return val
    return os.getenv(name, default)

# Jira config (module-level for convenience)
JIRA_BASE_URL = _get_param_with_fallback("JIRA_URL", decrypt=False, default=os.getenv("JIRA_BASE_URL", ""))
JIRA_EMAIL = _get_param_with_fallback("JIRA_EMAIL", decrypt=False, default=os.getenv("JIRA_EMAIL", ""))
JIRA_API_TOKEN = _get_param_with_fallback("JIRA_API_TOKEN", decrypt=True, default=os.getenv("JIRA_API_TOKEN", ""))
JIRA_PROJECT_KEY = _get_param_with_fallback("JIRA_PROJECT_KEY", decrypt=False, default=os.getenv("JIRA_PROJECT_KEY", ""))

def get_database_url() -> str:
    db = _get_param_with_fallback("DATABASE_URL", decrypt=False, default=os.getenv("DATABASE_URL"))
    if db:
        return db
    return "sqlite:///app/dev.sqlite"

def get_jira_config() -> Dict[str, str]:
    return {
        "base_url": JIRA_BASE_URL or "",
        "email": JIRA_EMAIL or "",
        "api_token": JIRA_API_TOKEN or "",
        "project_key": JIRA_PROJECT_KEY or ""
    }

class Config:
    SQLALCHEMY_DATABASE_URI = get_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Secret used to verify GitHub webhook; read from SSM or env
    GITHUB_WEBHOOK_SECRET = _get_param_with_fallback("GITHUB_WEBHOOK_SECRET", decrypt=False, default=os.getenv("GITHUB_WEBHOOK_SECRET", ""))
