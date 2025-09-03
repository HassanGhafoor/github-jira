# app/config.py
import os
import logging
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

def _ssm_client():
    # boto3 will also fall back to instance metadata if region not provided
    region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
    if region:
        return boto3.client("ssm", region_name=region)
    return boto3.client("ssm")

def get_ssm_param(name: str, with_decryption: bool = True) -> str | None:
    """
    Try env var first, then SSM Parameter Store. Returns None if not found.
    """
    # 1) environment (useful for local dev/.env or systemd exports)
    v = os.getenv(name)
    if v:
        return v

    # 2) SSM
    try:
        client = _ssm_client()
        resp = client.get_parameter(Name=name, WithDecryption=with_decryption)
        return resp["Parameter"]["Value"]
    except ClientError as e:
        logger.debug("SSM get_parameter failed for %s: %s", name, e)
        return None
    except Exception as e:
        logger.exception("Unexpected SSM error for %s: %s", name, e)
        return None

# --- Application configuration values (fallback to env when present) ---
GITHUB_WEBHOOK_SECRET = get_ssm_param("GITHUB_WEBHOOK_SECRET")
DATABASE_URL          = get_ssm_param("DATABASE_URL") or os.getenv("DATABASE_URL")

JIRA_BASE_URL         = get_ssm_param("JIRA_BASE_URL")
JIRA_EMAIL            = get_ssm_param("JIRA_EMAIL")
JIRA_API_TOKEN        = get_ssm_param("JIRA_API_TOKEN")
JIRA_PROJECT_KEY      = get_ssm_param("JIRA_PROJECT_KEY")

