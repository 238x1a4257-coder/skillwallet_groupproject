@echo off
cd /d "%~dp0"
echo ============================================
echo  Starting Personalized Networking Assistant
echo  Frontend (Streamlit)
echo ============================================
echo.
echo Make sure the backend is running first!
echo Open a separate terminal and run: start_backend.bat
echo.

streamlit run frontend/app.py

if errorlevel 1 (
    echo.
    echo ❌ Frontend failed to start.
    echo    Make sure you're in the project root folder.
    pause
)
