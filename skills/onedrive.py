from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx


def download_onedrive_file(filename: str, output_dir: str) -> dict[str, Any]:
    """
    Download a file from OneDrive via Microsoft Graph.
    Requires ONEDRIVE_ACCESS_TOKEN in env.
    """
    token = os.getenv("ONEDRIVE_ACCESS_TOKEN", "")
    if not token:
        return {"action": "onedrive_download", "status": "failed", "error": "ONEDRIVE_ACCESS_TOKEN missing"}
    headers = {"Authorization": f"Bearer {token}"}
    search_url = "https://graph.microsoft.com/v1.0/me/drive/root/search(q='{q}')"
    try:
        with httpx.Client(timeout=60) as client:
            res = client.get(search_url.format(q=filename), headers=headers)
            res.raise_for_status()
            values = res.json().get("value", [])
            if not values:
                return {"action": "onedrive_download", "status": "failed", "error": f"No file matching {filename}"}
            item = values[0]
            download_url = item.get("@microsoft.graph.downloadUrl")
            name = item.get("name", filename)
            if not download_url:
                item_id = item["id"]
                meta = client.get(f"https://graph.microsoft.com/v1.0/me/drive/items/{item_id}", headers=headers)
                meta.raise_for_status()
                download_url = meta.json().get("@microsoft.graph.downloadUrl")
            if not download_url:
                return {"action": "onedrive_download", "status": "failed", "error": "No download URL"}
            content = client.get(download_url)
            content.raise_for_status()
            out = Path(output_dir)
            out.mkdir(parents=True, exist_ok=True)
            path = out / name
            path.write_bytes(content.content)
            return {"action": "onedrive_download", "status": "executed", "path": str(path)}
    except Exception as exc:
        return {"action": "onedrive_download", "status": "failed", "error": str(exc)}
