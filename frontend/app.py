"""
Streamlit frontend for the Student Attendance System.
Enhanced with face recognition, camera support, and comprehensive error handling.
"""
import streamlit as st
import requests
from PIL import Image
import io
import pandas as pd
from datetime import datetime, timedelta
import cv2
import numpy as np

# MUST be the first Streamlit command
st.set_page_config(
    page_title="Student Attendance System",
    page_icon="📚",
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
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">📚 Student Attendance System</div>', unsafe_allow_html=True)

# Sidebar menu
st.sidebar.title("Navigation")
menu = ["Register Student", "Mark Attendance (Manual)", "Mark Attendance (Face Recognition)", "View Attendance", "Statistics", "System Health"]
choice = st.sidebar.selectbox("Select Option", menu)


def check_backend_health():
    """Check if backend is healthy."""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


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

# Page: Register Student
if choice == "Register Student":
    st.header("📝 Register New Student")
    
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
        
        if file:
            image = Image.open(file)
            st.image(image, caption="Uploaded Photo", use_container_width=True)
    
    with col2:
        st.subheader("Registration Guidelines")
        st.info("""
        **Important Guidelines:**
        - Photo should contain only ONE face
        - Face should be clearly visible
        - Good lighting is essential
        - Avoid sunglasses or face coverings
        - Maximum file size: 5MB
        - Supported formats: JPG, JPEG, PNG
        """)
    
    if st.button("✅ Register Student", type="primary"):
        if not name or not name.strip():
            st.error("❌ Please enter student name")
        elif not file:
            st.error("❌ Please upload a photo")
        else:
            with st.spinner("Registering student..."):
                try:
                    files = {"file": (file.name, file.getvalue(), file.type)}
                    data = {"name": name.strip()}
                    response = requests.post(
                        f"{BACKEND_URL}/register/", 
                        data=data, 
                        files=files,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"✅ Student '{result['name']}' registered successfully!")
                        st.balloons()
                        st.json(result)
                    else:
                        error_msg = handle_api_error(response)
                        st.error(f"❌ Registration failed: {error_msg}")
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Network error: {str(e)}")
                except Exception as e:
                    st.error(f"❌ Unexpected error: {str(e)}")

# Page: Mark Attendance (Manual)
elif choice == "Mark Attendance (Manual)":
    st.header("✋ Mark Attendance (Manual Selection)")
    
    try:
        with st.spinner("Loading students..."):
            response = requests.get(f"{BACKEND_URL}/students/", timeout=10)
            
            if response.status_code == 200:
                students = response.json()
                
                if not students:
                    st.warning("⚠️ No students registered yet. Please register students first.")
                else:
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        student_names = [s["name"] for s in students]
                        selected = st.selectbox("Select Student", student_names)
                        
                        if st.button("✅ Mark Present", type="primary"):
                            student_id = [s["id"] for s in students if s["name"] == selected][0]
                            
                            with st.spinner("Marking attendance..."):
                                try:
                                    response = requests.post(
                                        f"{BACKEND_URL}/attendance/", 
                                        params={"student_id": student_id},
                                        timeout=10
                                    )
                                    
                                    if response.status_code == 200:
                                        result = response.json()
                                        st.success(f"✅ Attendance marked for {result['student_name']}!")
                                        st.info(f"Timestamp: {result['timestamp']}")
                                    else:
                                        error_msg = handle_api_error(response)
                                        st.error(f"❌ Failed: {error_msg}")
                                except Exception as e:
                                    st.error(f"❌ Error: {str(e)}")
                    
                    with col2:
                        st.subheader("Student Details")
                        selected_student = [s for s in students if s["name"] == selected][0]
                        st.write(f"**ID:** {selected_student['id']}")
                        st.write(f"**Name:** {selected_student['name']}")
            else:
                error_msg = handle_api_error(response)
                st.error(f"❌ Failed to load students: {error_msg}")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# Page: Mark Attendance (Face Recognition)
elif choice == "Mark Attendance (Face Recognition)":
    st.header("📸 Mark Attendance (Face Recognition)")
    
    st.info("""
    **How it works:**
    1. Upload a photo or take a picture using your camera
    2. The system will automatically detect and recognize faces
    3. Attendance will be marked for recognized students
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Upload Photo")
        uploaded_file = st.file_uploader(
            "Upload photo for recognition", 
            type=["jpg", "jpeg", "png"],
            help="Upload a photo containing student faces"
        )
        
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Photo", use_container_width=True)
            
            if st.button("🔍 Recognize and Mark Attendance", type="primary"):
                with st.spinner("Processing face recognition..."):
                    try:
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                        response = requests.post(
                            f"{BACKEND_URL}/attendance/recognize/",
                            files=files,
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            
                            if result["status"] == "success":
                                st.success(f"✅ Successfully recognized {result['total_recognized']} student(s)!")
                                
                                # Display results in a table
                                df = pd.DataFrame(result["attendance_records"])
                                st.dataframe(df, use_container_width=True)
                                st.balloons()
                            else:
                                st.warning(result.get("message", "No students recognized"))
                        else:
                            error_msg = handle_api_error(response)
                            st.error(f"❌ Recognition failed: {error_msg}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
    
    with col2:
        st.subheader("Camera Capture")
        st.write("Use camera to capture and recognize faces")
        
        camera_photo = st.camera_input("Take a picture")
        
        if camera_photo:
            if st.button("🔍 Process Camera Photo", type="primary"):
                with st.spinner("Processing face recognition..."):
                    try:
                        files = {"file": ("camera.jpg", camera_photo.getvalue(), "image/jpeg")}
                        response = requests.post(
                            f"{BACKEND_URL}/attendance/recognize/",
                            files=files,
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            
                            if result["status"] == "success":
                                st.success(f"✅ Successfully recognized {result['total_recognized']} student(s)!")
                                
                                df = pd.DataFrame(result["attendance_records"])
                                st.dataframe(df, use_container_width=True)
                                st.balloons()
                            else:
                                st.warning(result.get("message", "No students recognized"))
                        else:
                            error_msg = handle_api_error(response)
                            st.error(f"❌ Recognition failed: {error_msg}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

# Page: View Attendance
elif choice == "View Attendance":
    st.header("📊 Attendance Records")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Get all students for filter
        try:
            students_response = requests.get(f"{BACKEND_URL}/students/", timeout=10)
            if students_response.status_code == 200:
                students = students_response.json()
                student_options = ["All Students"] + [s["name"] for s in students]
                selected_student = st.selectbox("Filter by Student", student_options)
            else:
                selected_student = "All Students"
        except:
            selected_student = "All Students"
    
    with col2:
        date_filter = st.date_input("Filter by Date", value=None)
    
    with col3:
        st.write("")  # Spacing
        st.write("")  # Spacing
        refresh = st.button("🔄 Refresh", type="primary")
    
    try:
        with st.spinner("Loading attendance records..."):
            params = {}
            
            if selected_student != "All Students":
                student_id = [s["id"] for s in students if s["name"] == selected_student][0]
                params["student_id"] = student_id
            
            if date_filter:
                params["date"] = date_filter.strftime("%Y-%m-%d")
            
            response = requests.get(
                f"{BACKEND_URL}/attendance/",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                records = response.json()
                
                if not records:
                    st.info("ℹ️ No attendance records found for the selected filters.")
                else:
                    st.success(f"✅ Found {len(records)} attendance record(s)")
                    
                    # Convert to DataFrame for better display
                    df = pd.DataFrame(records)
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df = df.sort_values('timestamp', ascending=False)
                    
                    # Display as table
                    st.dataframe(
                        df[['student_name', 'timestamp']].rename(columns={
                            'student_name': 'Student Name',
                            'timestamp': 'Timestamp'
                        }),
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Download button
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download as CSV",
                        data=csv,
                        file_name=f"attendance_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
            else:
                error_msg = handle_api_error(response)
                st.error(f"❌ Failed to load records: {error_msg}")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# Page: Statistics
elif choice == "Statistics":
    st.header("📈 Attendance Statistics")
    
    try:
        with st.spinner("Loading statistics..."):
            # Get all students
            students_response = requests.get(f"{BACKEND_URL}/students/", timeout=10)
            # Get all attendance records
            attendance_response = requests.get(f"{BACKEND_URL}/attendance/", timeout=10)
            
            if students_response.status_code == 200 and attendance_response.status_code == 200:
                students = students_response.json()
                records = attendance_response.json()
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Students", len(students))
                
                with col2:
                    st.metric("Total Attendance Records", len(records))
                
                with col3:
                    # Calculate today's attendance
                    today = datetime.now().date()
                    today_records = [r for r in records if datetime.fromisoformat(r['timestamp']).date() == today]
                    st.metric("Today's Attendance", len(today_records))
                
                # Attendance by student
                if records:
                    st.subheader("Attendance by Student")
                    df = pd.DataFrame(records)
                    attendance_counts = df['student_name'].value_counts().reset_index()
                    attendance_counts.columns = ['Student Name', 'Attendance Count']
                    st.bar_chart(attendance_counts.set_index('Student Name'))
                    
                    # Recent activity
                    st.subheader("Recent Activity (Last 10 records)")
                    recent_df = pd.DataFrame(records).tail(10)
                    recent_df['timestamp'] = pd.to_datetime(recent_df['timestamp'])
                    st.dataframe(
                        recent_df[['student_name', 'timestamp']].sort_values('timestamp', ascending=False),
                        use_container_width=True,
                        hide_index=True
                    )
            else:
                st.error("❌ Failed to load statistics")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# Page: System Health
elif choice == "System Health":
    st.header("🏥 System Health Check")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Backend Status")
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=5)
            if response.status_code == 200:
                st.success("✅ Backend is healthy")
                health_data = response.json()
                st.json(health_data)
            else:
                st.error("❌ Backend is unhealthy")
        except Exception as e:
            st.error(f"❌ Backend is not responding: {str(e)}")
    
    with col2:
        st.subheader("System Information")
        st.info(f"""
        **Frontend:** Streamlit
        **Backend URL:** {BACKEND_URL}
        **Current Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """)
    
    # Test endpoints
    st.subheader("Endpoint Tests")
    if st.button("🧪 Test All Endpoints"):
        endpoints = {
            "Health Check": "/health",
            "Students List": "/students/",
            "Attendance Records": "/attendance/"
        }
        
        for name, endpoint in endpoints.items():
            try:
                response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=5)
                if response.status_code == 200:
                    st.success(f"✅ {name}: OK")
                else:
                    st.error(f"❌ {name}: Failed (Status {response.status_code})")
            except Exception as e:
                st.error(f"❌ {name}: Error - {str(e)}")

# Footer
st.sidebar.markdown("---")
st.sidebar.info("""
**Student Attendance System v2.0**

Built with:
- FastAPI (Backend)
- Streamlit (Frontend)
- Face Recognition
- SQLite Database

© 2025 All Rights Reserved
""")
