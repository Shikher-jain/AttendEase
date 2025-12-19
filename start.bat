@echo off
REM Quick start script for the Student Attendance System (Windows)

echo Starting Student Attendance System...
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Create necessary directories
echo Creating directories...
if not exist "logs" mkdir logs
if not exist "student_images" mkdir student_images

REM Start backend
echo Starting backend server...
cd ..
start "Backend Server" cmd /k "uvicorn attendance_app.backend.main:app --reload --host 0.0.0.0 --port 8000"
cd attendance_app

REM Wait for backend to start
echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

REM Start frontend
echo Starting frontend...
streamlit run frontend/app.py

pause
