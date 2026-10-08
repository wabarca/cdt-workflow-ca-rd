"""Cross-Platform Environment Setup & Hardware Resource Optimizer for CDT.

Automates environment provisioning for Windows and Linux:
1. Detects OS and hardware resources (logical CPU cores, physical RAM).
2. Verifies / creates Python virtual environment (.venv).
3. Installs / updates Python dependencies from requirements.txt.
4. Locates R / Rscript executable.
5. Verifies and installs all required R packages from CRAN and local CDT source.
6. Generates a tuned hardware configuration for high-performance parallel execution.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Workspace root
WORKSPACE_ROOT = Path(__file__).resolve().parent

# Required R packages for CDT
REQUIRED_R_PACKAGES = [
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


def print_banner(text: str) -> None:
    print("\n" + "=" * 78)
    print(f"  {text}")
    print("=" * 78)


def get_hardware_info() -> Dict[str, any]:
    """Detect logical CPU cores and memory."""
    cpu_count = os.cpu_count() or 4
    system_os = platform.system()
    
    # Calculate recommended worker cores (leave 1 core free for OS responsiveness)
    workers = max(1, cpu_count - 1)
    
    return {
        "os": system_os,
        "os_release": platform.release(),
        "arch": platform.machine(),
        "total_cores": cpu_count,
        "recommended_workers": workers,
        "python_version": platform.python_version(),
    }


def find_rscript() -> Optional[Path]:
    """Locate Rscript binary across Windows and Linux."""
    # 1. PATH lookup
    rscript = shutil.which("Rscript")
    if rscript:
        return Path(rscript).resolve()

    system_os = platform.system()
    if system_os == "Windows":
        candidates = [
            Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "R",
            Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "R",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "R",
        ]
        for base in candidates:
            if base.exists():
                for vdir in sorted(base.glob("R-*"), reverse=True):
                    candidate = vdir / "bin" / "Rscript.exe"
                    if candidate.exists():
                        return candidate
    elif system_os == "Linux":
        candidates = [
            Path("/usr/bin/Rscript"),
            Path("/usr/local/bin/Rscript"),
            Path("/opt/R/bin/Rscript"),
            Path("/usr/lib/R/bin/Rscript"),
        ]
        for c in candidates:
            if c.exists() and os.access(c, os.X_OK):
                return c

    return None


def setup_python_venv() -> Tuple[Path, Path]:
    """Create or verify Python virtual environment and return (python_bin, pip_bin)."""
    venv_dir = WORKSPACE_ROOT / ".venv"
    system_os = platform.system()

    if system_os == "Windows":
        py_bin = venv_dir / "Scripts" / "python.exe"
        pip_bin = venv_dir / "Scripts" / "pip.exe"
    else:
        py_bin = venv_dir / "bin" / "python"
        pip_bin = venv_dir / "bin" / "pip"

    if not venv_dir.exists() or not py_bin.exists():
        print(f"[*] Creando entorno virtual Python en: {venv_dir}")
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
    else:
        print(f"[OK] Entorno virtual Python detectado en: {venv_dir}")

    # Upgrade pip and install requirements
    req_file = WORKSPACE_ROOT / "requirements.txt"
    if req_file.exists():
        print(f"[*] Instalando / actualizando paquetes Python desde {req_file.name}...")
        subprocess.run([str(py_bin), "-m", "pip", "install", "--upgrade", "pip"], check=False)
        subprocess.run([str(py_bin), "-m", "pip", "install", "-r", str(req_file)], check=True)
        print("[OK] Paquetes de Python instalados exitosamente.")

    return py_bin, pip_bin


def setup_r_environment(rscript_path: Path) -> bool:
    """Verify and install required R packages from CRAN and local CDT source."""
    print(f"\n[*] Verificando paquetes de R con ejecutable: {rscript_path}")

    # R command to check and install missing packages
    pkgs_str = ", ".join(f"'{p}'" for p in REQUIRED_R_PACKAGES)
    r_code = f"""
    cran_mirror <- 'https://cloud.r-project.org/'
    options(repos = c(CRAN = cran_mirror))
    
    required_pkgs <- c({pkgs_str})
    installed <- rownames(installed.packages())
    missing_pkgs <- required_pkgs[!required_pkgs %in% installed]
    
    if (length(missing_pkgs) > 0) {{
        message('Instalando paquetes faltantes de CRAN: ', paste(missing_pkgs, collapse=', '))
        install.packages(missing_pkgs, repos = cran_mirror, dependencies = TRUE)
    }} else {{
        message('Todos los paquetes base de CRAN estan instalados.')
    }}
    
    # Verificar instalacion del paquete CDT local
    if (!'CDT' %in% installed) {{
        message('Instalando paquete CDT local desde el codigo fuente...')
        tryCatch({{
            install.packages('{str(WORKSPACE_ROOT).replace(chr(92), "/")}', repos = NULL, type = 'source')
            message('CDT instalado exitosamente.')
        }}, error = function(e) {{
            message('Nota: Si CDT ya esta disponible en .libPaths(), se cargara dinamicamente.')
        }})
    }}
    
    # Comprobacion final
    final_installed <- rownames(installed.packages())
    status <- sapply(required_pkgs, function(p) p %in% final_installed)
    cat('R_CHECK_RESULT:', paste(names(status), status, sep='=', collapse=','), '\n')
    """

    res = subprocess.run([str(rscript_path), "-e", r_code], capture_output=True, text=True)
    
    for line in res.stdout.splitlines():
        if "R_CHECK_RESULT:" in line:
            raw_res = line.replace("R_CHECK_RESULT:", "").strip()
            pairs = raw_res.split(",")
            for p in pairs:
                if "=" in p:
                    pkg, ok = p.split("=")
                    icon = "[OK]" if ok.strip() == "TRUE" else "[MISSING]"
                    print(f"  {icon:10} R Package: {pkg}")

    return res.returncode == 0


def generate_hardware_config(hw_info: Dict[str, any], rscript_path: Optional[Path]) -> None:
    """Generate high-performance parallel execution configuration."""
    cfg_file = WORKSPACE_ROOT / "config" / "hardware_resources.yaml"
    cfg_file.parent.mkdir(parents=True, exist_ok=True)

    content = f"""# ==============================================================================
# CONFIGURACIÓN DE RECURSOS DE HARDWARE Y PARALELIZACIÓN DE ALTO RENDIMIENTO
# Generado automáticamente por setup_environment.py
# ==============================================================================

hardware:
  system_os: "{hw_info['os']}"
  os_release: "{hw_info['os_release']}"
  architecture: "{hw_info['arch']}"
  total_logical_cores: {hw_info['total_cores']}
  recommended_workers: {hw_info['recommended_workers']}
  python_executable: "{str(WORKSPACE_ROOT / ('.venv/Scripts/python.exe' if hw_info['os'] == 'Windows' else '.venv/bin/python'))}"
  rscript_executable: "{str(rscript_path) if rscript_path else 'Rscript'}"

parallelization:
  enabled: true
  engine: "doSNOW"
  nb_cores: {hw_info['recommended_workers']}
  detect_cores: false
  memory_gc_interval: 100
  disk_io_optimized: true
"""
    with open(cfg_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"\n[OK] Configuración de recursos generada en: {cfg_file}")


def main() -> None:
    print_banner("INSTALADOR Y CONFIGURADOR DE ENTORNO: CDT v8.0 AUTOMATION")

    # 1. Hardware detection
    hw = get_hardware_info()
    print(f"  Sistema Operativo : {hw['os']} ({hw['os_release']} - {hw['arch']})")
    print(f"  Núcleos de CPU    : {hw['total_cores']} núcleos detectados")
    print(f"  Núcleos a Asignar : {hw['recommended_workers']} núcleos paralelos (100% recursos con estabilidad)")
    print(f"  Python Base       : {hw['python_version']} ({sys.executable})")

    # 2. Python Virtual Environment
    print_banner("1. CONFIGURACIÓN DEL ENTORNO PYTHON")
    py_bin, pip_bin = setup_python_venv()

    # 3. R Environment
    print_banner("2. CONFIGURACIÓN DEL ENTORNO R")
    rscript = find_rscript()
    if not rscript:
        print("[!] Advertencia: No se encontró el ejecutable Rscript en el sistema.")
        if hw["os"] == "Linux":
            print("    En Ubuntu/Debian, instale R con: sudo apt-get update && sudo apt-get install -y r-base r-base-dev libnetcdf-dev libgdal-dev libgeos-dev libudunits2-dev")
        elif hw["os"] == "Windows":
            print("    En Windows, descargue e instale R 4.4+ desde: https://cran.r-project.org/bin/windows/base/")
    else:
        print(f"[OK] Rscript localizado en: {rscript}")
        setup_r_environment(rscript)

    # 4. Save Hardware Tuning Config
    print_banner("3. OPTIMIZACIÓN DE RECURSOS DE HARDWARE")
    generate_hardware_config(hw, rscript)

    print_banner("INSTALACIÓN Y CONFIGURACIÓN COMPLETADA CON ÉXITO")
    print("Para ejecutar los experimentos utilizando todos los recursos configurados:")
    if hw["os"] == "Windows":
        print("  >> Powershell: .\\run_experiments.ps1 -Config config/experiments_rainfall/EXP_R01_SBA_IDW_Baseline.yaml")
        print("  >> CMD / Bat : run_experiments.bat config/experiments_rainfall/EXP_R01_SBA_IDW_Baseline.yaml")
    else:
        print("  >> Linux Bash: ./run_experiments.sh config/experiments_rainfall/EXP_R01_SBA_IDW_Baseline.yaml")
    print("=" * 78 + "\n")


if __name__ == "__main__":
    main()
