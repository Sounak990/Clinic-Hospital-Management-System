# Arahona Clinic Portal - A Multi-User Clinic Management System

## 1. Overview

Arahona Clinic Portal is a full-stack web application designed to streamline clinical operations by providing a centralized platform for patients, doctors, and administrators. The system features role-based access control (RBAC), ensuring that each user type has access to a dashboard and functionalities tailored to their specific needs.

This application is built with Python using the Streamlit framework for the frontend and SQLAlchemy ORM for database management, demonstrating a modern approach to rapid application development.

---

## 2. Core Features

### Multi-Role Authentication
- **Secure Login:** Separate, secure login portals for Patients, Doctors, and Administrators.
- **Password Security:** User passwords are not stored in plain text. They are securely hashed using the industry-standard `bcrypt` algorithm.
- **Session Management:** User sessions and roles are managed using `st.session_state`, ensuring persistent login status and correct permission handling.

### Patient Portal
- **Self-Registration:** A public-facing form allows new patients to register their details, including name, mobile number, date of birth, and reason for visit.
- **Input Validation:** The registration form includes validation to prevent duplicate entries (based on mobile number) and ensure data integrity.

### Admin Dashboard
The admin has full oversight and control over the clinic's operations.
- **Patient Management:** View a list of all registered patients, see their current status (`Active`/`Completed`), and assign them to doctors. Implements a business rule preventing a patient from being assigned to more than two doctors on the same day.
- **Appointment Management:** Schedule new appointments for any patient with any doctor. The admin also manages appointment cancellation requests submitted by doctors, with the authority to approve or deny them.
- **Doctor Statistics:** A dedicated dashboard to track key performance indicators for each doctor, including their total number of unique assigned patients and total scheduled appointments.
- **Clinic-Wide Calendar:** A high-level monthly calendar view displaying the total number of appointments scheduled per day across the entire clinic.

### Doctor Dashboard
The doctor's portal is designed to manage their daily workflow efficiently.
- **Personalized Dashboard:** Upon login, doctors see a summary of their assigned patients and scheduled appointments for the current day.
- **Patient Interaction:** View a list of all assigned patients, add clinical notes and prescriptions, and officially mark a patient's case as "Completed" after treatment.
- **Appointment Handling:**
  - **Accept Patients:** Formally accept an admin-scheduled appointment by clicking "Add to My Patient List," which creates a `DoctorAssignment` record and moves the patient to their active list.
  - **Request Cancellation:** Submit a cancellation request to the admin with a mandatory reason. The appointment is not cancelled until the admin approves it.

---

## 3. Technical Stack

- **Backend/Frontend Framework:** [Streamlit](https://streamlit.io/)
- **Database:** [SQLite](https://www.sqlite.org/index.html)
- **Object Relational Mapper (ORM):** [SQLAlchemy](https://www.sqlalchemy.org/)
- **Password Hashing:** [bcrypt](https://pypi.org/project/bcrypt/)
- **Core Language:** [Python 3](https://www.python.org/)

---

## 4. Project Structure

The project is organized into modular Python files to separate concerns, improving readability and maintainability.

.
├── app.py # Main application entry point, handles routing and authentication UI.
├── admin_navigation.py # Contains all UI and logic for the Admin dashboard.
├── doctor_navigation.py # Contains all UI and logic for the Doctor dashboard.
├── your-background.jpg # Static asset for the UI background.
├── requirements.txt # Lists all Python package dependencies.
└── clinic.db # SQLite database file (auto-generated on first run).

text

---

## 5. Database Schema

The application uses a relational database model managed by SQLAlchemy ORM. The schema is designed to ensure data integrity and efficiently model clinical relationships.

- **`User`**: Stores login credentials (`username`, `password_hash`) and `role` (Admin, Doctor).
- **`Patient`**: Stores patient-specific information (`name`, `mobile`, `dob`, `status`, `prescriptions`).
- **`Appointment`**: Links a `Patient` to a `Doctor` for a specific `date` and `time`. It holds the status of the appointment (`Scheduled`, `Cancelled`, etc.).
- **`DoctorAssignment`**: A crucial link table that formally assigns a `Patient` to a `Doctor` for a given day. This is the basis for the doctor's "My Patients" list.

Relationships are managed using SQLAlchemy's `relationship` and `ForeignKey` constructs to enforce referential integrity.

---

## 6. Setup and Installation

**Prerequisites:** Python 3.8+

**1. Clone the repository (Example):**
git clone https://github.com/your-username/clinic-management-system.git
cd clinic-management-system

text

**2. Create and activate a virtual environment:**
For Windows
python -m venv venv
.\venv\Scripts\activate

For macOS/Linux
python3 -m venv venv
source venv/bin/activate

text

**3. Install dependencies:**
pip install -r requirements.txt

text

**4. Run the application:**
streamlit run app.py

text

**Important Note:** The `clinic.db` file is created automatically on the first run. If you make any changes to the database models in the Python files (e.g., adding a new column), you must **delete the existing `clinic.db` file** and restart the application to allow the new schema to be created.
