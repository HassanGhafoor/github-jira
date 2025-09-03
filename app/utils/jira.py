import os
import json
import logging
import requests

# Load environment variables
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "").rstrip("/")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "")

logger = logging.getLogger(__name__)

def build_summary(event: str, payload: dict) -> str:
    """
    Build a Jira summary based on GitHub event type.
    """
    repo = payload.get("repository", {}).get("full_name", "unknown/repo")

    if event == "pull_request":
        title = payload.get("pull_request", {}).get("title", "No title")
        return f"[GitHub] PR opened: {title} ({repo})"

    elif event == "issues":
        title = payload.get("issue", {}).get("title", "No title")
        return f"[GitHub] Issue opened: {title} ({repo})"

    # Default for unsupported events
    return f"[GitHub] Event: {event} ({repo})"


def create_jira_ticket(summary: str, description: str) -> str:
    """
    Create a Jira issue and return its key.
    """
    if not JIRA_BASE_URL or not JIRA_EMAIL or not JIRA_API_TOKEN or not JIRA_PROJECT_KEY:
        logger.error("Jira configuration is missing.")
        raise ValueError("Jira configuration missing in environment variables")

    url = f"{JIRA_BASE_URL}/rest/api/3/issue"
    headers = {"Content-Type": "application/json"}
    auth = (JIRA_EMAIL, JIRA_API_TOKEN)

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
                        "content": [
                            {"type": "text", "text": description}
                        ]
                    }
                ]
            },
            "issuetype": {"name": "Task"},
        }
    }

    logger.debug(f"Creating Jira ticket with payload: {json.dumps(payload, indent=2)[:1000]}")

    response = requests.post(url, headers=headers, auth=auth, json=payload)

    if response.status_code != 201:
        logger.error(f"Jira API error {response.status_code}: {response.text}")
        raise RuntimeError(f"Jira API error {response.status_code}: {response.text}")

    issue_key = response.json().get("key")
    logger.info(f"Jira ticket created: {issue_key}")
    return issue_key
