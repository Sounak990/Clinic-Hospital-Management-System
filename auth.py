import streamlit as st
import bcrypt
from db import SessionLocal, User

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

def ensure_demo_user():
    db = SessionLocal()
    # Remove old demo user if exists for clarity
    old_user = db.query(User).filter_by(username="abc").first()
    if old_user:
        db.delete(old_user)
        db.commit()
    # Ensure demo Doctor and Admin users exist
    for username in ["Sounak Santra Doctor", "Sounak Santra Admin"]:
        if not db.query(User).filter_by(username=username).first():
            user = User(username=username, password_hash=hash_password("Sounak@4"))
            db.add(user)
            db.commit()
    db.close()

def login(role=None):
    ensure_demo_user()

    st.title("Arahona Clinic Management Login")

    if role not in ["Doctor", "Admin"]:  # fallback UI, but expected to pass role
        role = st.selectbox("Login as", ["Doctor", "Admin"])
    else:
        st.write(f"Logging in as **{role}**")

    username = st.text_input("Username", value="Sounak Santra")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        db = SessionLocal()
        full_username = f"{username} {role}"
        user = db.query(User).filter_by(username=full_username).first()
        if user and verify_password(password, user.password_hash):
            st.session_state["user"] = full_username
            st.session_state["role"] = role
            st.success(f"Login successful as {role}!")
            st.experimental_rerun()
        else:
            st.error("Invalid credentials or role mismatch.")
        db.close()
