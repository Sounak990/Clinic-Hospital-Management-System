import streamlit as st
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine, Column, Integer, String, Date, Time, Text, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta
import calendar
import time

# --- Database Setup ---
DB_URL = "sqlite:///clinic.db"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- ORM Models (Consistent with other files) ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    mobile = Column(String(20), unique=True, nullable=False)
    dob = Column(Date)
    reason_to_visit = Column(Text)
    status = Column(String, default="Active")
    prescriptions = Column(Text)
    
    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    doctor_assignments = relationship("DoctorAssignment", back_populates="patient", cascade="all, delete-orphan")

class DoctorAssignment(Base):
    __tablename__ = "doctor_assignments"
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.id'))
    doctor_name = Column(String(100), nullable=False)
    assignment_date = Column(Date, default=datetime.today().date(), nullable=False)
    patient = relationship("Patient", back_populates="doctor_assignments")

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

Base.metadata.create_all(bind=engine)


# --- UI Styling ---
def apply_admin_styling():
    st.markdown("""
        <style>
        div[data-testid="stBlock"], div[data-testid="stExpander"] {
            background-color: rgba(136, 150, 213, 0.9);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 10px; padding: 1rem; margin-bottom: 1rem;
        }
        div[data-testid="stExpander"] summary p { font-weight: bold; color: white; }
        div[data-testid="stMetric"] { background-color: transparent; color: white !important; }
        div[data-testid="stMetric"] * { color: white !important; }
        .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp label, .stApp li { color: white; }
        </style>
    """, unsafe_allow_html=True)


# --- Doctor Statistics Page ---
def show_doctor_statistics():
    st.header("📊 Doctor Statistics")
    session = SessionLocal()
    doctors = session.query(User).filter_by(role="Doctor").all()

    for doctor in doctors:
        with st.container(border=True):
            st.subheader(doctor.username)
            total_patients = session.query(func.count(func.distinct(DoctorAssignment.patient_id))).filter_by(doctor_name=doctor.username).scalar()
            total_appointments = session.query(Appointment).filter_by(doctor_name=doctor.username).count()
            col1, col2 = st.columns(2)
            col1.metric("Total Unique Patients Assigned", total_patients or 0)
            col2.metric("Total Appointments Scheduled", total_appointments or 0)
    session.close()


# --- Monthly Calendar Page ---
def show_dashboard_calendar():
    st.header("📅 Monthly Calendar")
    session = SessionLocal()
    today = datetime.now()
    year, month = today.year, today.month
    with st.container(border=True):
        st.subheader(f"Clinic-Wide Metrics for {calendar.month_name[month]} {year}")
        start_of_month = datetime(year, month, 1)
        end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        appointments = session.query(Appointment).filter(Appointment.date.between(start_of_month.date(), end_of_month.date())).all()
        week_start = today - timedelta(days=today.weekday())
        weekly_appts = sum(1 for appt in appointments if week_start.date() <= appt.date <= today.date())
        col1, col2 = st.columns(2)
        col1.metric("Appointments This Week (All Doctors)", weekly_appts)
        col2.metric("Appointments This Month (All Doctors)", len(appointments))
    session.close()


# --- Patient Management Page ---
def manage_patients_and_assignments():
    st.header("🧑‍🤝‍🧑 Patient Management & Assignment")
    session = SessionLocal()
    patients = session.query(Patient).order_by(Patient.name).all()
    doctors = [user.username for user in session.query(User).filter_by(role="Doctor").all()]
    if not patients:
        with st.container(border=True): st.info("No patients found in the system.")
    else:
        for patient in patients:
            with st.container(border=True):
                col1, col2 = st.columns([2, 1])
                col1.subheader(f"{patient.name}")
                col1.text(f"Mobile: {patient.mobile} | Status: {patient.status}")
                assignments_today = session.query(DoctorAssignment).filter_by(patient_id=patient.id, assignment_date=datetime.today().date()).all()
                assigned_doctors_today = [a.doctor_name for a in assignments_today]
                col1.info(f"Assigned Today: {', '.join(assigned_doctors_today) if assigned_doctors_today else 'None'}")
                with col2.form(key=f"assign_form_{patient.id}"):
                    selected_doctor = st.selectbox("Assign Doctor", options=[""] + doctors, key=f"doc_{patient.id}", label_visibility="collapsed")
                    if st.form_submit_button("Assign"):
                        if selected_doctor:
                            if len(assigned_doctors_today) >= 2:
                                st.error("Limit Reached: Max 2 doctors per day.")
                            elif selected_doctor in assigned_doctors_today:
                                st.warning(f"{selected_doctor} is already assigned.")
                            else:
                                session.add(DoctorAssignment(patient_id=patient.id, doctor_name=selected_doctor))
                                session.commit()
                                # ** MODIFIED: Custom notification **
                                st.toast(f"Success! {patient.name} assigned to {selected_doctor}.", icon="✅")
                                time.sleep(1) # Pause to let user see the toast
                                st.rerun()
    session.close()

# --- Appointment Management Page ---
def manage_appointments():
    st.header("🗓️ Appointment Management")
    session = SessionLocal()
    with st.expander("Create New Appointment"):
        with st.form("new_appt_form"):
            patients = session.query(Patient).all()
            doctors = [user.username for user in session.query(User).filter_by(role="Doctor").all()]
            patient_map = {f"{p.name} ({p.mobile})": p.id for p in patients}
            selected_patient_key = st.selectbox("Select Patient", options=list(patient_map.keys()))
            selected_doctor_name = st.selectbox("Select Doctor", options=doctors)
            appt_date = st.date_input("Appointment Date", min_value=datetime.today())
            appt_time = st.time_input("Appointment Time", value=datetime.now().time())
            reason = st.text_area("Reason for Visit")
            if st.form_submit_button("Schedule Appointment"):
                if selected_patient_key:
                    patient_id = patient_map[selected_patient_key]
                    session.add(Appointment(patient_id=patient_id, doctor_name=selected_doctor_name, date=appt_date, time=appt_time, reason=reason))
                    session.commit()
                    # ** MODIFIED: Custom notification **
                    st.toast(f"Appointment for {selected_patient_key} scheduled successfully!", icon="🗓️")
                    time.sleep(1)
                    st.rerun()
                    
    st.subheader("Pending Cancellation Requests")
    cancellation_requests = session.query(Appointment).filter_by(status="Cancellation Requested").all()
    if not cancellation_requests:
        with st.container(border=True): st.info("No pending cancellation requests.")
    else:
        for appt in cancellation_requests:
            with st.container(border=True):
                st.write(f"**Patient:** {appt.patient.name} | **Doctor:** {appt.doctor_name}")
                st.warning(f"**Reason for Cancellation:** {appt.cancellation_reason}")
                col1, col2 = st.columns(2)
                if col1.button("✅ Approve", key=f"approve_{appt.id}"):
                    appt.status = "Cancelled"
                    session.commit()
                    # ** MODIFIED: Custom notification **
                    st.toast(f"Cancellation approved for {appt.patient.name}.", icon="👍")
                    time.sleep(1)
                    st.rerun()
                if col2.button("❌ Deny", key=f"deny_{appt.id}"):
                    appt.status = "Scheduled"
                    appt.cancellation_reason = None
                    session.commit()
                    # ** MODIFIED: Custom notification **
                    st.toast(f"Cancellation request for {appt.patient.name} was denied.", icon="❌")
                    time.sleep(1)
                    st.rerun()
    session.close()


# --- Main Admin Navigation Function ---
def show_admin_navigation():
    apply_admin_styling()
    st.sidebar.title("👨‍⚕️ Admin Panel")
    
    if st.session_state.get('logout_flow_active', False):
        st.sidebar.warning("Are you sure?")
        c1, c2 = st.sidebar.columns(2)
        if c1.button("Yes, Logout", key="confirm_logout", type="primary"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()
        if c2.button("No, Stay", key="cancel_logout"):
            st.session_state.logout_flow_active = False; st.rerun()
    else:
        nav_options = ["Patient Management", "Appointment Management", "Doctor Statistics", "Monthly Calendar"]
        selected = st.sidebar.radio("Menu", nav_options, key="admin_nav")
        st.sidebar.markdown("---")
        if st.sidebar.button("🔒 Logout", key="admin_logout_start"):
            st.session_state.logout_flow_active = True; st.rerun()
            
        if selected == "Patient Management": manage_patients_and_assignments()
        elif selected == "Appointment Management": manage_appointments()
        elif selected == "Doctor Statistics": show_doctor_statistics()
        elif selected == "Monthly Calendar": show_dashboard_calendar()
