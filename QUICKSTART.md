# Quick Start Guide

## Installation (One-time setup)

### Windows
```bash
# Navigate to project directory
cd attendance_app

# Run the start script
start.bat
```

### macOS/Linux
```bash
# Navigate to project directory
cd attendance_app

# Make script executable
chmod +x start.sh

# Run the start script
./start.sh
```

### Manual Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend (Terminal 1)
cd ..
uvicorn attendance_app.backend.main:app --reload

# Start frontend (Terminal 2)
cd attendance_app
streamlit run frontend/app.py
```

## Access the Application

- **Frontend UI**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## First Steps

1. **Register Students**
   - Go to "Register Student"
   - Enter student name
   - Upload a clear photo with face visible
   - Click "Register Student"

2. **Mark Attendance**
   - Use "Mark Attendance (Face Recognition)"
   - Upload a photo or use camera
   - System automatically recognizes and marks attendance

3. **View Records**
   - Go to "View Attendance"
   - Filter by student or date
   - Download as CSV

## Common Issues

**Backend not starting?**
- Check if port 8000 is available
- Make sure Python 3.8+ is installed

**Frontend not connecting?**
- Verify backend is running at http://localhost:8000
- Check the backend URL in the sidebar

**Face not detected?**
- Ensure good lighting
- Upload clear photos with visible faces
- One face per photo for registration

## Need Help?

Check the full [README.md](README.md) for detailed documentation.
