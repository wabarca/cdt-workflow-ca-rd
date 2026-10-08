# ==============================================================================
# Instalador y Verificador de Entorno CDT para Windows (PowerShell)
# ==============================================================================

Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "  INICIANDO INSTALACIÓN Y VERIFICACIÓN DE ENTORNO CDT (POWERSHELL)" -ForegroundColor Cyan
Write-Host "==============================================================================" -ForegroundColor Cyan

python setup_environment.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[OK] Entorno configurado correctamente." -ForegroundColor Green
} else {
    Write-Host "`n[!] Ocurrió un problema durante la configuración." -ForegroundColor Red
}
