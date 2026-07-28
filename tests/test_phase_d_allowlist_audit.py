from config.allowlist import is_path_allowed
from brain.audit import AuditLog
from fastapi.testclient import TestClient

from brain.api import app


def test_allowlist_blocks_outside_roots() -> None:
    assert is_path_allowed(".") is True
    assert is_path_allowed("data/inbox") is True
    assert is_path_allowed("/etc/passwd") is False


def test_audit_and_history_endpoint(tmp_path) -> None:
    log = AuditLog(str(tmp_path / "audit.jsonl"))
    log.write("intent", {"intent": "list ."})
    assert len(log.tail(5)) == 1
    client = TestClient(app)
    res = client.get("/v1/history?limit=5")
    assert res.status_code == 200
    assert "events" in res.json()
