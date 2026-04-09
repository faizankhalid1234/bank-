# Vite dev server (port 5173) — proxies /api to Django
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

Set-Location (Join-Path $PSScriptRoot "frontend")

$node = "C:\Program Files\nodejs\node.exe"
$npm = "C:\Program Files\nodejs\npm.cmd"
if (-not (Test-Path $npm)) {
    Write-Host "Node.js not found. Install: winget install OpenJS.NodeJS.LTS" -ForegroundColor Red
    exit 1
}

Write-Host "Frontend: http://localhost:5173/  (backend: http://127.0.0.1:8000/ — start_backend.ps1)" -ForegroundColor Green
if (-not (Test-Path ".\node_modules")) {
    & $npm install
}
& $npm run dev
