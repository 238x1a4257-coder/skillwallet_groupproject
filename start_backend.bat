@echo off
cd /d "%~dp0"
echo ============================================
echo  Starting Personalized Networking Assistant
echo  Backend Server
echo ============================================
echo.

:: Kill any existing process on port 8000
echo [1/3] Checking port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
    echo Port 8000 is in use by PID %%a - killing...
    taskkill /F /PID %%a >nul 2>&1
    timeout /t 1 /nobreak >nul
)
echo Port 8000 is free.

echo [2/3] Loading AI models (DistilBERT + GPT-2)...
echo This may take 10-30 seconds on first run...

echo [3/3] Starting server...
echo.
python -m uvicorn backend.main:app --reload --port 8000

if errorlevel 1 (
    echo.
    echo ❌ Backend failed to start. Common causes:
    echo    - Port 8000 already in use (run this script again)
    echo    - Missing dependencies (run: pip install -r requirements.txt)
    echo    - Make sure you're in the project root folder
    pause
)
