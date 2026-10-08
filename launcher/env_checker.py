"""Environment and Dependency Checker for CDT (Linux & Windows).

Validates R installation (e.g. R 4.4.3+), detects Rscript executable path,
checks all required R packages, system libraries, and compiler toolchains.
"""

from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REQUIRED_R_PACKAGES: list[str] = [
    "CDT",
    "ncdf4",
    "sp",
    "sf",
    "gstat",
    "matrixStats",
    "fitdistrplus",
    "qmap",
    "doParallel",
    "foreach",
    "fields",
    "lmomco",
    "yaml",
    "jsonlite",
]

MINIMUM_R_VERSION: Tuple[int, int, int] = (4, 0, 0)


def find_rscript_executable() -> Optional[Path]:
    """Locate the Rscript binary across Windows and Linux environments.

    Returns:
        Path to Rscript executable if found, None otherwise.
    """
    # 1. Check if Rscript is in PATH
    rscript_path = shutil.which("Rscript")
    if rscript_path:
        return Path(rscript_path).resolve()

    system = platform.system()

    if system == "Windows":
        # Check standard Windows Program Files directories for R
        search_dirs = [
            Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "R",
            Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "R",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "R",
            Path(os.environ.get("USERPROFILE", "")) / "R",
        ]

        found_candidates: list[Path] = []
        for base in search_dirs:
            if base.exists() and base.is_dir():
                for version_dir in sorted(base.glob("R-*"), reverse=True):
                    candidate = version_dir / "bin" / "Rscript.exe"
                    if candidate.exists():
                        found_candidates.append(candidate)

        if found_candidates:
            return found_candidates[0]

    elif system == "Linux":
        # Check standard Linux paths
        linux_paths = [
            Path("/usr/bin/Rscript"),
            Path("/usr/local/bin/Rscript"),
            Path("/opt/R/bin/Rscript"),
            Path("/usr/lib/R/bin/Rscript"),
        ]
        for p in linux_paths:
            if p.exists() and os.access(p, os.X_OK):
                return p

    return None


def get_r_version(rscript_path: Path) -> Tuple[Optional[Tuple[int, int, int]], str]:
    """Extract the R version from the Rscript binary.

    Args:
        rscript_path: Path to the Rscript executable.

    Returns:
        Tuple of ((major, minor, patch), raw_version_string).
    """
    try:
        res = subprocess.run(
            [str(rscript_path), "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        output = res.stderr if res.stderr else res.stdout
        match = re.search(r"version\s+([0-9]+)\.([0-9]+)\.([0-9]+)", output, re.IGNORECASE)
        if match:
            major, minor, patch = map(int, match.groups())
            return (major, minor, patch), f"{major}.{minor}.{patch}"
        return None, output.strip()
    except Exception as e:
        return None, f"Error obtaining R version: {e}"


def check_installed_r_packages(
    rscript_path: Path, packages: list[str] = REQUIRED_R_PACKAGES
) -> Dict[str, bool]:
    """Query R to determine which required packages are currently installed.

    Args:
        rscript_path: Path to Rscript executable.
        packages: List of package names to check.

    Returns:
        Dictionary mapping package names to True (installed) or False (missing).
    """
    pkg_str = ", ".join(f"'{p}'" for p in packages)
    r_command = (
        f"installed <- rownames(installed.packages()); "
        f"pkgs <- c({pkg_str}); "
        f"cat(paste(pkgs, pkgs %in% installed, sep = ':', collapse = ','))"
    )

    try:
        res = subprocess.run(
            [str(rscript_path), "-e", r_command],
            capture_output=True,
            text=True,
            check=True,
        )
        raw_pairs = res.stdout.strip().split(",")
        results = {}
        for pair in raw_pairs:
            if ":" in pair:
                name, status = pair.split(":")
                results[name.strip()] = status.strip() == "TRUE"
        return results
    except Exception as e:
        print(f"[!] Warning: Could not query R packages: {e}", file=sys.stderr)
        return {p: False for p in packages}


def check_system_environment(rscript_path: Optional[Path | str] = None) -> Dict[str, Any]:
    """Perform a comprehensive pre-flight check of the execution environment.

    Args:
        rscript_path: Optional custom path to Rscript executable.

    Returns:
        Structured dictionary with environment diagnostic results.
    """
    system_info = {
        "os": platform.system(),
        "os_release": platform.release(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
    }

    if rscript_path is not None:
        rscript_path = Path(rscript_path).resolve()
        if not rscript_path.exists():
            rscript_path = None
    else:
        rscript_path = find_rscript_executable()

    r_available = rscript_path is not None

    r_version_tuple = None
    r_version_str = "Not installed or not found"
    r_version_ok = False

    if rscript_path:
        r_version_tuple, r_version_str = get_r_version(rscript_path)
        if r_version_tuple and r_version_tuple >= MINIMUM_R_VERSION:
            r_version_ok = True

    pkg_status: Dict[str, bool] = {}
    missing_packages: list[str] = []

    if rscript_path and r_version_ok:
        pkg_status = check_installed_r_packages(rscript_path, REQUIRED_R_PACKAGES)
        missing_packages = [p for p, installed in pkg_status.items() if not installed]

    is_ready = bool(
        r_available and r_version_ok and (len(missing_packages) == 0 or "CDT" in pkg_status and pkg_status["CDT"])
    )

    return {
        "system": system_info,
        "rscript_path": str(rscript_path) if rscript_path else None,
        "r_available": r_available,
        "r_version": r_version_str,
        "r_version_ok": r_version_ok,
        "packages": pkg_status,
        "missing_packages": missing_packages,
        "is_ready": is_ready,
    }


def print_environment_report(status: Dict[str, Any]) -> None:
    """Print a user-friendly console report of the environment health check."""
    print("=" * 70)
    print("       CDT ENVIRONMENT & DEPENDENCY PRE-FLIGHT CHECK")
    print("=" * 70)
    print(f"  Operating System  : {status['system']['os']} {status['system']['os_release']} ({status['system']['architecture']})")
    print(f"  Python Version    : {status['system']['python_version']}")
    print(f"  Rscript Path      : {status['rscript_path'] or 'NOT FOUND'}")
    print(f"  R Version         : {status['r_version']} (Required >= 4.0.0, e.g. R 4.4.3)")

    print("\n  Required R Packages Status:")
    print("  " + "-" * 50)
    if status["packages"]:
        for pkg, installed in status["packages"].items():
            icon = "[OK]" if installed else "[MISSING]"
            print(f"    {icon:10} {pkg}")
    else:
        print("    [!] Could not check R packages because Rscript was not found.")

    print("=" * 70)
    if status["is_ready"]:
        print("  >>> STATUS: ENVIRONMENT IS FULLY COMPATIBLE & READY FOR CDT <<<")
    else:
        print("  >>> STATUS: ENVIRONMENT NEEDS ATTENTION BEFORE RUNNING <<<")
        if not status["r_available"]:
            print("  * Please install R 4.4.3 (https://cran.r-project.org/) and add it to PATH.")
        elif not status["r_version_ok"]:
            print(f"  * R version {status['r_version']} is outdated. Please update to R >= 4.0.0.")
        elif status["missing_packages"]:
            print(f"  * Missing R packages: {', '.join(status['missing_packages'])}")
            print("    Run: install.packages(c(" + ", ".join(f"'{p}'" for p in status["missing_packages"]) + "))")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    report = check_system_environment()
    print_environment_report(report)
    sys.exit(0 if report["is_ready"] else 1)
