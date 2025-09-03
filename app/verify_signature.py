import hmac
import hashlib

def verify_signature(secret: str, payload: bytes, signature_header: str) -> bool:
    """
    Verify the GitHub webhook signature.

    secret: Webhook secret as a string
    payload: Raw request body (bytes)
    signature_header: The value of 'X-Hub-Signature-256' header from GitHub
    """
    if not secret or not signature_header:
        return False

    # Expected signature
    mac = hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256)
    expected_signature = f"sha256={mac.hexdigest()}"

    # Constant-time comparison
    return hmac.compare_digest(expected_signature, signature_header)
