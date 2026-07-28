from __future__ import annotations

import os
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def _load_credentials(credentials_file: str, token_file: str) -> Credentials:
    if os.path.exists(token_file):
        return Credentials.from_authorized_user_file(token_file, SCOPES)
    flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
    creds = flow.run_local_server(port=0)
    Path(token_file).write_text(creds.to_json(), encoding="utf-8")
    return creds


def download_file_by_name(
    filename: str, output_dir: str, credentials_file: str, token_file: str
) -> str:
    creds = _load_credentials(credentials_file, token_file)
    service = build("drive", "v3", credentials=creds)
    q = f"name = '{filename}' and trashed = false"
    res = service.files().list(q=q, fields="files(id,name)", pageSize=1).execute()
    files = res.get("files", [])
    if not files:
        raise FileNotFoundError(f"Could not find {filename} in Google Drive")
    file_id = files[0]["id"]
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / filename
    request = service.files().get_media(fileId=file_id)
    with out_path.open("wb") as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
    return str(out_path)
