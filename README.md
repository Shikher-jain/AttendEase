# 📚 Student Attendance System v2.1 🎥

A comprehensive face recognition-based attendance system with **real-time live video recognition**, robust error handling, logging, and a modern user interface.

## 🌟 Features

### 🎥 **NEW: Live Face Recognition**
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
- ✅ Comprehensive error handling and validation
- ✅ Detailed logging for debugging and monitoring
- ✅ **Hybrid face detection** (face_recognition library + Haar Cascade for improved accuracy)
- ✅ Face detection with validation (single face per image)
- ✅ Database relationships and integrity constraints
- ✅ RESTful API with FastAPI
- ✅ Interactive UI with Streamlit
- ✅ Configuration management with environment variables
- ✅ Comprehensive test suite

## 📁 Project Structure

```
attendance_app/
├── backend/                # Backend API
│   ├── main.py            # FastAPI application with endpoints
│   ├── database.py        # SQLAlchemy models and DB config
│   ├── config.py          # Configuration management
│   └── logger.py          # Logging configuration
├── frontend/              # Frontend UI
│   └── app.py            # Streamlit application
├── shared/                # Shared utilities
│   ├── face_recognition_service.py  # Face recognition logic
│   └── live_video_service.py        # Live video processing
├── tests/                 # Test suite
│   ├── test_api.py       # API endpoint tests
│   ├── test_database.py  # Database model tests
│   └── test_face_recognition.py  # Face recognition tests
├── student_images/        # Student photos storage
├── logs/                  # Application logs
├── haarcascade_frontalface_default.xml  # Haar Cascade classifier for face detection
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Webcam (optional, for camera-based attendance)

### Installation

1. **Clone or navigate to the repository**
   ```bash
   cd attendance_app
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

#### 1. Start the Backend Server

```bash
# From the attendance_app directory
cd ..
uvicorn attendance_app.backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

#### 2. Start the Frontend Application

Open a new terminal and run:

```bash
# From the attendance_app directory
streamlit run frontend/app.py
```

The web interface will open automatically at `http://localhost:8501`

## 📖 Usage Guide

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

## 🔧 Configuration

The system can be configured using environment variables or by editing [backend/config.py](backend/config.py):

```python
# Database
DATABASE_URL = "sqlite:///./attendance.db"

# File Upload
UPLOAD_DIR = "student_images"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Face Recognition
FACE_RECOGNITION_MODEL = "hog"  # 'hog' or 'cnn'
FACE_RECOGNITION_TOLERANCE = 0.6  # Lower = more strict

# Face Detection Method (NEW)
FACE_DETECTION_METHOD = "both"  # 'auto' (face_recognition only), 'haar' (Haar Cascade only), or 'both' (combined)
HAAR_CASCADE_PATH = "haarcascade_frontalface_default.xml"

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "logs/app.log"

# API
API_HOST = "0.0.0.0"
API_PORT = 8000
```

## 🧪 Running Tests

Execute the test suite to ensure everything is working:

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_api.py -v

# Run with coverage
pytest tests/ --cov=backend --cov=shared --cov-report=html
```

## 📊 API Documentation

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

## 🛠️ Troubleshooting

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

## 📝 Logging

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

## 🔒 Security Considerations

- Change default configurations in production
- Use environment variables for sensitive data
- Implement authentication for API endpoints
- Use HTTPS in production
- Regularly backup the database
- Implement rate limiting for API endpoints

## 🚀 Deployment

### Production Deployment

1. **Install production dependencies**
   ```bash
   pip install gunicorn  # For UNIX systems
   ```

2. **Run with Gunicorn**
   ```bash
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker attendance_app.backend.main:app
   ```

3. **Use environment variables**
   ```bash
   export DATABASE_URL="postgresql://user:pass@localhost/attendance"
   export LOG_LEVEL="WARNING"
   ```

4. **Deploy frontend**
   ```bash
   streamlit run frontend/app.py --server.port 80 --server.address 0.0.0.0
   ```

## 🤝 Contributing

To contribute to this project:
1. Create a new branch for your feature
2. Make your changes
3. Run tests to ensure everything works
4. Submit a pull request with clear description

## 📄 License

This project is licensed under the MIT License.

## 👥 Support

For issues, questions, or contributions:
- Create an issue in the repository
- Check logs for error details
- Review API documentation at `/docs`

## 🎯 Future Enhancements

- [ ] Add user authentication and roles
- [ ] Email notifications for attendance
- [ ] Multi-camera support
- [ ] Mobile app integration
- [ ] Advanced analytics and reporting
- [ ] Export to multiple formats (PDF, Excel)
- [ ] Integration with existing school systems
- [ ] Real-time dashboard updates

---

**Version**: 2.0.0  
**Last Updated**: December 2025  
**Built with**: FastAPI, Streamlit, face_recognition, SQLAlchemy
