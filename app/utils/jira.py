# app/utils/jira.py
import base64
import json
import logging
import requests

from .. import config  # relative import of the config module

logger = logging.getLogger(__name__)

def _auth_header() -> dict:
    cfg = config.get_jira_config()
    email = cfg.get("email")
    token = cfg.get("api_token")
    if not (email and token):
        logger.error("Jira credentials missing (JIRA_EMAIL or JIRA_API_TOKEN).")
        raise RuntimeError("Jira credentials not set")
    token_bytes = f"{email}:{token}".encode("utf-8")
    return {"Authorization": "Basic " + base64.b64encode(token_bytes).decode("utf-8")}

def create_jira_ticket(summary: str, description: str) -> str:
    cfg = config.get_jira_config()
    base = cfg.get("base_url")
    project = cfg.get("project_key")
    if not base or not project:
        logger.error("Jira base URL or project key not set.")
        raise RuntimeError("Jira base URL or project key not set")

    url = f"{base.rstrip('/')}/rest/api/3/issue"
    payload = {
        "fields": {
            "project": {"key": project},
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
