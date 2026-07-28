from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx


def download_dropbox_file(filename: str, output_dir: str) -> dict[str, Any]:
    """
    Download a Dropbox file by name using Dropbox API search + download.
    Requires DROPBOX_ACCESS_TOKEN.
    """
    token = os.getenv("DROPBOX_ACCESS_TOKEN", "")
    if not token:
        return {"action": "dropbox_download", "status": "failed", "error": "DROPBOX_ACCESS_TOKEN missing"}
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        with httpx.Client(timeout=60) as client:
            search = client.post(
                "https://api.dropboxapi.com/2/files/search_v2",
                headers=headers,
                json={"query": filename, "options": {"max_results": 5}},
            )
            search.raise_for_status()
            matches = search.json().get("matches", [])
            if not matches:
                return {"action": "dropbox_download", "status": "failed", "error": f"No file matching {filename}"}
            meta = matches[0]["metadata"]["metadata"]
            path_display = meta.get("path_display") or meta.get("path_lower")
            name = meta.get("name", filename)
            dl = client.post(
                "https://content.dropboxapi.com/2/files/download",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Dropbox-API-Arg": f'{{"path":"{path_display}"}}',
                },
            )
            dl.raise_for_status()
            out = Path(output_dir)
            out.mkdir(parents=True, exist_ok=True)
            dest = out / name
            dest.write_bytes(dl.content)
            return {"action": "dropbox_download", "status": "executed", "path": str(dest)}
    except Exception as exc:
        return {"action": "dropbox_download", "status": "failed", "error": str(exc)}
