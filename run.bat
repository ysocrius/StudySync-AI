@echo off
cd /d "%~dp0"
echo "Starting Citrine & Sage Assignment..."

:: Check for .env
if not exist "backend\.env" (
    echo [WARNING] backend\.env not found! Please create it with your OPENAI_API_KEY.
    pause
    exit /b
)

:: Start Backend
start "Citrine Backend" cmd /k "cd backend && (if not exist venv python -m venv venv) && call venv\Scripts\activate && pip install -r requirements.txt && python main.py"

:: Start Frontend
start "Citrine Frontend" cmd /k "cd frontend && npm install && npm run dev"

echo App is starting... Check the new terminal windows.
echo Frontend will be at http://localhost:5173
echo Backend will be at http://localhost:5000
pause
