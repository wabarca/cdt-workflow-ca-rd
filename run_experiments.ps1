# ==============================================================================
# Lanzador de Experimentos CDT para Windows (PowerShell)
# ==============================================================================

param (
    [string]$Config = "config/experiments_rainfall/EXP_R01_SBA_IDW_Baseline.yaml",
    [switch]$CheckEnv
)

# Usar el entorno virtual si existe
if (Test-Path ".venv\Scripts\python.exe") {
    $PyExec = ".venv\Scripts\python.exe"
} else {
    $PyExec = "python"
}

Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "  EJECUTANDO EXPERIMENTO CDT CON MAXIMIZACIÓN DE RECURSOS" -ForegroundColor Cyan
Write-Host "  Configuración : $Config" -ForegroundColor Yellow
Write-Host "  Python        : $PyExec" -ForegroundColor Yellow
Write-Host "==============================================================================" -ForegroundColor Cyan

if ($CheckEnv) {
    & $PyExec launcher\experiment_runner.py --config $Config --check-env
} else {
    & $PyExec launcher\experiment_runner.py --config $Config
}
