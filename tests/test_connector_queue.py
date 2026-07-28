from fastapi.testclient import TestClient

from brain.api import app


def test_automate_intent_is_queued_for_connector() -> None:
    client = TestClient(app)
    res = client.post(
        "/v1/tasks",
        json={
            "intent": "automate notepad: type hello",
            "target_device": "windows-laptop",
            "dispatch": True,
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "queued"
    task_id = body["task_id"]

    claimed = client.get("/v1/devices/windows-laptop/tasks/next")
    assert claimed.status_code == 200
    task = claimed.json()["task"]
    assert task is not None
    assert task["id"] == task_id
    assert task["status"] == "running"

    reported = client.post(
        f"/v1/tasks/{task_id}/result",
        json={"status": "completed", "result": {"action": "ui_automation", "ok": True}},
    )
    assert reported.status_code == 200
    assert reported.json()["status"] == "completed"


def test_inline_execution_when_dispatch_false() -> None:
    client = TestClient(app)
    res = client.post(
        "/v1/tasks",
        json={"intent": "list .", "target_device": "windows-laptop", "dispatch": False},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "completed"
