import hmac
import hashlib
from app.app import verify_signature

def test_verify_signature_valid():
    secret = "mysecret"
    body = b'{"hello":"world"}'
    mac = hmac.new(secret.encode(), msg=body, digestmod=hashlib.sha256).hexdigest()
    header = f"sha256={mac}"

    assert verify_signature(secret, body, header) is True


def test_verify_signature_invalid():
    secret = "mysecret"
    body = b'{"hello":"world"}'
    header = "sha256=wronghash"

    assert verify_signature(secret, body, header) is False
