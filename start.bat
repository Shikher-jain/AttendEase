@echo off
REM Quick start script for AttendEase Student Attendance System (Windows)

echo ========================================
echo   AttendEase - Student Attendance System
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo [1/6] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully!
) else (
    echo [1/6] Virtual environment found
)
echo.

REM Activate virtual environment
echo [2/6] Activating virtual environment...
call venv\Scripts\activate
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo.

REM Install/Update dependencies
echo [3/6] Installing/Updating dependencies...
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed successfully!
echo.

REM Create necessary directories
echo [4/6] Creating necessary directories...
if not exist "logs" mkdir logs
if not exist "student_images" mkdir student_images
if not exist "backend\__pycache__" mkdir backend\__pycache__
if not exist "shared\__pycache__" mkdir shared\__pycache__
echo Directories ready!
echo.

REM Check if .env file exists
if not exist ".env" (
    echo WARNING: .env file not found!
    echo Creating .env from .env.example...
    copy .env.example .env >nul
    echo Please configure .env file if needed
    echo.
)

REM Start backend
echo [5/6] Starting backend server...
echo Backend will run on http://localhost:8000
echo API Docs: http://localhost:8000/docs
start "AttendEase Backend" cmd /k "uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"
echo.

REM Wait for backend to start
echo Waiting for backend to initialize...
timeout /t 5 /nobreak >nul
echo.

REM Start frontend
echo [6/6] Starting frontend...
echo Frontend will open at http://localhost:8501
echo.
echo ========================================
echo   Both services are starting...
echo   Close this window to stop both servers
echo ========================================
echo.

REM Choose which frontend to start
choice /C 12 /N /M "Start [1] Standard Frontend or [2] Live Recognition Frontend? "
if errorlevel 2 (
    streamlit run frontend/app_live.py
) else (
    streamlit run frontend/app.py
)

pause
