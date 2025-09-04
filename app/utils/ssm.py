# app/utils/ssm.py
import boto3
import os

_region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
_ssm = boto3.client("ssm", region_name=_region)

def get_param(name: str, decrypt: bool = True) -> str:
    """Fetch a parameter from AWS SSM Parameter Store."""
    resp = _ssm.get_parameter(Name=name, WithDecryption=decrypt)
    return resp["Parameter"]["Value"]

