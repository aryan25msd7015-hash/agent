from __future__ import annotations

import asyncio
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket
from pydantic import BaseModel

from brain.approval import requires_approval
from brain.audit import audit_log
from brain.orchestrator import Orchestrator
from brain.store import TaskStore
from config.settings import settings

app = FastAPI(title="Personal Agent Gateway")
store = TaskStore(settings.db_path)
orch = Orchestrator()
_streams: dict[str, list[WebSocket]] = {}


class CreateTaskRequest(BaseModel):
    intent: str
    target_device: str = "windows-laptop"
    metadata: dict[str, Any] | None = None
    # When True (default), queue for connector execution instead of inline.
    dispatch: bool = True


class ApprovalRequest(BaseModel):
    approved: bool


class TaskResultRequest(BaseModel):
    status: str = "completed"
    result: Any = None


def _should_dispatch(intent: str, dispatch_flag: bool) -> bool:
    if not dispatch_flag:
        return False
    lower = intent.lower().strip()
    # Keep approval gate before any execution path.
    if requires_approval(intent):
        return False
    # Device-local UI / browser work should run on connector.
    if lower.startswith("automate ") or lower.startswith("browse "):
        return True
    # Explicit NL desktop phrases also go to connector after planning.
    desktop_hints = ("open ", "type in ", "click ", "press ", "launch ")
    return any(h in lower for h in desktop_hints) and not any(
        x in lower for x in ("gdrive", "google drive", "tableau", "list ")
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/tasks")
async def create_task(req: CreateTaskRequest) -> dict[str, Any]:
    task = store.create_task(req.intent, req.target_device, req.metadata)
    if requires_approval(req.intent) and not (req.metadata or {}).get("approved", False):
        task = store.update_task(task.id, status="pending_approval")
        await _broadcast(task.id, {"event": "pending_approval", "task_id": task.id, "intent": req.intent})
        return {"task_id": task.id, "status": task.status, "result": "Approval required", "intent": req.intent}

    if _should_dispatch(req.intent, req.dispatch):
        task = store.update_task(task.id, status="queued")
        await _broadcast(task.id, {"event": "queued", "task_id": task.id})
        return {"task_id": task.id, "status": task.status, "result": "Queued for connector"}

    store.update_task(task.id, status="running")
    await _broadcast(task.id, {"event": "running", "task_id": task.id})
    result = orch.run(req.intent)
    task = store.update_task(task.id, status="completed", result=str(result))
    await _broadcast(task.id, {"event": "completed", "task_id": task.id, "result": result})
    return {"task_id": task.id, "status": task.status, "result": result}


@app.post("/v1/tasks/{task_id}/approve")
async def approve_task(task_id: str, req: ApprovalRequest) -> dict[str, Any]:
    try:
        task = store.get_task(task_id)
    except KeyError as exc:
        raise HTTPException(404, "task not found") from exc
    if task.status != "pending_approval":
        raise HTTPException(400, "task is not pending approval")
    if not req.approved:
        task = store.update_task(task.id, status="cancelled", result="Denied by user")
        await _broadcast(task.id, {"event": "cancelled", "task_id": task.id})
        return {"task_id": task.id, "status": task.status, "result": task.result}
    store.update_metadata(task.id, {"approved": True})
    # After approval, queue for connector if UI/desktop intent; else run inline.
    if _should_dispatch(task.intent, True):
        task = store.update_task(task.id, status="queued")
        await _broadcast(task.id, {"event": "queued", "task_id": task.id})
        return {"task_id": task.id, "status": task.status, "result": "Approved and queued"}
    store.update_task(task.id, status="running")
    await _broadcast(task.id, {"event": "running", "task_id": task.id})
    result = orch.run(task.intent)
    task = store.update_task(task.id, status="completed", result=str(result))
    await _broadcast(task.id, {"event": "completed", "task_id": task.id, "result": result})
    return {"task_id": task.id, "status": task.status, "result": result}


@app.get("/v1/devices/{device_id}/tasks/next")
def claim_next_task(device_id: str) -> dict[str, Any]:
    task = store.claim_next(device_id)
    if task is None:
        return {"task": None}
    return {"task": task.__dict__}


@app.post("/v1/tasks/{task_id}/result")
async def report_task_result(task_id: str, req: TaskResultRequest) -> dict[str, Any]:
    try:
        store.get_task(task_id)
    except KeyError as exc:
        raise HTTPException(404, "task not found") from exc
    status = req.status if req.status in {"completed", "failed"} else "completed"
    task = store.update_task(task_id, status=status, result=str(req.result))
    await _broadcast(task.id, {"event": status, "task_id": task.id, "result": req.result})
    return {"task_id": task.id, "status": task.status, "result": task.result}


@app.get("/v1/history")
def history(limit: int = 20) -> dict[str, Any]:
    return {"events": audit_log.tail(limit=limit)}


@app.get("/v1/tasks/{task_id}")
def get_task(task_id: str) -> dict[str, Any]:
    try:
        task = store.get_task(task_id)
    except KeyError as exc:
        raise HTTPException(404, "task not found") from exc
    return task.__dict__


@app.websocket("/v1/tasks/{task_id}/stream")
async def stream_task(task_id: str, ws: WebSocket) -> None:
    await ws.accept()
    _streams.setdefault(task_id, []).append(ws)
    try:
        while True:
            await ws.receive_text()
    except Exception:
        pass
    finally:
        _streams[task_id].remove(ws)


async def _broadcast(task_id: str, payload: dict[str, Any]) -> None:
    sockets = _streams.get(task_id, [])
    if not sockets:
        return
    for ws in list(sockets):
        try:
            await ws.send_json(payload)
        except Exception:
            await asyncio.sleep(0)
