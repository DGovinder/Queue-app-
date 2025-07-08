# streamlit_app.py

import streamlit as st
import sqlite3
import bcrypt
from datetime import datetime, timedelta

# ================= DB SETUP ==================
conn = sqlite3.connect('queue_system.db', check_same_thread=False)
c = conn.cursor()

def create_tables():
    c.execute('''
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT,
        dob TEXT,
        id_number TEXT,
        language TEXT,
        password_hash TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT,
        specialization TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        doctor_id INTEGER,
        time TEXT,
        status TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS prescriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        doctor_id INTEGER,
        medication TEXT,
        prescribed_on TEXT,
        refill_due TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        content TEXT,
        submitted_on TEXT,
        status TEXT
    )
    ''')

    conn.commit()

create_tables()

# ================= UTILS ==================
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

def password_policy(password):
    if len(password) < 6:
        return False
    if not any(char.isdigit() for char in password):
        return False
    if not any(char in "!@#$%^&*()-_=+[{]}\|;:'\",<.>/?`~" for char in password):
        return False
    return True

def get_languages():
    return [
        "English", "Afrikaans", "isiNdebele", "isiXhosa", "isiZulu", 
        "Sepedi", "Sesotho", "Setswana", "siSwati", "Tshivenḓa", "Xitsonga"
    ]

def get_doctors():
    c.execute("SELECT * FROM doctors")
    return c.fetchall()

def add_random_doctors():
    c.execute("SELECT COUNT(*) FROM doctors")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO doctors (full_name, specialization) VALUES (?, ?)", ("Dr. John Khumalo", "General Practitioner"))
        c.execute("INSERT INTO doctors (full_name, specialization) VALUES (?, ?)", ("Dr. Mary Naidoo", "Family Doctor"))
        conn.commit()

add_random_doctors()

# ================= APP PAGES ==================

def register():
    st.header("Patient Registration")
    full_name = st.text_input("Full Name")
    dob = st.date_input("Date of Birth")
    id_number = st.text_input("ID Number")
    language = st.selectbox("Language", get_languages())
    password = st.text_input("Password", type="password")

    if st.button("Register"):
        if not password_policy(password):
            st.error("Password must be at least 6 characters, include a number and a special character.")
            return

        password_hash = hash_password(password)
        c.execute('INSERT INTO patients (full_name, dob, id_number, language, password_hash) VALUES (?, ?, ?, ?, ?)',
                  (full_name, dob.isoformat(), id_number, language, password_hash))
        conn.commit()
        st.success("Registration successful! Please sign in.")

def sign_in():
    st.header("Sign In")
    id_number = st.text_input("ID Number")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        c.execute('SELECT id, password_hash, full_name FROM patients WHERE id_number=?', (id_number,))
        result = c.fetchone()

        if result and check_password(password, result[1]):
            st.session_state["patient_id"] = result[0]
            st.session_state["patient_name"] = result[2]
            st.success(f"Welcome {result[2]}!")
        else:
            st.error("Invalid credentials.")

def dashboard():
    st.header(f"Welcome, {st.session_state['patient_name']}!")

    # Appointments
    st.subheader("My Appointments")
    c.execute("SELECT a.id, d.full_name, a.time, a.status FROM appointments a JOIN doctors d ON a.doctor_id = d.id WHERE a.patient_id=?", (st.session_state["patient_id"],))
    rows = c.fetchall()
    for r in rows:
        st.text(f"Doctor: {r[1]}, Time: {r[2]}, Status: {r[3]}")

    st.subheader("Book New Appointment")
    doctors = get_doctors()
    doctor_choice = st.selectbox("Choose Doctor", [f"{d[0]} - {d[1]}" for d in doctors] + ["Random Doctor"])
    if st.button("Get Available Slots"):
        slot_time = datetime.now() + timedelta(days=1, hours=2)
        doctor_id = None
        if doctor_choice != "Random Doctor":
            doctor_id = int(doctor_choice.split(" - ")[0])
        else:
            doctor_id = doctors[0][0]

        c.execute('INSERT INTO appointments (patient_id, doctor_id, time, status) VALUES (?, ?, ?, ?)',
                  (st.session_state["patient_id"], doctor_id, slot_time.isoformat(), "Scheduled"))
        conn.commit()
        st.success("Appointment booked!")

    # Prescriptions
    st.subheader("My Prescribed Medications")
    c.execute("SELECT medication, prescribed_on, refill_due FROM prescriptions WHERE patient_id=?", (st.session_state["patient_id"],))
    meds = c.fetchall()
    for m in meds:
        st.text(f"{m[0]} | Prescribed on: {m[1]} | Refill due: {m[2]}")

    # Complaints
    st.subheader("Submit Complaint")
    complaint = st.text_area("Describe your complaint")
    if st.button("Submit Complaint"):
        c.execute('INSERT INTO complaints (patient_id, content, submitted_on, status) VALUES (?, ?, ?, ?)',
                  (st.session_state["patient_id"], complaint, datetime.now().isoformat(), "Pending"))
        conn.commit()
        st.success("Complaint submitted.")

# ================= MAIN ==================

st.title("KZN Public Healthcare Queue Management")

menu = ["Home", "Register"]
choice = st.sidebar.selectbox("Navigation", menu)

if "patient_id" not in st.session_state:
    if choice == "Home":
        sign_in()
    elif choice == "Register":
        register()
else:
    dashboard()
