# Vite dev server (port 5173) — proxies /api to Django
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

Set-Location (Join-Path $PSScriptRoot "frontend")

$node = "C:\Program Files\nodejs\node.exe"
$npm = "C:\Program Files\nodejs\npm.cmd"
if (-not (Test-Path $npm)) {
    Write-Host "Node.js not found. Install: winget install OpenJS.NodeJS.LTS" -ForegroundColor Red
    exit 1
}

Write-Host "Vite dev — /api proxied to VITE_DJANGO_URL (Railway API: https://web-production-77db8.up.railway.app)" -ForegroundColor Green
Write-Host "Production SPA: https://allybank-front-1wz4.vercel.app/" -ForegroundColor DarkGray
if (-not (Test-Path ".\node_modules")) {
    & $npm install
}
& $npm run dev
