# Django API + SPA + admin (port 8000)
Set-Location $PSScriptRoot
if (-not (Test-Path ".\venv\Scripts\Activate.ps1")) {
    Write-Host "venv missing. Create: python -m venv venv" -ForegroundColor Red
    exit 1
}
& ".\venv\Scripts\Activate.ps1"
python manage.py migrate --noinput
Write-Host "Backend: http://127.0.0.1:8000/  |  Admin: http://127.0.0.1:8000/admin/" -ForegroundColor Green
Write-Host "Tip: Django env = backend/.env" -ForegroundColor DarkGray
python manage.py runserver 8000
