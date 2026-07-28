from fastapi.testclient import TestClient

from brain.api import app


def test_risky_task_requires_approval() -> None:
    client = TestClient(app)
    res = client.post("/v1/tasks", json={"intent": "delete C:\\temp\\x.txt", "target_device": "windows-laptop"})
    assert res.status_code == 200
    payload = res.json()
    assert payload["status"] == "pending_approval"
    task_id = payload["task_id"]

    deny = client.post(f"/v1/tasks/{task_id}/approve", json={"approved": False})
    assert deny.status_code == 200
    assert deny.json()["status"] == "cancelled"
