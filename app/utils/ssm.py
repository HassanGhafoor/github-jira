# app/utils/ssm.py
import boto3
import os

# Default region fallback (so code doesn't raise NoRegionError)
_REGION = os.getenv("AWS_DEFAULT_REGION", os.getenv("AWS_REGION", "us-east-1"))

# Lazily create client so import-time won't fail catastrophically
def _ssm_client():
    return boto3.client("ssm", region_name=_REGION)

def get_param(name: str, decrypt: bool = True) -> str:
    """Fetch a parameter from AWS SSM Parameter Store (raises on AWS errors)."""
    client = _ssm_client()
    resp = client.get_parameter(Name=name, WithDecryption=decrypt)
    return resp["Parameter"]["Value"]

