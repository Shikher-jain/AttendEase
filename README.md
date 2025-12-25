#  Student Attendance System v2.1 

A comprehensive face recognition-based attendance system with **real-time live video recognition**, robust error handling, logging, and a modern user interface.

##  Features

###  **NEW: Live Face Recognition**
- **Live Camera Registration**: Register students using real-time camera capture (no uploads!)
- **Quick Live Attendance**: Instant attendance marking from live video feed
- **Session-Based Attendance**: Continuous recognition for large groups
- **Real-Time Video Streaming**: MJPEG video stream with face detection overlays
- **Visual Feedback**: See recognition happen in real-time with bounding boxes and labels

### Core Functionality
- **Student Registration**: Register students with photos and automatic face detection
- **Manual Attendance**: Mark attendance by selecting students from a list
- **Face Recognition Attendance**: Automatically detect and recognize students from photos
- **Camera Integration**: Real-time face recognition using device camera
- **Attendance Tracking**: View, filter, and export attendance records
- **Statistics Dashboard**: Monitor attendance trends and system usage

### Technical Features
-  Comprehensive error handling and validation
-  Detailed logging for debugging and monitoring
-  **Hybrid face detection** (Mediapipe + optional Haar Cascade fallback)
-  Face detection with validation (single face per image)
-  Database relationships and integrity constraints
-  RESTful API with FastAPI
-  Interactive UI with Streamlit
-  Configuration management with environment variables
-  Comprehensive test suite

##  Project Structure

```
attendance_app/
 backend/                # Backend API
    main.py            # FastAPI application with endpoints
    database.py        # SQLAlchemy models and DB config
    config.py          # Configuration management
    logger.py          # Logging configuration
 frontend/              # Frontend UI
    app.py            # Streamlit application
 shared/                # Shared utilities
   face_recognition_service.py  # Mediapipe + DeepFace face recognition logic
    live_video_service.py        # Live video processing
 tests/                 # Test suite
    test_api.py       # API endpoint tests
    test_database.py  # Database model tests
   test_face_recognition.py  # Face recognition tests (optional)
 student_images/        # Student photos storage
 logs/                  # Application logs
 haarcascade_frontalface_default.xml  # Haar Cascade classifier for face detection
 requirements.txt       # Python dependencies
 README.md             # This file
```

##  Quick Start Guide

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Webcam (optional, for camera-based attendance)

### Installation (One-time Setup)

#### Using Start Scripts (Recommended)

**Windows:**
```bash
# Navigate to project directory
cd AttendEase

# Run the start script
start.bat

# Choose option:
# 1 - Standard interface (app.py)
# 2 - Live interface (app_live.py)
```

**macOS/Linux:**
```bash
# Navigate to project directory
cd AttendEase

# Make script executable
chmod +x start.sh

# Run the start script
./start.sh

# Choose option:
# 1 - Standard interface
# 2 - Live interface
```

#### Manual Setup

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
uvicorn backend.main:app --reload

# Start frontend (Terminal 2)
# Standard interface:
streamlit run frontend/app.py
# OR Live interface:
streamlit run frontend/app_live.py
```

### Access the Application

- **Frontend UI**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### First Steps

1. **Register Students**
   - Go to "Register Student" or "Live Registration"
   - Enter student name
   - Upload photo or use live camera
   - Click "Register Student"

2. **Mark Attendance**
   - Use "Mark Attendance (Face Recognition)" or "Live Attendance"
   - Upload photo or use camera
   - System automatically recognizes and marks attendance

3. **View Records**
   - Go to "View Attendance"
   - Filter by student or date
   - Download as CSV

### Quick Start Common Issues

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

---

##  Usage Guide

### Registering Students

1. Navigate to "Register Student" in the sidebar
2. Enter the student's full name
3. Upload a clear photo with the student's face
4. Click "Register Student"

**Guidelines for best results:**
- Upload photos with only ONE face
- Ensure good lighting
- Face should be clearly visible
- Avoid sunglasses or face coverings
- Supported formats: JPG, JPEG, PNG
- Maximum file size: 5MB

### Marking Attendance

#### Manual Method
1. Go to "Mark Attendance (Manual)"
2. Select a student from the dropdown
3. Click "Mark Present"

#### Face Recognition Method
1. Go to "Mark Attendance (Face Recognition)"
2. **Option A**: Upload a photo
   - Click "Browse files" to upload
   - Click "Recognize and Mark Attendance"
3. **Option B**: Use camera
   - Click "Take a picture" to capture
   - Click "Process Camera Photo"

The system will automatically:
- Detect faces in the image
- Recognize registered students
- Mark attendance for all recognized students

### Viewing Attendance

1. Navigate to "View Attendance"
2. Use filters to narrow down records:
   - **By Student**: Select a specific student or "All Students"
   - **By Date**: Choose a specific date
3. Click "Refresh" to reload
4. Download records as CSV using the "Download as CSV" button

### Monitoring Statistics

1. Go to "Statistics" to view:
   - Total students registered
   - Total attendance records
   - Today's attendance count
   - Attendance by student (bar chart)
   - Recent activity

### System Health Check

1. Navigate to "System Health"
2. View backend status and system information
3. Run endpoint tests to verify system functionality

---

##  Live Face Recognition Guide

### Overview

The system supports **real-time live video recognition** for both registration and attendance marking with three powerful modes:

#### Live Features
- **Live Camera Registration**: Register students using real-time camera capture (no uploads!)
- **Quick Live Attendance**: Instant attendance marking from live video feed
- **Session-Based Attendance**: Continuous recognition for large groups with reliability thresholds
- **Real-Time Video Streaming**: MJPEG video stream with face detection overlays
- **Visual Feedback**: See recognition happen in real-time with bounding boxes and labels

### Getting Started with Live Recognition

#### 1. Start the Live Interface

```bash
# Terminal 1 - Backend
uvicorn backend.main:app --reload

# Terminal 2 - Live Frontend
streamlit run frontend/app_live.py
```

**Access at**: http://localhost:8501

#### 2. Camera Control

Control the camera from the sidebar:
- ** Start Camera** - Activates your webcam
- ** Stop Camera** - Deactivates camera
- **Status Indicator** - Shows if camera is active

### Live Registration 

Register students using real-time camera capture:

1. Click "Start Camera" in the sidebar
2. Go to "Live Registration"
3. Enter student name
4. Position face in camera view
5. Click "Capture & Register"
6. System automatically captures and registers

**Benefits:**
- No need to upload files
- Instant capture with validation
- Single face validation
- Better quality control

### Quick Live Attendance 

Mark attendance instantly from live camera feed:

1. Ensure camera is started
2. Go to "Live Attendance (Quick)"
3. Position students in front of camera
4. Click "Mark Attendance Now"
5. System recognizes and marks instantly

**Best for:** Individual attendance, small groups, quick check-ins

### Session-Based Attendance 

Continuous recognition session for reliable group attendance:

1. Start camera
2. Go to "Live Attendance (Session)"
3. Click "Start Session"
4. Students stand in camera view (3-5 seconds each)
5. System continuously recognizes faces
6. Set minimum recognitions (e.g., 3 times)
7. Click "Confirm & Mark Attendance"

**Benefits:**
- More reliable (requires multiple recognitions)
- Better for large groups
- Reduces false positives
- Shows recognition count in real-time

### Tips for Best Results

**Lighting:**
- Good, even lighting is essential
- Avoid backlighting
- Face should be well-lit

**Positioning:**
- Look directly at camera
- Face should be clear and unobstructed
- Maintain reasonable distance (1-2 meters)

**For Groups:**
- Use session mode
- Give each student a few seconds in frame
- Wait for "recognized" indicator

### Live API Endpoints

#### Camera Management
```bash
POST /live/camera/start?camera_index=0  # Start camera
POST /live/camera/stop                   # Stop camera
GET /live/camera/status                  # Check status
```

#### Live Registration
```bash
POST /live/register                      # Register with live camera
Form data: name=John%20Doe
```

#### Live Attendance
```bash
POST /live/attendance/quick              # Quick attendance (instant)
POST /live/attendance/session/start?session_id=class_1
GET /live/attendance/session/status?session_id=class_1
POST /live/attendance/session/confirm?session_id=class_1&min_recognitions=3
POST /live/attendance/session/stop?session_id=class_1
```

#### Video Streaming
```bash
GET /live/video/stream                   # Get live MJPEG stream
GET /live/frame/capture                  # Capture current frame
```

### Use Cases

**Scenario 1: Class Registration**
1. Start camera
2. Open Live Registration
3. Call each student  Enter name  Capture
4. Takes ~10 seconds per student

**Scenario 2: Daily Attendance (Small Class)**
1. Start camera
2. Open Quick Live Attendance
3. Students pass by camera one by one
4. Click "Mark Attendance Now" for each
5. Instant recognition and marking

**Scenario 3: Large Class Attendance**
1. Start camera and attendance session
2. Students enter, each pauses 3-5 seconds
3. System continuously recognizes
4. After all students arrived, confirm attendance
5. Only students with 3+ recognitions are marked

### Live Recognition Troubleshooting

**Camera Not Starting**
- Check if camera is available (Windows: `Get-PnpDevice -Class Camera`)
- Try different camera index (0, 1, 2): `POST /live/camera/start?camera_index=1`
- Check permissions/firewall

**Face Not Detected**
- Improve lighting
- Move closer to camera
- Remove glasses/hat temporarily
- Look directly at camera
- Ensure no obstructions

**Recognition Not Working**
- Verify students are registered
- Check camera is started
- Ensure good lighting
- Face should be clearly visible
- Try adjusting distance from camera

**Stream Not Loading**
- Check backend is running
- Verify camera is started
- Check firewall settings
- Try refreshing the page

### Performance Optimization

**For Better Speed:**
```python
# In config.py:
FACE_EMBEDDING_MODEL = "Facenet"   # Smaller model, faster on CPU
FACE_DETECTION_METHOD = "mediapipe"
```

**For Better Accuracy:**
```python
# In config.py:
FACE_EMBEDDING_MODEL = "Facenet512"  # Higher dimensional embeddings
FACE_RECOGNITION_TOLERANCE = 0.6      # Lower = stricter matching
FACE_DETECTION_METHOD = "both"       # Mediapipe + Haar fallback
```

**Camera Settings:**
```python
# In live_video_service.py:
self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)   # Resolution
self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
self.camera.set(cv2.CAP_PROP_FPS, 30)             # Frame rate
```

### Workflow Comparison

| Task | Old Method | Live Method |
|------|------------|-------------|
| **Registration** | Upload photo  Process | Face camera  Instant capture |
| **Attendance** | Select from list | Automatic recognition |
| **Group Attendance** | One by one selection | Continuous session mode |
| **Speed** | ~30 sec/student | ~5 sec/student |
| **Reliability** | Depends on photo quality | Real-time validation |

### Benefits Summary

 **No photo upload needed** - Instant camera capture  
 **Real-time validation** - See recognition immediately  
 **Faster registration** - 3x faster than upload method  
 **Better for groups** - Session mode handles multiple students  
 **More engaging** - Visual feedback with live video  
 **Flexible modes** - Choose quick or session-based  
 **Professional look** - Live video stream with overlays  

---

##  Configuration

The system can be configured using environment variables or by editing `backend/config.py`:

```python
# Database
DATABASE_URL = "sqlite:///./attendance.db"

# File Upload
UPLOAD_DIR = "student_images"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Face Recognition
FACE_EMBEDDING_MODEL = "Facenet512"  # DeepFace embedding backbone
FACE_RECOGNITION_TOLERANCE = 0.75     # Lower = more strict

# Face Detection Method
FACE_DETECTION_METHOD = "mediapipe"  # 'mediapipe', 'haar', or 'both'
FACE_DETECTION_CONFIDENCE = 0.6
HAAR_CASCADE_PATH = "haarcascade_frontalface_default.xml"

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "logs/app.log"

# API
API_HOST = "0.0.0.0"
API_PORT = 8000
```

##  Running Tests

Execute the test suite to ensure everything is working:

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_api.py -v

# Run with coverage
pytest tests/ --cov=backend --cov=shared --cov-report=html
```

##  API Documentation

### Endpoints

#### Health Check
- **GET** `/health` - Check system health

#### Students
- **POST** `/register/` - Register a new student
- **GET** `/students/` - List all students

#### Attendance
- **POST** `/attendance/` - Mark attendance (manual)
- **POST** `/attendance/recognize/` - Mark attendance via face recognition
- **GET** `/attendance/` - Get attendance records (with optional filters)

### Example API Calls

```bash
# Health check
curl http://localhost:8000/health

# List students
curl http://localhost:8000/students/

# Mark attendance
curl -X POST "http://localhost:8000/attendance/?student_id=1"

# Get attendance records
curl http://localhost:8000/attendance/
```

##  Troubleshooting

### Backend Issues

**Problem**: Backend won't start
```bash
# Solution: Check if port 8000 is in use
netstat -ano | findstr :8000  # Windows
lsof -i :8000  # macOS/Linux
```

**Problem**: Database errors
```bash
# Solution: Delete and recreate database
rm attendance.db
# Restart backend to recreate tables
```

### Face Recognition Issues

**Problem**: No face detected
- Ensure good lighting in photos
- Face should be clearly visible
- Upload higher resolution images

**Problem**: Wrong person recognized
- Reduce `FACE_RECOGNITION_TOLERANCE` in config.py
- Re-register student with better quality photo

### Frontend Issues

**Problem**: Backend not responding
- Verify backend is running at correct URL
- Check backend URL in frontend sidebar
- Look for firewall or network issues

##  Logging

Logs are stored in `logs/app.log` with detailed information:
- API requests and responses
- Face recognition operations
- Database operations
- Errors and exceptions

View logs in real-time:
```bash
# Windows
Get-Content logs/app.log -Tail 50 -Wait

# macOS/Linux
tail -f logs/app.log
```

##  Security Considerations

- Change default configurations in production
- Use environment variables for sensitive data
- Implement authentication for API endpoints
- Use HTTPS in production
- Regularly backup the database
- Implement rate limiting for API endpoints

##  Deployment

### Deploy to Render (Recommended)

**Quick Setup:**

1. **Get Cloudinary Account** (Free)
   - Sign up at [cloudinary.com](https://cloudinary.com)
   - Note: Cloud Name, API Key, API Secret

2. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Deploy to Render"
   git push origin main
   ```

3. **Deploy on Render**
   - Go to [dashboard.render.com](https://dashboard.render.com)
   - Click **"New +"**  **"Blueprint"**
   - Connect your repository
   - All environment variables are pre-configured in `render.yaml`
   - Click **"Apply"**

4. **Access Your App:**
   ```
   https://attendease-backend.onrender.com
   ```

**Includes:**
-  PostgreSQL database (auto-provisioned)
-  Cloudinary storage (CDN-backed)
-  HTTPS by default
-  Free tier available

### Local Production Testing

1. **Install production dependencies**
   ```bash
   pip install gunicorn  # For UNIX systems
   ```

2. **Run with Gunicorn**
   ```bash
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.main:app
   ```

3. **Use environment variables**
   ```bash
   export DATABASE_URL="postgresql://user:pass@localhost/attendance"
   export LOG_LEVEL="WARNING"
   ```

##  Contributing

To contribute to this project:
1. Create a new branch for your feature
2. Make your changes
3. Run tests to ensure everything works
4. Submit a pull request with clear description

##  License

This project is licensed under the MIT License.

##  Support

For issues, questions, or contributions:
- Create an issue in the repository
- Check logs in `logs/app.log` for error details
- Review API documentation at `/docs`
- Test endpoints at http://localhost:8000/docs

##  Future Enhancements

- [ ] Add user authentication and roles
- [ ] Email notifications for attendance
- [ ] Multi-camera support
- [ ] Mobile app integration
- [ ] Advanced analytics and reporting
- [ ] Export to multiple formats (PDF, Excel)
- [ ] Integration with existing school systems
- [ ] Real-time dashboard updates

---

**Version**: 2.1.0 (Production-Ready)  
**Last Updated**: December 2025  
**Built with**: FastAPI, Streamlit, Mediapipe, DeepFace, SQLAlchemy, Cloudinary