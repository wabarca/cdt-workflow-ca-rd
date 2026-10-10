"""Standardize Temperature YAML configurations to match CDT 8.0 signatures."""

import glob
import re
from pathlib import Path

def standardize_temp_yaml(file_path: Path):
    text = file_path.read_text(encoding="utf-8")

    # Standardize bias methods
    text = re.sub(r'method:\s*["\']multiplicative\.bias\.var["\']', 'method: "mbvar"', text)
    text = re.sub(r'method:\s*["\']admon["\']', 'method: "mbmon"', text)

    # Standardize merging methods
    text = re.sub(r'merging:\s*\n\s*method:\s*["\']sba["\']', 'merging:\n  method: "SBA"', text)
    text = re.sub(r'merging:\s*\n\s*method:\s*["\']regr\.kriging["\']', 'merging:\n  method: "RK"', text)
    text = re.sub(r'merging:\s*\n\s*method:\s*["\']barnes["\']', 'merging:\n  method: "SBA"\n  interpolation:\n    method: "barnes"', text)

    # In RK passes, replace interp_method: "regr.kriging" with interp_method: "okr"
    text = re.sub(r'interp_method:\s*["\']regr\.kriging["\']', 'interp_method: "okr"', text)

    file_path.write_text(text, encoding="utf-8")
    print(f"Updated: {file_path}")

for p in sorted(glob.glob("config/experiments_t*/*.yaml")):
    standardize_temp_yaml(Path(p))
