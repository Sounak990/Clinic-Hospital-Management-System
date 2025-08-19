# app.py

import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Date, Text, Time, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import datetime, date, timedelta # Import timedelta
import bcrypt
import base64
import os
import time


# --- Import Navigation Modules ---
# Ensure these files (admin_navigation.py, doctor_navigation.py) exist in your project folder.
from admin_navigation import show_admin_navigation
from doctor_navigation import show_doctor_dashboard


# --- Database Setup (Consistent across all files) ---
DB_URL = "sqlite:///clinic.db"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- Database Models (The "Single Source of Truth") ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)


class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    mobile = Column(String(20), unique=True, nullable=False)
    dob = Column(Date, nullable=True)
    reason_to_visit = Column(Text) # Added as per your request
    status = Column(String, default="Active")
    prescriptions = Column(Text)


    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    doctor_assignments = relationship("DoctorAssignment", back_populates="patient", cascade="all, delete-orphan")


class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.id'))
    doctor_name = Column(String(100), nullable=False)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    reason = Column(Text)
    status = Column(String, default="Scheduled")
    cancellation_reason = Column(Text)
    patient = relationship("Patient", back_populates="appointments")


class DoctorAssignment(Base):
    __tablename__ = "doctor_assignments"
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.id'))
    doctor_name = Column(String(100), nullable=False)
    assignment_date = Column(Date, default=datetime.today().date(), nullable=False)
    patient = relationship("Patient", back_populates="doctor_assignments")


# --- Create Database Tables ---
Base.metadata.create_all(bind=engine)


# --- UI & Styling Configuration ---
def set_page_config_and_style():
    """Sets page config and injects CSS for styling based on your request."""
    st.set_page_config(page_title="Arahona Clinic Portal", layout="wide")


    bg_path = os.path.join(os.path.dirname(__file__), 'your-background.jpg')
    if os.path.exists(bg_path):
        with open(bg_path, "rb") as f:
            img_data = base64.b64encode(f.read()).decode()
        bg_style = f'background-image: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url("data:image/jpg;base64,{img_data}");'
    else:
        st.warning("Background image 'your-background.jpg' not found. Using fallback.")
        bg_style = "background: linear-gradient(to right, #2c3e50, #4ca1af);"


    st.markdown(f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap');
            
            .stApp {{
                {bg_style}
                background-size: cover;
                background-position: center;
                background-attachment: fixed;
            }}
            
            /* Center the main content */
            [data-testid="stAppViewContainer"] > .main {{
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                padding: 2rem;
            }}


            /* Login/Register Form Container Styling */
            .form-container {{
                background-color: rgba(136, 150, 213, 0.9) !important;
                border: 1px solid rgba(255, 255, 255, 0.2);
                padding: 2.5rem;
                border-radius: 15px;
                width: 100%;
                max-width: 550px;
                margin: auto;
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            }}


            h1, h2, .welcome-text, label, .st-emotion-cache-1y4p8pa, .stRadio > label {{
                font-family: 'Montserrat', sans-serif;
                color: #FFFFFF !important;
                text-align: center;
            }}


            h1 {{ margin-bottom: 0.5rem; }}
            .welcome-text {{ font-size: 1.2rem; margin-bottom: 2rem; }}


            /* Input fields styling */
            [data-testid="stTextInput"] input, 
            [data-testid="stTextArea"] textarea,
            [data-testid="stDateInput"] input,
            [data-testid="stSelectbox"] div[data-baseweb="select"] > div {{
                background-color: rgba(255, 255, 255, 0.2) !important;
                color: #FFFFFF !important;
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.5);
            }}


            /* Button Styling */
            [data-testid="stButton"] button {{
                background-color: #4a5bbf !important;
                color: white !important;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                width: 100%;
                font-weight: 600;
                font-family: 'Montserrat', sans-serif;
            }}
             [data-testid="stButton"] button:hover {{
                background-color: #3a4aaf !important;
            }}
        </style>
    """, unsafe_allow_html=True)


# --- Database Seeding ---
def init_db():
    """Initializes the database with default users if they don't exist."""
    session = SessionLocal()
    if not session.query(User).filter_by(username="admin").first():
        hashed_pw = bcrypt.hashpw("Admin@123".encode(), bcrypt.gensalt())
        session.add(User(username="admin", password_hash=hashed_pw.decode(), role="Admin"))
    
    doctors = ["Dr. Das", "Dr. Santra", "Dr. Banarjee", "Dr. Ghosh"]
    for doctor in doctors:
        if not session.query(User).filter_by(username=doctor).first():
            hashed_pw = bcrypt.hashpw("@123".encode(), bcrypt.gensalt())
            session.add(User(username=doctor, password_hash=hashed_pw.decode(), role="Doctor"))
    
    session.commit()
    session.close()


# --- Authentication & Registration Page ---
def show_auth_page():
    """Displays a single page for login and registration."""
    st.markdown("<h1>Arahona Clinic Portal</h1>", unsafe_allow_html=True)
    st.markdown("<p class='welcome-text'>Your trusted healthcare partner</p>", unsafe_allow_html=True)


    # Wrap the form selector in the custom container
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    
    role = st.radio("Who are you?", ("Patient", "Doctor", "Admin"), horizontal=True, key="role_selector")


    # --- Patient Registration Form ---
    if role == "Patient":
        st.markdown("<h2>Patient Registration</h2>", unsafe_allow_html=True)
        with st.form("patient_registration_form"):
            name = st.text_input("Full Name", placeholder="e.g., Jane Doe")
            mobile = st.text_input("Mobile Number", placeholder="e.g., 9876543210")
            
            # --- MODIFIED: DOB restricted to current day and 30 days prior ---
            today = date.today()
            dob = st.date_input(
                "Date of Birth", 
                min_value=today - timedelta(days=30), # Minimum date is 30 days ago
                max_value=today,                    # Maximum date is today
                value=None
            )
            
            reason = st.text_area("Reason for Visit", placeholder="e.g., General check-up, fever, etc.") # Added field


            if st.form_submit_button("Register"):
                if not all([name, mobile, dob, reason]):
                    st.error("Please fill all fields.")
                else:
                    with st.spinner("Processing registration..."):
                        session = SessionLocal()
                        try:
                            if session.query(Patient).filter_by(mobile=mobile.strip()).first():
                                st.error("This mobile number is already registered.")
                            else:
                                new_patient = Patient(
                                    name=name.strip(), 
                                    mobile=mobile.strip(), 
                                    dob=dob, 
                                    reason_to_visit=reason.strip()
                                )
                                session.add(new_patient)
                                session.commit()
                                st.success("Registration Successful! An admin will contact you shortly.", icon="✅")
                                time.sleep(3)
                        finally:
                            session.close()


    # --- Login Forms ---
    else: # Doctor or Admin
        st.markdown(f"<h2>{role} Login</h2>", unsafe_allow_html=True)
        with st.form(f"{role.lower()}_login_form"):
            if role == "Doctor":
                username = st.selectbox("Select Doctor", ["Dr. Das", "Dr. Santra", "Dr. Banarjee", "Dr. Ghosh"])
                password = st.text_input("Password", type="password")
            else: # Admin
                username = st.text_input("Admin Username", value="admin")
                password = st.text_input("Admin Password", type="password")
            
            if st.form_submit_button(f"Login as {role}"):
                with st.spinner("Verifying..."):
                    session = SessionLocal()
                    user = session.query(User).filter_by(username=username, role=role).first()
                    session.close()
                    if user and bcrypt.checkpw(password.encode(), user.password_hash.encode()):
                        st.session_state.update({"login_status": True, "username": username, "role": role})
                        st.rerun()
                    else:
                        st.error("Invalid credentials. Please try again.")


    st.markdown('</div>', unsafe_allow_html=True)


# --- Main Application Flow ---
def main():
    set_page_config_and_style()
    init_db()


    if not st.session_state.get("login_status", False):
        show_auth_page()
    else:
        # If logged in, show the appropriate dashboard
        if st.session_state.role == "Admin":
            show_admin_navigation()
        elif st.session_state.role == "Doctor":
            show_doctor_dashboard()


if __name__ == "__main__":
    main()
