@echo off
setlocal
cd /d "%~dp0"

set "PYTHON=python"
if exist "%CD%\venv\Scripts\python.exe" (
  "%CD%\venv\Scripts\python.exe" -V >nul 2>&1
  if not errorlevel 1 (
    set "PYTHON=%CD%\venv\Scripts\python.exe"
  )
)

echo Starting Cinema Home API on http://127.0.0.1:8000
start "Cinema Home API" cmd /k ""%PYTHON%" -m uvicorn api:app --host 127.0.0.1 --port 8000"

echo Starting Cinema Home frontend on http://127.0.0.1:3000
start "Cinema Home Frontend" cmd /k ""%PYTHON%" -m http.server 3000 --bind 127.0.0.1"

echo.
echo Frontend: http://127.0.0.1:3000
echo API:      http://127.0.0.1:8000
echo.
echo Close the spawned windows to stop the app.
