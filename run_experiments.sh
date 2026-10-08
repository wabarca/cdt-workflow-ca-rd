#!/usr/bin/env bash
# ==============================================================================
# Lanzador de Experimentos CDT para Linux / macOS (Bash)
# ==============================================================================

CONFIG_PATH=${1:-"config/experiments_rainfall/EXP_R01_SBA_IDW_Baseline.yaml"}

if [ -f ".venv/bin/python" ]; then
    PY_EXEC=".venv/bin/python"
elif command -v python3 &>/dev/null; then
    PY_EXEC="python3"
else
    PY_EXEC="python"
fi

echo "=============================================================================="
echo "  EJECUTANDO EXPERIMENTO CDT CON MAXIMIZACIÓN DE RECURSOS"
echo "  Configuración : $CONFIG_PATH"
echo "  Python        : $PY_EXEC"
echo "=============================================================================="

$PY_EXEC launcher/experiment_runner.py --config "$CONFIG_PATH"
