from __future__ import annotations

from skills.build_tableau import build_twbx_from_template


def build_twbx(csv_path: str, template_twb: str, output_dir: str) -> str:
    return build_twbx_from_template(csv_path, template_twb, output_dir)
