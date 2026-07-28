from __future__ import annotations

"""
Minimal MCP-style tool shim for Google Drive actions.
This script exposes python-callable functions for future MCP wiring.
"""

from skills.download_gdrive import download_file_by_name


def drive_download(filename: str, output_dir: str, credentials_file: str, token_file: str) -> str:
    return download_file_by_name(filename, output_dir, credentials_file, token_file)
