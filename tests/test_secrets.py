import os

from config.secrets import SecretManager


def test_secret_manager_env_fallback() -> None:
    os.environ["TEST_SECRET_ENV"] = "abc123"
    sm = SecretManager("test-service")
    assert sm.get("missing-key", env_fallback="TEST_SECRET_ENV") == "abc123"
