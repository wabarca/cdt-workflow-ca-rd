@echo off
REM ==============================================================================
REM Lanzador de Experimentos CDT para Windows (CMD)
REM ==============================================================================

set CONFIG_PATH=%1
if "%CONFIG_PATH%"=="" (
    set CONFIG_PATH=config/experiments_rainfall/EXP_R01_SBA_IDW_Baseline.yaml
)

REM Usar el entorno virtual si existe, sino el python global
if exist .venv\Scripts\python.exe (
    set PY_EXEC=.venv\Scripts\python.exe
) else (
    set PY_EXEC=python
)

echo ==============================================================================
echo   EJECUTANDO EXPERIMENTO CDT CON MAXIMIZACION DE RECURSOS
echo   Configuracion: %CONFIG_PATH%
echo   Python:        %PY_EXEC%
echo ==============================================================================

%PY_EXEC% launcher\experiment_runner.py --config %CONFIG_PATH%
pause
