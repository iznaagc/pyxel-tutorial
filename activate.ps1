# Activate Python virtual environment
$venvPath = Join-Path $PSScriptRoot ".venv\Scripts\Activate.ps1"

if (Test-Path $venvPath) {
    & $venvPath
    Write-Host "Virtual environment activated." -ForegroundColor Green
} else {
    Write-Host "Error: .venv not found at $venvPath" -ForegroundColor Red
    Write-Host "Run 'python -m venv .venv' to create it first." -ForegroundColor Yellow
}
