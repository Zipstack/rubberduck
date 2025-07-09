#!/usr/bin/env python3
"""Test if AWS credentials are available in the backend environment."""

import os
import boto3

# Check environment variables
print("Environment variables:")
print(f"  AWS_ACCESS_KEY_ID: {'set' if os.environ.get('AWS_ACCESS_KEY_ID') else 'not set'}")
print(f"  AWS_SECRET_ACCESS_KEY: {'set' if os.environ.get('AWS_SECRET_ACCESS_KEY') else 'not set'}")
print(f"  AWS_DEFAULT_REGION: {os.environ.get('AWS_DEFAULT_REGION', 'not set')}")

# Check boto3 session
session = boto3.Session()
credentials = session.get_credentials()

print("\nBoto3 credentials:")
if credentials:
    print(f"  Access key: {credentials.access_key[:5]}...")
    print(f"  Secret key: {'***' if credentials.secret_key else 'not set'}")
else:
    print("  No credentials found")

# Check credentials file
creds_file = os.path.expanduser("~/.aws/credentials")
print(f"\nAWS credentials file exists: {os.path.exists(creds_file)}")