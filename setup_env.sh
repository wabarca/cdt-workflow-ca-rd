#!/usr/bin/env bash
# ==============================================================================
# Instalador y Verificador de Entorno CDT para Linux / macOS (Bash)
# ==============================================================================

set -e

echo "=============================================================================="
echo "  INICIANDO INSTALACIÓN Y VERIFICACIÓN DE ENTORNO CDT (LINUX / BASH)"
echo "=============================================================================="

# Detectar python3
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "[!] Error: No se encontró Python en el sistema. Por favor instale python3."
    exit 1
fi

$PYTHON_CMD setup_environment.py

echo ""
echo "[OK] Configuración finalizada. Puede ejecutar experimentos con ./run_experiments.sh"
