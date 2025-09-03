import os
import json
import hmac
import hashlib
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from .utils.jira import create_jira_ticket, build_summary
from .db import init_db, log_ticket_creation

# Load environment variables
load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Secret from environment
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")

# Initialize database 
from .config import get_database_url

DATABASE_URL = os.getenv("DATABASE_URL") or get_database_url()
engine, SessionLocal = init_db(DATABASE_URL)


def verify_signature(secret: str, body: bytes, signature_header: str) -> bool:
    """
    Verify GitHub webhook signature (X-Hub-Signature-256).
    """
    if not secret or not signature_header or not signature_header.startswith("sha256="):
        return False

    received_sig = signature_header.split("=", 1)[1].strip()
    mac = hmac.new(secret.encode("utf-8"), msg=body, digestmod=hashlib.sha256)
    expected = mac.hexdigest()
    return hmac.compare_digest(received_sig, expected)


@app.route("/", methods=["GET"])
def health():
    """Simple health check endpoint."""
    return jsonify({"status": "ok"}), 200


@app.route("/webhook", methods=["POST"])
def webhook():
    """Receive GitHub webhook, create Jira ticket, and log event."""
    body = request.get_data()
    sig_header = request.headers.get("X-Hub-Signature-256", "")
    event = request.headers.get("X-GitHub-Event", "unknown")

    # Verify signature
    if not verify_signature(GITHUB_WEBHOOK_SECRET, body, sig_header):
        logger.warning("Invalid signature for event %s", event)
        return jsonify({"error": "invalid signature"}), 401

    try:
        payload = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "invalid JSON"}), 400

    logger.info("Received GitHub event: %s", event)

    # Process only certain events
    if event in ("issues", "pull_request"):
        summary = build_summary(event, payload)
        description = json.dumps(payload, indent=2)[:6000]

        try:
            issue_key = create_jira_ticket(summary, description)
            logger.info("Created Jira ticket: %s", issue_key)

            # Log to DB
            with SessionLocal() as session:
                delivery_id = request.headers.get("X-GitHub-Delivery", "n/a")
                log_ticket_creation(
                    session,
                    source_event=event,
                    delivery_id=delivery_id,
                    ticket_key=issue_key
                )

            return jsonify({"ok": True, "jira_ticket": issue_key}), 200

        except Exception as e:
            logger.exception("Failed to create Jira ticket")
            return jsonify({"error": "jira_failed"}), 500

    return jsonify({"ok": True, "ignored_event": event}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
import os
import json
import hmac
import hashlib
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from .utils.jira import create_jira_ticket, build_summary
from .db import init_db, log_ticket_creation

# Load environment variables from .env (local dev; in AWS use SSM)
load_dotenv()

app = Flask(__name__)

# ===========================
# Logging Setup
# ===========================
log_dir = "/var/log/github-jira"
os.makedirs(log_dir, exist_ok=True)

# Console logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File logging (for CloudWatch Agent)
file_handler = RotatingFileHandler(
    os.path.join(log_dir, "app.log"),
    maxBytes=5_000_000,  # 5 MB
    backupCount=3
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s %(levelname)s %(name)s: %(message)s"
))
logger.addHandler(file_handler)
app.logger.addHandler(file_handler)
logging.getLogger().addHandler(file_handler)  # root logger too

# ===========================
# Config & DB
# ===========================
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")
engine, SessionLocal = init_db(os.getenv("DATABASE_URL"))


# ===========================
# Helper Functions
# ===========================
def verify_signature(secret: str, body: bytes, signature_header: str) -> bool:
    """
    Verify GitHub webhook signature (X-Hub-Signature-256).
    """
    if not secret or not signature_header or not signature_header.startswith("sha256="):
        return False

    received_sig = signature_header.split("=", 1)[1].strip()
    mac = hmac.new(secret.encode("utf-8"), msg=body, digestmod=hashlib.sha256)
    expected = mac.hexdigest()
    return hmac.compare_digest(received_sig, expected)


# ===========================
# Routes
# ===========================
@app.route("/", methods=["GET"])
def health():
    """Simple health check endpoint."""
    return jsonify({"status": "ok"}), 200


@app.route("/webhook", methods=["POST"])
def webhook():
    """Receive GitHub webhook, create Jira ticket, and log event."""
    body = request.get_data()
    sig_header = request.headers.get("X-Hub-Signature-256", "")
    event = request.headers.get("X-GitHub-Event", "unknown")

    # Verify signature
    if not verify_signature(GITHUB_WEBHOOK_SECRET, body, sig_header):
        logger.warning("Invalid signature for event %s", event)
        return jsonify({"error": "invalid signature"}), 401

    try:
        payload = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "invalid JSON"}), 400

    logger.info("Received GitHub event: %s", event)

    # Only process certain events
    if event in ("issues", "pull_request"):
        summary = build_summary(event, payload)
        description = json.dumps(payload, indent=2)[:6000]

        try:
            issue_key = create_jira_ticket(summary, description)
            logger.info("Created Jira ticket: %s", issue_key)

            # Log to DB
            with SessionLocal() as session:
                delivery_id = request.headers.get("X-GitHub-Delivery", "n/a")
                log_ticket_creation(
                    session,
                    source_event=event,
                    delivery_id=delivery_id,
                    ticket_key=issue_key
                )

            return jsonify({"ok": True, "jira_ticket": issue_key}), 200

        except Exception:
            logger.exception("Failed to create Jira ticket")
            return jsonify({"error": "jira_failed"}), 500

    return jsonify({"ok": True, "ignored_event": event}), 200


# ===========================
# Entry Point
# ===========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
