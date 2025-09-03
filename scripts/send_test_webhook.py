import os
import hmac
import hashlib
import json
import requests
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

# Get secret from .env
SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")

# Payload to send
payload = {
    "action": "opened",
    "pull_request": {"title": "Test PR"},
    "repository": {"full_name": "myuser/myrepo"}
}

# Convert payload to JSON bytes
data = json.dumps(payload).encode("utf-8")

# Compute signature
signature = "sha256=" + hmac.new(SECRET.encode(), data, hashlib.sha256).hexdigest()

# Send POST request
resp = requests.post(
    "http://127.0.0.1:5000/webhook",
    headers={
        "X-Hub-Signature-256": signature,
        "X-GitHub-Event": "pull_request",
        "Content-Type": "application/json"
    },
    data=data
)

print("Status:", resp.status_code)
print("Response:", resp.json())
