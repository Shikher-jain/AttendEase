"""
Complete Streamlit frontend for Student Attendance System.
Combines manual upload and live webcam features.
"""
import streamlit as st
import requests
from PIL import Image
import io
import pandas as pd
from datetime import datetime, timedelta
import cv2
import numpy as np
import time
import base64
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MUST be the first Streamlit command
st.set_page_config(
    page_title="Student Attendance System",
    page_icon="📚",
    layout="wide"
)

# Configuration
BACKEND_URL = st.sidebar.text_input("Backend URL", os.getenv("BACKEND_URL", "http://localhost:8000"))

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
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
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
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">📚 AttendEase - Student Attendance System</div>', unsafe_allow_html=True)

# Sidebar menu
st.sidebar.title("Navigation")
menu_categories = {
    "📝 Registration": ["Register Student (Upload)", "Register Student (Live Camera)"],
    "✅ Attendance": ["Mark Attendance (Manual)", "Mark Attendance (Upload Photo)", "Mark Attendance (Live - Quick)", "Mark Attendance (Live - Session)"],
    "📊 View & Reports": ["View Students", "View Attendance", "Statistics"],
    "🔧 System": ["System Health", "Camera Status"]
}

# Flatten menu for selectbox
all_options = []
for category, options in menu_categories.items():
    all_options.extend(options)

choice = st.sidebar.selectbox("Select Option", all_options)


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
            data = response.json()
            return data.get("is_active", False), data.get("active_sessions", 0)
        return False, 0
    except:
        return False, 0


def start_camera():
    """Start the camera."""
    try:
        response = requests.post(f"{BACKEND_URL}/live/camera/start", timeout=10)
        if response.status_code == 200:
            return True, "Camera started successfully"
        return False, response.json().get("detail", "Failed to start camera")
    except Exception as e:
        return False, str(e)


def stop_camera():
    """Stop the camera."""
    try:
        response = requests.post(f"{BACKEND_URL}/live/camera/stop", timeout=10)
        if response.status_code == 200:
            return True, "Camera stopped successfully"
        return False, response.json().get("detail", "Failed to stop camera")
    except Exception as e:
        return False, str(e)


def handle_api_error(response):
    """Handle API error responses."""
    try:
        error_detail = response.json().get("detail", "Unknown error")
    except:
        error_detail = response.text or "Unknown error"
    return error_detail


# Check backend health
if not check_backend_health():
    st.error("⚠️ Backend is not responding. Please ensure the backend server is running.")
    st.info(f"Expected backend URL: {BACKEND_URL}")
    st.stop()

# Camera control in sidebar (if camera-related page)
if "Live" in choice or "Camera" in choice:
    st.sidebar.markdown("---")
    st.sidebar.subheader("📹 Camera Control")
    camera_status, active_sessions = check_camera_status()
    
    if camera_status:
        st.sidebar.success("🟢 Camera is ACTIVE")
        st.sidebar.write(f"Active sessions: {active_sessions}")
        if st.sidebar.button("🛑 Stop Camera"):
            success, msg = stop_camera()
            if success:
                st.sidebar.success(msg)
                st.rerun()
            else:
                st.sidebar.error(msg)
    else:
        st.sidebar.warning("⚫ Camera is OFF")
        if st.sidebar.button("▶️ Start Camera"):
            success, msg = start_camera()
            if success:
                st.sidebar.success(msg)
                st.rerun()
            else:
                st.sidebar.error(msg)

# ========== REGISTRATION PAGES ==========

if choice == "Register Student (Upload)":
    st.header("📝 Register New Student (Upload Photo)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Student Information")
        name = st.text_input("Student Name *", max_chars=100)
        st.caption("Enter the full name of the student")
        
        st.subheader("Upload Photo")
        file = st.file_uploader(
            "Upload Student Photo *", 
            type=["jpg", "jpeg", "png"],
            help="Upload a clear photo with the student's face visible"
        )
        
        if file is not None:
            image = Image.open(file)
            st.image(image, caption="Uploaded Photo", use_container_width=True)
        
        if st.button("Register Student", type="primary", use_container_width=True):
            if not name:
                st.error("Please enter student name")
            elif not file:
                st.error("Please upload a photo")
            else:
                with st.spinner("Registering student..."):
                    try:
                        files = {"file": (file.name, file.getvalue(), file.type)}
                        data = {"name": name}
                        response = requests.post(
                            f"{BACKEND_URL}/register/",
                            files=files,
                            data=data,
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.success(f"✅ Student registered successfully!")
                            st.json(result)
                        else:
                            error_msg = handle_api_error(response)
                            st.error(f"❌ Registration failed: {error_msg}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
    
    with col2:
        st.subheader("📋 Registration Guidelines")
        st.info("""
        **Photo Requirements:**
        - Clear, front-facing photo
        - Good lighting
        - Only one face in the photo
        - Face should be clearly visible
        - Acceptable formats: JPG, JPEG, PNG
        - Maximum file size: 5MB
        
        **Name Requirements:**
        - Use full name
        - Maximum 100 characters
        - Must be unique
        """)

elif choice == "Register Student (Live Camera)":
    st.header("📹 Register New Student (Live Camera)")
    
    camera_active, _ = check_camera_status()
    
    if not camera_active:
        st.warning("⚠️ Camera is not active. Please start the camera from the sidebar.")
        st.stop()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Live Camera Feed")
        video_placeholder = st.empty()
        video_url = f"{BACKEND_URL}/live/video/stream"
        video_placeholder.image(video_url, use_container_width=True)
    
    with col2:
        st.subheader("Student Information")
        name = st.text_input("Student Name *", key="live_reg_name")
        
        st.caption("Position your face in the camera and click Capture")
        
        if st.button("📸 Capture & Register", type="primary", use_container_width=True):
            if not name:
                st.error("Please enter student name")
            else:
                with st.spinner("Capturing and registering..."):
                    try:
                        response = requests.post(
                            f"{BACKEND_URL}/live/register",
                            json={"name": name},
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.success(f"✅ {result['message']}")
                            if "student" in result:
                                st.json(result["student"])
                        else:
                            error_msg = handle_api_error(response)
                            st.error(f"❌ Registration failed: {error_msg}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

# ========== ATTENDANCE PAGES ==========

elif choice == "Mark Attendance (Manual)":
    st.header("✅ Mark Attendance (Manual Selection)")
    
    try:
        response = requests.get(f"{BACKEND_URL}/students/", timeout=10)
        if response.status_code == 200:
            students = response.json()
            
            if not students:
                st.warning("No students registered yet.")
            else:
                st.subheader("Select Student")
                student_names = [s["name"] for s in students]
                selected_name = st.selectbox("Choose student:", student_names)
                
                if st.button("Mark Attendance", type="primary"):
                    selected_student = next(s for s in students if s["name"] == selected_name)
                    
                    try:
                        response = requests.post(
                            f"{BACKEND_URL}/attendance/",
                            json={"student_id": selected_student["id"]},
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.success(f"✅ Attendance marked for {selected_name}")
                            st.json(result)
                        else:
                            error_msg = handle_api_error(response)
                            st.error(f"❌ Failed: {error_msg}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        else:
            st.error("Failed to fetch students")
    except Exception as e:
        st.error(f"Error: {str(e)}")

elif choice == "Mark Attendance (Upload Photo)":
    st.header("📸 Mark Attendance (Face Recognition - Upload)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        file = st.file_uploader("Upload Photo", type=["jpg", "jpeg", "png"])
        
        if file is not None:
            image = Image.open(file)
            st.image(image, caption="Uploaded Photo", use_container_width=True)
            
            if st.button("Recognize & Mark Attendance", type="primary"):
                with st.spinner("Recognizing faces..."):
                    try:
                        files = {"file": (file.name, file.getvalue(), file.type)}
                        response = requests.post(
                            f"{BACKEND_URL}/recognize/",
                            files=files,
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            results = response.json()
                            st.success(f"✅ Recognized {len(results)} face(s)")
                            
                            for result in results:
                                if result["name"] != "Unknown":
                                    st.write(f"**{result['name']}** - Confidence: {result['confidence']:.2%}")
                        else:
                            error_msg = handle_api_error(response)
                            st.error(f"❌ Recognition failed: {error_msg}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
    
    with col2:
        st.info("""
        **Instructions:**
        1. Upload a clear photo
        2. Photo can contain multiple faces
        3. System will recognize registered students
        4. Attendance will be marked automatically
        """)

elif choice == "Mark Attendance (Live - Quick)":
    st.header("⚡ Quick Attendance (Live Camera)")
    
    camera_active, _ = check_camera_status()
    
    if not camera_active:
        st.warning("⚠️ Camera is not active. Please start the camera from the sidebar.")
        st.stop()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Live Camera Feed")
        video_placeholder = st.empty()
        video_url = f"{BACKEND_URL}/live/video/stream"
        video_placeholder.image(video_url, use_container_width=True)
    
    with col2:
        st.subheader("Quick Actions")
        
        if st.button("📸 Capture & Mark Attendance", type="primary", use_container_width=True):
            with st.spinner("Processing..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/live/attendance/quick",
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        if result["status"] == "success":
                            st.success(f"✅ Marked attendance for {result['total_marked']} student(s)")
                            for att in result["marked_attendance"]:
                                st.write(f"**{att['student_name']}** - Confidence: {att['confidence']:.2%}")
                        else:
                            st.warning(result["message"])
                    else:
                        error_msg = handle_api_error(response)
                        st.error(f"❌ Failed: {error_msg}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

elif choice == "Mark Attendance (Live - Session)":
    st.header("🔄 Continuous Attendance Session")
    
    camera_active, _ = check_camera_status()
    
    if not camera_active:
        st.warning("⚠️ Camera is not active. Please start the camera from the sidebar.")
        st.stop()
    
    st.info("Continuous session mode - automatically detects and marks attendance")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Live Feed")
        video_placeholder = st.empty()
        video_url = f"{BACKEND_URL}/live/video/stream"
    
    with col2:
        st.subheader("Session Control")
        session_name = st.text_input("Session Name", value=f"Session_{datetime.now().strftime('%Y%m%d_%H%M')}")
        
        if "session_active" not in st.session_state:
            st.session_state.session_active = False
        
        if not st.session_state.session_active:
            if st.button("▶️ Start Session", type="primary"):
                st.session_state.session_active = True
                st.rerun()
        else:
            if st.button("⏹️ Stop Session", type="secondary"):
                st.session_state.session_active = False
                st.rerun()
    
    if st.session_state.session_active:
        video_placeholder.image(video_url, use_container_width=True)
        st.success("🟢 Session is active")
    else:
        st.info("Click 'Start Session' to begin")

# ========== VIEW & REPORTS PAGES ==========

elif choice == "View Students":
    st.header("👥 Registered Students")
    
    try:
        response = requests.get(f"{BACKEND_URL}/students/", timeout=10)
        
        if response.status_code == 200:
            students = response.json()
            
            if not students:
                st.info("No students registered yet.")
            else:
                st.success(f"Total Students: {len(students)}")
                
                df = pd.DataFrame(students)
                st.dataframe(df, use_container_width=True)
                
                # Delete student option
                st.subheader("Delete Student")
                student_to_delete = st.selectbox(
                    "Select student to delete:",
                    options=[s["name"] for s in students]
                )
                
                if st.button("Delete Student", type="secondary"):
                    student_id = next(s["id"] for s in students if s["name"] == student_to_delete)
                    try:
                        del_response = requests.delete(
                            f"{BACKEND_URL}/students/{student_id}",
                            timeout=10
                        )
                        
                        if del_response.status_code == 200:
                            st.success(f"✅ Deleted {student_to_delete}")
                            st.rerun()
                        else:
                            st.error(handle_api_error(del_response))
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        else:
            st.error("Failed to fetch students")
    except Exception as e:
        st.error(f"Error: {str(e)}")

elif choice == "View Attendance":
    st.header("📋 Attendance Records")
    
    col1, col2 = st.columns(2)
    
    with col1:
        date_filter = st.date_input("Filter by Date", value=datetime.now())
    
    with col2:
        try:
            response = requests.get(f"{BACKEND_URL}/students/", timeout=10)
            if response.status_code == 200:
                students = response.json()
                student_names = ["All Students"] + [s["name"] for s in students]
                student_filter = st.selectbox("Filter by Student", student_names)
        except:
            student_filter = "All Students"
    
    try:
        response = requests.get(f"{BACKEND_URL}/attendance/", timeout=10)
        
        if response.status_code == 200:
            attendance_records = response.json()
            
            if not attendance_records:
                st.info("No attendance records found.")
            else:
                df = pd.DataFrame(attendance_records)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                # Apply filters
                if student_filter != "All Students":
                    df = df[df['student_name'] == student_filter]
                
                df_filtered = df[df['timestamp'].dt.date == date_filter]
                
                st.success(f"Total Records: {len(df_filtered)}")
                st.dataframe(df_filtered, use_container_width=True)
                
                # Download option
                csv = df_filtered.to_csv(index=False)
                st.download_button(
                    label="📥 Download as CSV",
                    data=csv,
                    file_name=f"attendance_{date_filter}.csv",
                    mime="text/csv"
                )
        else:
            st.error("Failed to fetch attendance records")
    except Exception as e:
        st.error(f"Error: {str(e)}")

elif choice == "Statistics":
    st.header("📊 Attendance Statistics")
    
    try:
        response = requests.get(f"{BACKEND_URL}/attendance/stats", timeout=10)
        
        if response.status_code == 200:
            stats = response.json()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Students", stats.get("total_students", 0))
            with col2:
                st.metric("Total Attendance", stats.get("total_attendance_records", 0))
            with col3:
                st.metric("Today's Attendance", stats.get("today_attendance", 0))
            with col4:
                st.metric("Avg Attendance Rate", f"{stats.get('average_attendance_rate', 0):.1f}%")
            
            # Charts
            if "daily_attendance" in stats:
                st.subheader("Daily Attendance Trend")
                df = pd.DataFrame(stats["daily_attendance"])
                st.line_chart(df.set_index("date"))
        else:
            st.error("Failed to fetch statistics")
    except Exception as e:
        st.error(f"Error: {str(e)}")

# ========== SYSTEM PAGES ==========

elif choice == "System Health":
    st.header("🔧 System Health Check")
    
    try:
        response = requests.get(f"{BACKEND_URL}/diagnostics", timeout=10)
        
        if response.status_code == 200:
            diagnostics = response.json()
            
            st.subheader("System Status")
            st.success("✅ Backend is healthy")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Face Recognition Service")
                face_service = diagnostics["face_service"]
                st.write(f"**Detection Method:** {face_service['detection_method']}")
                st.write(f"**Model:** {face_service['model']}")
                st.write(f"**Tolerance:** {face_service['tolerance']}")
                st.write(f"**Known Faces:** {face_service['known_faces_count']}")
                if face_service['known_faces']:
                    st.write("**Registered Students:**")
                    for name in face_service['known_faces']:
                        st.write(f"- {name}")
            
            with col2:
                st.subheader("Haar Cascade")
                haar = diagnostics["haar_cascade"]
                if haar['valid']:
                    st.success("✅ Haar Cascade is valid")
                else:
                    st.error("❌ Haar Cascade is invalid")
                st.write(f"**Path:** {haar['path']}")
                st.write(f"**Method:** {haar['configured_method']}")
                
                st.subheader("Storage")
                storage = diagnostics["storage"]
                st.write(f"**Type:** {storage['type']}")
                st.write(f"**Upload Dir:** {storage['upload_dir']}")
            
            st.json(diagnostics)
        else:
            st.error("Failed to fetch diagnostics")
    except Exception as e:
        st.error(f"Error: {str(e)}")

elif choice == "Camera Status":
    st.header("📹 Camera Status")
    
    camera_active, active_sessions = check_camera_status()
    
    if camera_active:
        st.success("🟢 Camera is ACTIVE")
        st.write(f"**Active Sessions:** {active_sessions}")
        
        st.subheader("Live Feed")
        video_url = f"{BACKEND_URL}/live/video/stream"
        st.image(video_url, use_container_width=True)
    else:
        st.warning("⚫ Camera is OFF")
        st.info("Start the camera from the sidebar to view live feed.")
