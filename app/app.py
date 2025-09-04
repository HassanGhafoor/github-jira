# app/app.py
import os
import json
import hmac
import hashlib
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load .env if present (dev)
load_dotenv()

# local imports
from .config import Config
from .extensions import db, migrate
from .utils.jira import create_jira_ticket

# Create app and init extensions
app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate.init_app(app, db)

# Register models (so SQLAlchemy knows about them)
with app.app_context():
    from . import models  # noqa: F401

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Secret
GITHUB_WEBHOOK_SECRET = app.config.get("GITHUB_WEBHOOK_SECRET", "")

def verify_signature(secret: str, body: bytes, signature_header: str) -> bool:
    if not secret or not signature_header or not signature_header.startswith("sha256="):
        return False
    received_sig = signature_header.split("=", 1)[1].strip()
    mac = hmac.new(secret.encode("utf-8"), msg=body, digestmod=hashlib.sha256)
    expected = mac.hexdigest()
    return hmac.compare_digest(received_sig, expected)

def build_summary(event: str, payload: dict) -> str:
    if event == "issues":
        action = payload.get("action", "unknown")
        title = (payload.get("issue") or {}).get("title", "No title")
        repo = (payload.get("repository") or {}).get("full_name", "unknown/repo")
        return f"[GitHub] Issue {action}: {title} ({repo})"
    if event == "pull_request":
        action = payload.get("action", "unknown")
        title = (payload.get("pull_request") or {}).get("title", "No title")
        repo = (payload.get("repository") or {}).get("full_name", "unknown/repo")
        return f"[GitHub] PR {action}: {title} ({repo})"
    return f"[GitHub] Event: {event}"

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.get_data()
    sig_header = request.headers.get("X-Hub-Signature-256", "")
    event = request.headers.get("X-GitHub-Event", "unknown")

    if not verify_signature(GITHUB_WEBHOOK_SECRET, body, sig_header):
        logger.warning("Invalid signature for event %s", event)
        return jsonify({"error": "invalid signature"}), 401

    try:
        payload = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "invalid JSON"}), 400

    logger.info("Received GitHub event: %s", event)

    if event in ("issues", "pull_request"):
        summary = build_summary(event, payload)
        description = json.dumps(payload, indent=2)[:6000]

        try:
            issue_key = create_jira_ticket(summary, description)
            logger.info("Created Jira ticket: %s", issue_key)

            from .models import WebhookLog
            entry = WebhookLog(
                source_event=event,
                delivery_id=request.headers.get("X-GitHub-Delivery", "n/a"),
                ticket_key=issue_key,
                payload=description
            )
            db.session.add(entry)
            db.session.commit()

            return jsonify({"ok": True, "jira_ticket": issue_key}), 200

        except Exception as e:
            logger.exception("Failed to create Jira ticket")
            return jsonify({"error": "jira_failed", "details": str(e)}), 500

    return jsonify({"ok": True, "ignored_event": event}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
