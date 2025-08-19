import streamlit as st
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine, Column, Integer, String, Date, Time, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

# --- Database Setup (Must match other files) ---
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
def apply_doctor_styling():
    st.markdown("""
        <style>
        div[data-testid="stBlock"], div[data-testid="stExpander"] {
            background-color: rgba(136, 150, 213, 0.9);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 10px; padding: 1rem; margin-bottom: 1rem;
        }
        div[data-testid="stExpander"] summary p { font-weight: bold; color: white; }
        .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp label, .stApp li { color: white; }
        </style>
    """, unsafe_allow_html=True)

# --- Dashboard Page ---
def show_doctor_overview(doctor_name):
    st.header("Today's Dashboard")
    session = SessionLocal()
    today = datetime.today().date()
    
    with st.container(border=True):
        st.subheader("Assigned Patients for Today")
        assigned_patient_ids = [a.patient_id for a in session.query(DoctorAssignment).filter_by(doctor_name=doctor_name, assignment_date=today).all()]
        if assigned_patient_ids:
            patients_today = session.query(Patient).filter(Patient.id.in_(assigned_patient_ids), Patient.status == "Active").all()
            if patients_today:
                for p in patients_today:
                    st.write(f"- {p.name} ({p.mobile})")
            else:
                st.info("No active patients assigned for today.")
        else:
            st.info("No patients assigned for today.")

    with st.container(border=True):
        st.subheader("Scheduled Appointments for Today")
        appointments_today = session.query(Appointment).filter(Appointment.doctor_name == doctor_name, Appointment.date == today, Appointment.status == "Scheduled").order_by(Appointment.time).all()
        if appointments_today:
            for appt in appointments_today:
                st.write(f"- {appt.patient.name} at {appt.time.strftime('%I:%M %p')}")
        else:
            st.info("No appointments scheduled for today.")
    session.close()

# --- "My Patients" Page ---
def manage_my_patients(doctor_name):
    st.header("My Active Patients")
    session = SessionLocal()
    assigned_ids = {a.patient_id for a in session.query(DoctorAssignment).filter_by(doctor_name=doctor_name).all()}
    active_patients = session.query(Patient).filter(Patient.id.in_(assigned_ids), Patient.status == "Active").order_by(Patient.name).all()

    if not active_patients:
        st.info("You have no active patients assigned. Go to 'My Appointments' to add patients to your list.")
    else:
        for p in active_patients:
            with st.container(border=True):
                st.subheader(p.name)
                col1, col2 = st.columns(2)
                col1.text(f"Mobile: {p.mobile}")
                col2.text(f"Status: {p.status}")

                with st.expander("📝 Add Prescription / Notes"):
                    notes = st.text_area("Clinical Notes & Prescription", value=(p.prescriptions or ""), key=f"notes_{p.id}")
                    if st.button("Save Notes", key=f"save_{p.id}"):
                        p.prescriptions = notes
                        session.commit()
                        st.success(f"Notes for {p.name} saved!")
                        st.rerun()

                if st.session_state.get(f'confirm_complete_{p.id}'):
                    st.warning(f"Are you sure you want to mark {p.name}'s case as completed?")
                    c1, c2 = st.columns(2)
                    if c1.button("✅ Yes, Complete", key=f"yes_complete_{p.id}", type="primary"):
                        p.status = "Completed"
                        session.commit()
                        st.success(f"{p.name} marked as completed.")
                        del st.session_state[f'confirm_complete_{p.id}']
                        st.rerun()
                    if c2.button("❌ No, Cancel", key=f"no_complete_{p.id}"):
                        del st.session_state[f'confirm_complete_{p.id}']
                        st.rerun()
                else:
                    if st.button("Mark as Completed", key=f"complete_{p.id}"):
                        st.session_state[f'confirm_complete_{p.id}'] = True
                        st.rerun()
    session.close()

# --- "My Appointments" Page (MODIFIED) ---
def manage_my_appointments(doctor_name):
    st.header("My Appointments")
    session = SessionLocal()
    
    appointments = session.query(Appointment).filter(
        Appointment.doctor_name == doctor_name,
        Appointment.status.in_(["Scheduled", "Cancellation Requested"])
    ).order_by(Appointment.date, Appointment.time).all()
    
    if not appointments:
        with st.container(border=True):
            st.info("You have no pending appointments scheduled by the admin.")
    else:
        for appt in appointments:
            with st.container(border=True):
                st.subheader(f"{appt.patient.name} on {appt.date.strftime('%d %b, %Y')} at {appt.time.strftime('%I:%M %p')}")
                st.write(f"**Reason:** {appt.reason} | **Status:** {appt.status}")

                if appt.status == "Scheduled":
                    # --- Logic for the two main actions: Add Patient or Cancel ---
                    col1, col2 = st.columns(2)

                    # Button to formally add the patient to the doctor's list
                    with col1:
                        assignment_exists = session.query(DoctorAssignment).filter_by(
                            patient_id=appt.patient_id,
                            doctor_name=doctor_name,
                            assignment_date=appt.date
                        ).first()
                        
                        if not assignment_exists:
                            if st.button("✅ Add to My Patient List", key=f"add_patient_{appt.id}"):
                                new_assignment = DoctorAssignment(
                                    patient_id=appt.patient_id,
                                    doctor_name=doctor_name,
                                    assignment_date=appt.date
                                )
                                session.add(new_assignment)
                                session.commit()
                                st.success(f"{appt.patient.name} has been added to your patient list.")
                                st.rerun()
                        else:
                            st.success("Patient is already on your list for this day.")

                    # Expander to request cancellation
                    with col2:
                        with st.expander("Request to Cancel"):
                            with st.form(key=f"cancel_form_{appt.id}"):
                                reason = st.text_area("Reason for cancellation", key=f"reason_{appt.id}", height=100)
                                if st.form_submit_button("Submit Request", type="primary"):
                                    if reason:
                                        appt.status = "Cancellation Requested"
                                        appt.cancellation_reason = reason
                                        session.commit()
                                        st.success("Cancellation request sent to admin.")
                                        st.rerun()
                                    else:
                                        st.error("A reason is required to request cancellation.")
    session.close()

# --- Main Navigation Function ---
def show_doctor_dashboard():
    apply_doctor_styling()
    doctor_name = st.session_state.get("username", "")
    st.sidebar.title(f"👨‍⚕️ Dr. {doctor_name.split('Dr. ')[-1]}'s Portal")
    
    if st.session_state.get('logout_flow_doctor', False):
        st.sidebar.warning("Are you sure?")
        c1, c2 = st.sidebar.columns(2)
        if c1.button("Yes, Logout", key="confirm_doc_logout", type="primary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        if c2.button("No, Stay", key="cancel_doc_logout"):
            st.session_state.logout_flow_doctor = False
            st.rerun()
    else:
        nav_options = ["Dashboard", "My Patients", "My Appointments"]
        selected = st.sidebar.radio("Menu", nav_options, key="doctor_nav")
        st.sidebar.markdown("---")
        if st.sidebar.button("🔒 Logout", key="doctor_logout_start"):
            st.session_state.logout_flow_doctor = True
            st.rerun()
        
        if selected == "Dashboard":
            show_doctor_overview(doctor_name)
        elif selected == "My Patients":
            manage_my_patients(doctor_name)
        elif selected == "My Appointments":
            manage_my_appointments(doctor_name)
