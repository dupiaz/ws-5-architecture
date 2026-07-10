@echo off
title SRT Subtitle Translator V2 (Isolated Env)

cd /d "%~dp0"

:: ── Check local virtual environment ───────────────────────────
if not exist ".venv\Scripts\python.exe" (
    echo [!] ERROR: Khong tim thay moi truong Python ao [.venv] trong repo!
    echo     Vui long khoi tao lai bang cach chay cac lenh sau:
    echo     uv venv
    echo     uv pip install tkinterdnd2
    echo.
    pause
    exit /b 1
)

echo [*] Starting SRT Subtitle Translator using local .venv...
echo.
".venv\Scripts\python.exe" app/main.py

echo.
echo [x] App closed.
pause
