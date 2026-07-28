from __future__ import annotations

from pathlib import Path
import shutil
import zipfile


def build_twbx_from_template(csv_path: str, template_twb: str, output_dir: str) -> str:
    """
    Lightweight placeholder packager:
    - Copies template .twb
    - Adds csv into a .twbx zip (Tableau package format)
    """
    csv = Path(csv_path)
    if not csv.exists():
        raise FileNotFoundError(csv_path)
    twb = Path(template_twb)
    if not twb.exists():
        raise FileNotFoundError(template_twb)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_twb = out_dir / f"{csv.stem}.twb"
    shutil.copy2(twb, out_twb)
    out_twbx = out_dir / f"{csv.stem}.twbx"
    with zipfile.ZipFile(out_twbx, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_twb, arcname=out_twb.name)
        zf.write(csv, arcname=f"Data/{csv.name}")
    return str(out_twbx)
