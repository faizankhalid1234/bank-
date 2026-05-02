@echo off
setlocal
cd /d "%~dp0frontend"
where npm >nul 2>nul
if %errorlevel% equ 0 (
  call npm install
  if errorlevel 1 exit /b 1
  call npm run build
) else if exist "%ProgramFiles%\nodejs\npm.cmd" (
  call "%ProgramFiles%\nodejs\npm.cmd" install
  if errorlevel 1 exit /b 1
  call "%ProgramFiles%\nodejs\npm.cmd" run build
) else (
  echo Node.js not found. Install: winget install OpenJS.NodeJS.LTS
  exit /b 1
)
if errorlevel 1 exit /b 1
echo.
echo Build complete. Production app: https://allybank-front-1wz4.vercel.app/  ^(API: Railway^)
