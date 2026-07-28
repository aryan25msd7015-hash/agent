from fastapi.testclient import TestClient

from brain.api import app


def test_create_task_completes() -> None:
    client = TestClient(app)
    res = client.post("/v1/tasks", json={"intent": "list .", "target_device": "windows-laptop"})
    assert res.status_code == 200
    payload = res.json()
    assert payload["status"] == "completed"
    assert "task_id" in payload
