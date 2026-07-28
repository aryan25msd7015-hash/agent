from __future__ import annotations

import asyncio
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket
from pydantic import BaseModel

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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/tasks")
async def create_task(req: CreateTaskRequest) -> dict[str, Any]:
    task = store.create_task(req.intent, req.target_device, req.metadata)
    store.update_task(task.id, status="running")
    await _broadcast(task.id, {"event": "running", "task_id": task.id})
    result = orch.run(req.intent)
    task = store.update_task(task.id, status="completed", result=str(result))
    await _broadcast(task.id, {"event": "completed", "task_id": task.id, "result": result})
    return {"task_id": task.id, "status": task.status, "result": result}


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
