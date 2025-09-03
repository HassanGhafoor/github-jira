# app/utils/jira.py
import base64
import json
import logging
import requests

from ..config import (
    JIRA_BASE_URL,
    JIRA_EMAIL,
    JIRA_API_TOKEN,
    JIRA_PROJECT_KEY,
)

logger = logging.getLogger(__name__)

def _auth_header() -> dict:
    """
    Returns HTTP Basic Auth header for Jira.
    Raises RuntimeError if credentials missing.
    """
    if not (JIRA_EMAIL and JIRA_API_TOKEN):
        logger.error("Jira credentials missing (JIRA_EMAIL or JIRA_API_TOKEN).")
        raise RuntimeError("Jira credentials not set")
    token = f"{JIRA_EMAIL}:{JIRA_API_TOKEN}".encode("utf-8")
    return {"Authorization": "Basic " + base64.b64encode(token).decode("utf-8")}

def create_jira_ticket(summary: str, description: str) -> str:
    """
    Create a Jira Task in the configured project.
    Returns the Jira issue key (e.g., ENG-123).
    """
    if not JIRA_BASE_URL or not JIRA_PROJECT_KEY:
        logger.error("Jira base URL or project key not set.")
        raise RuntimeError("Jira base URL or project key not set")

    url = f"{JIRA_BASE_URL.rstrip('/')}/rest/api/3/issue"
    payload = {
        "fields": {
            "project": {"key": JIRA_PROJECT_KEY},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description}]
                    }
                ]
            },
            "issuetype": {"name": "Task"}
        }
    }

    headers = {"Content-Type": "application/json", **_auth_header()}
    logger.debug("POST %s payload=%s", url, json.dumps(payload)[:1000])

    resp = requests.post(url, json=payload, headers=headers, timeout=20)

    if resp.status_code not in (200, 201):
        logger.error("Jira ticket creation failed: %s %s", resp.status_code, resp.text)
        raise RuntimeError(f"Jira API error {resp.status_code}: {resp.text}")

    key = resp.json().get("key")
    logger.info("Created Jira ticket: %s", key)
    return key

