"""
Enhanced Streamlit frontend with live video face recognition.
"""
import streamlit as st
import requests
from PIL import Image
import io
import pandas as pd
from datetime import datetime
import cv2
import numpy as np
import time
import base64

# MUST be the first Streamlit command
st.set_page_config(
    page_title="Student Attendance System - Live Recognition",
    page_icon="📹",
    layout="wide"
)

# Configuration
BACKEND_URL = st.sidebar.text_input("Backend URL", "http://localhost:8000")

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .live-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background-color: #ff0000;
        animation: blink 1s infinite;
        margin-right: 8px;
    }
    @keyframes blink {
        0%, 50%, 100% { opacity: 1; }
        25%, 75% { opacity: 0.3; }
    }
    .recognized-student {
        padding: 10px;
        margin: 5px 0;
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        border-radius: 4px;
    }
    .video-frame-detected {
        border: 5px solid #28a745;
        border-radius: 8px;
        padding: 5px;
        box-shadow: 0 0 20px rgba(40, 167, 69, 0.5);
    }
    .video-frame-no-face {
        border: 5px solid #dc3545;
        border-radius: 8px;
        padding: 5px;
        box-shadow: 0 0 20px rgba(220, 53, 69, 0.5);
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">📹 Student Attendance System - Live Recognition</div>', unsafe_allow_html=True)

# Sidebar menu
st.sidebar.title("Navigation")
menu = [
    "Live Registration", 
    "Live Attendance (Quick)", 
    "Live Attendance (Session)",
    "View Students",
    "View Attendance",
    "System Status"
]
choice = st.sidebar.selectbox("Select Option", menu)


def check_backend_health():
    """Check if backend is healthy."""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def check_camera_status():
    """Check if camera is active."""
    try:
        response = requests.get(f"{BACKEND_URL}/live/camera/status", timeout=5)
        if response.status_code == 200:
            return response.json()
        return {"is_active": False, "active_sessions": 0}
    except:
        return {"is_active": False, "active_sessions": 0}


def start_camera():
    """Start the camera."""
    try:
        response = requests.post(f"{BACKEND_URL}/live/camera/start", timeout=10)
        if response.status_code == 200:
            return True, response.json().get("message", "Camera started")
        return False, response.json().get("detail", "Failed to start camera")
    except Exception as e:
        return False, str(e)


def stop_camera():
    """Stop the camera."""
    try:
        response = requests.post(f"{BACKEND_URL}/live/camera/stop", timeout=10)
        if response.status_code == 200:
            return True, "Camera stopped"
        return False, "Failed to stop camera"
    except Exception as e:
        return False, str(e)


def check_face_detection():
    """Check if face is currently detected in frame."""
    try:
        response = requests.get(f"{BACKEND_URL}/live/face/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("face_detected", False), data.get("face_count", 0)
        return False, 0
    except:
        return False, 0


# Check backend health
if not check_backend_health():
    st.error("⚠️ Backend is not responding. Please ensure the backend server is running.")
    st.info(f"Expected backend URL: {BACKEND_URL}")
    st.stop()

# Camera control in sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("📹 Camera Control")
camera_status = check_camera_status()

if camera_status["is_active"]:
    st.sidebar.success("🟢 Camera is ACTIVE")
    st.sidebar.write(f"Active sessions: {camera_status['active_sessions']}")
    if st.sidebar.button("🛑 Stop Camera"):
        success, msg = stop_camera()
        if success:
            st.sidebar.success(msg)
            st.rerun()
        else:
            st.sidebar.error(msg)
else:
    st.sidebar.warning("🔴 Camera is INACTIVE")
    if st.sidebar.button("▶️ Start Camera"):
        success, msg = start_camera()
        if success:
            st.sidebar.success(msg)
            st.rerun()
        else:
            st.sidebar.error(msg)

# Page: Live Registration
if choice == "Live Registration":
    st.header("📹 Live Registration with Camera")
    
    if not camera_status["is_active"]:
        st.warning("⚠️ Camera is not active. Please start the camera from the sidebar.")
        st.stop()
    
    st.info("""
    **How it works:**
    1. Enter the student's name
    2. Position yourself in front of the camera
    3. Click "Capture & Register"
    4. The system will automatically capture your face and register you
    
    **Tips:**
    - Ensure good lighting
    - Look directly at the camera
    - Make sure you're the only person in frame
    - Stay still when capturing
    """)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Registration Details")
        student_name = st.text_input("Student Name *", max_chars=100)
        
        st.write("")
        st.write("**Camera Preview**")
        
        # Check face detection status
        face_detected, face_count = check_face_detection()
        
        if face_detected and face_count == 1:
            st.success("✅ Face detected! Ready to capture.")
            border_class = "video-frame-detected"
        elif face_count > 1:
            st.warning(f"⚠️ Multiple faces detected ({face_count}). Please ensure only one person is in frame.")
            border_class = "video-frame-no-face"
        else:
            st.error("❌ No face detected. Position yourself in the camera frame.")
            border_class = "video-frame-no-face"
        
        # Video stream preview with conditional border
        video_url = f"{BACKEND_URL}/live/video/stream"
        st.markdown(f'<div class="{border_class}"><img src="{video_url}" width="100%"></div>', unsafe_allow_html=True)
        
        # Auto-refresh checkbox for live feedback
        if st.checkbox("🔄 Auto-refresh detection", value=True, key="auto_refresh_reg"):
            time.sleep(1)
            st.rerun()
    
    with col2:
        st.subheader("Capture & Register")
        
        if st.button("📸 Capture & Register", type="primary", use_container_width=True):
            if not student_name or not student_name.strip():
                st.error("❌ Please enter student name")
            else:
                with st.spinner("Capturing and registering..."):
                    try:
                        # Live register
                        data = {"name": student_name.strip()}
                        response = requests.post(
                            f"{BACKEND_URL}/live/register",
                            data=data,
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.success(f"✅ {result['name']} registered successfully!")
                            st.balloons()
                            st.json(result)
                        else:
                            error_msg = response.json().get("detail", "Unknown error")
                            st.error(f"❌ Registration failed: {error_msg}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

# Page: Live Attendance (Quick)
elif choice == "Live Attendance (Quick)":
    st.header("⚡ Quick Live Attendance")
    
    if not camera_status["is_active"]:
        st.warning("⚠️ Camera is not active. Please start the camera from the sidebar.")
        st.stop()
    
    st.info("""
    **Quick Attendance Mode:**
    - Point camera at students
    - Click "Mark Attendance Now"
    - System instantly recognizes and marks attendance
    - Best for individual or small group attendance
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📹 Live Camera Feed")
        video_url = f"{BACKEND_URL}/live/video/stream"
        st.markdown(f'<img src="{video_url}" width="100%">', unsafe_allow_html=True)
    
    with col2:
        st.subheader("Controls")
        
        if st.button("✅ Mark Attendance Now", type="primary", use_container_width=True):
            with st.spinner("Processing..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/live/attendance/quick",
                        timeout=15
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        if result["status"] == "success":
                            st.success(f"✅ Marked attendance for {result['total_marked']} student(s)!")
                            
                            # Display marked students
                            for record in result["marked_attendance"]:
                                st.markdown(f"""
                                <div class="recognized-student">
                                    <strong>{record['student_name']}</strong><br>
                                    Confidence: {record['confidence']:.2%}<br>
                                    Time: {record['timestamp']}
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.warning(result.get("message", "No students recognized"))
                    else:
                        st.error("❌ Failed to mark attendance")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        st.markdown("---")
        st.write("**Recent Captures**")
        if st.button("🔄 Refresh Status"):
            st.rerun()

# Page: Live Attendance (Session)
elif choice == "Live Attendance (Session)":
    st.header("🎯 Live Attendance Session")
    
    if not camera_status["is_active"]:
        st.warning("⚠️ Camera is not active. Please start the camera from the sidebar.")
        st.stop()
    
    st.info("""
    **Session Mode - Best for Class Attendance:**
    1. Start a session
    2. Students stand in front of camera
    3. System continuously recognizes faces
    4. Confirm when done to mark attendance
    
    **Advantages:**
    - More reliable (requires multiple recognitions)
    - Better for groups
    - Shows recognized count in real-time
    """)
    
    # Session management
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📹 Live Camera Feed")
        video_url = f"{BACKEND_URL}/live/video/stream"
        st.markdown(f'<img src="{video_url}" width="100%">', unsafe_allow_html=True)
    
    with col2:
        st.subheader("Session Controls")
        
        session_id = "default"
        
        # Start session
        if st.button("▶️ Start Session", use_container_width=True):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/live/attendance/session/start",
                    params={"session_id": session_id},
                    timeout=10
                )
                if response.status_code == 200:
                    st.success("✅ Session started!")
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        
        # Get session status
        try:
            response = requests.get(
                f"{BACKEND_URL}/live/attendance/session/status",
                params={"session_id": session_id},
                timeout=10
            )
            
            if response.status_code == 200:
                status = response.json()
                
                st.markdown("---")
                st.metric("Recognized Students", status["recognized_count"])
                st.metric("Session Duration", f"{status['session_duration']:.1f}s")
                
                if status["recognized_students"]:
                    st.markdown("**Recognized:**")
                    for student in status["recognized_students"]:
                        st.markdown(f"""
                        <div class="recognized-student">
                            {student['name']}<br>
                            <small>Seen {student['recognition_count']}x - {student['confidence']:.2%}</small>
                        </div>
                        """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                # Confirm and mark attendance
                min_recognitions = st.number_input(
                    "Min recognitions required",
                    min_value=1,
                    max_value=10,
                    value=3
                )
                
                if st.button("✅ Confirm & Mark Attendance", type="primary", use_container_width=True):
                    try:
                        response = requests.post(
                            f"{BACKEND_URL}/live/attendance/session/confirm",
                            params={
                                "session_id": session_id,
                                "min_recognitions": min_recognitions
                            },
                            timeout=15
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            if result["status"] == "success":
                                st.success(f"✅ Marked attendance for {result['total_marked']} student(s)!")
                                st.balloons()
                                for record in result["marked_attendance"]:
                                    st.write(f"- {record['student_name']}")
                            else:
                                st.warning(result.get("message"))
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                
                # Stop session
                if st.button("🛑 Stop Session", use_container_width=True):
                    try:
                        response = requests.post(
                            f"{BACKEND_URL}/live/attendance/session/stop",
                            params={"session_id": session_id},
                            timeout=10
                        )
                        if response.status_code == 200:
                            st.success("Session stopped")
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        except:
            st.info("No active session. Click 'Start Session' to begin.")
        
        # Auto-refresh
        if st.checkbox("Auto-refresh (every 2s)"):
            time.sleep(2)
            st.rerun()

# Page: View Students
elif choice == "View Students":
    st.header("👥 Registered Students")
    
    try:
        response = requests.get(f"{BACKEND_URL}/students/", timeout=10)
        if response.status_code == 200:
            students = response.json()
            
            if not students:
                st.info("No students registered yet.")
            else:
                st.success(f"✅ Total Students: {len(students)}")
                
                df = pd.DataFrame(students)
                st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.error("Failed to load students")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# Page: View Attendance
elif choice == "View Attendance":
    st.header("📊 Attendance Records")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        try:
            response = requests.get(f"{BACKEND_URL}/attendance/", timeout=10)
            
            if response.status_code == 200:
                records = response.json()
                
                if not records:
                    st.info("No attendance records found.")
                else:
                    st.success(f"✅ Total Records: {len(records)}")
                    
                    df = pd.DataFrame(records)
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df = df.sort_values('timestamp', ascending=False)
                    
                    st.dataframe(
                        df[['student_name', 'timestamp']],
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Download button
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "📥 Download CSV",
                        csv,
                        f"attendance_{datetime.now().strftime('%Y%m%d')}.csv",
                        "text/csv"
                    )
            else:
                st.error("Failed to load attendance records")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    
    with col2:
        st.subheader("Quick Stats")
        try:
            students = requests.get(f"{BACKEND_URL}/students/").json()
            records = requests.get(f"{BACKEND_URL}/attendance/").json()
            
            st.metric("Total Students", len(students))
            st.metric("Total Records", len(records))
            
            today = datetime.now().date()
            today_records = [
                r for r in records 
                if datetime.fromisoformat(r['timestamp']).date() == today
            ]
            st.metric("Today's Attendance", len(today_records))
        except:
            pass

# Page: System Status
elif choice == "System Status":
    st.header("🏥 System Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Backend Status")
        if check_backend_health():
            st.success("✅ Backend is healthy")
        else:
            st.error("❌ Backend is unhealthy")
        
        st.subheader("Camera Status")
        status = check_camera_status()
        if status["is_active"]:
            st.success("✅ Camera is active")
            st.write(f"Active sessions: {status['active_sessions']}")
        else:
            st.warning("⚠️ Camera is inactive")
    
    with col2:
        st.subheader("System Information")
        st.info(f"""
        **Backend URL:** {BACKEND_URL}
        **Current Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        **Mode:** Live Recognition Enabled
        """)
    
    # Test video stream
    st.subheader("Camera Test")
    if camera_status["is_active"]:
        st.write("Live camera feed:")
        video_url = f"{BACKEND_URL}/live/video/stream"
        st.markdown(f'<img src="{video_url}" width="50%">', unsafe_allow_html=True)
    else:
        st.info("Start camera to test video stream")

# Footer
st.sidebar.markdown("---")
st.sidebar.info("""
**Live Face Recognition System**

Features:
- Live camera registration
- Real-time face detection
- Quick attendance marking
- Session-based attendance
- Continuous recognition

Version 2.1.0
""")
