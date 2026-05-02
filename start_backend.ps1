# Django API + SPA + admin (port 8000)
Set-Location $PSScriptRoot
if (-not (Test-Path ".\venv\Scripts\Activate.ps1")) {
    Write-Host "venv missing. Create: python -m venv venv" -ForegroundColor Red
    exit 1
}
& ".\venv\Scripts\Activate.ps1"
python manage.py migrate --noinput
Write-Host "Django runserver (local): port 8000  |  Railway API+admin: https://web-production-77db8.up.railway.app/" -ForegroundColor Green
Write-Host "Env: backend/.env — local dev CORS: DEPLOYMENT_CORS_ORIGINS=http://localhost:5173" -ForegroundColor DarkGray
python manage.py runserver 8000
