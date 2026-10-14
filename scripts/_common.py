"""Shared settings for the helper scripts."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ACCOUNT = os.environ.get("SNOWFLAKE_ACCOUNT", "<your-account>")  # e.g. orgname-accountname
KEY_PATH = Path(os.environ.get("SNOWFLAKE_KEY_PATH", ROOT / "keys" / "rsa_key.p8"))
USER = os.environ.get("SNOWFLAKE_USER", "KAFKA_CONNECTOR_USER")
ROLE = os.environ.get("SNOWFLAKE_ROLE", "KAFKA_CONNECTOR_ROLE")


def der_private_key():
    from cryptography.hazmat.primitives import serialization
    key = serialization.load_pem_private_key(KEY_PATH.read_bytes(), password=None)
    return key.private_bytes(serialization.Encoding.DER, serialization.PrivateFormat.PKCS8,
                             serialization.NoEncryption())
