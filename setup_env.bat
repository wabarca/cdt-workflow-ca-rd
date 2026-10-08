@echo off
REM ==============================================================================
REM Instalador y Verificador de Entorno CDT para Windows (CMD)
REM ==============================================================================

echo ==============================================================================
echo   INICIANDO INSTALACION Y VERIFICACION DE ENTORNO CDT (WINDOWS)
echo ==============================================================================

python setup_environment.py
if %ERRORLEVEL% NEQ 0 (
    echo [!] Error durante la ejecucion de setup_environment.py
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [OK] Proceso finalizado. El entorno esta listo para ejecutar experimentos.
pause
