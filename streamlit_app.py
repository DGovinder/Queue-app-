import streamlit as st
import sqlite3
import hashlib
from datetime import datetime, timedelta

# ============================
# DATABASE SETUP
# ============================
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
        surname TEXT,
        place_of_work TEXT,
        practice_number TEXT,
        password_hash TEXT
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

# ============================
# UTILITY FUNCTIONS
# ============================
SPECIAL_CHARS = r"!@#$%^&*()-_=+[{]}\\|;:'\",<.>/?`~"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(password, hashed):
    return hashlib.sha256(password.encode()).hexdigest() == hashed

def password_policy(password):
    if len(password) < 6:
        return False
    if not any(char.isdigit() for char in password):
        return False
    if not any(char in SPECIAL_CHARS for char in password):
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

# ============================
# PATIENT FUNCTIONS
# ============================

def patient_register():
    st.header("Patient Registration")
    full_name = st.text_input("Full Name")
    dob = st.date_input(
        "Date of Birth",
        min_value=datetime(1910, 1, 1).date(),
        max_value=datetime.today().date()
    )
    id_number = st.text_input("ID Number")
    language = st.selectbox("Language", get_languages())
    password = st.text_input("Password", type="password")

    if st.button("Register as Patient"):
        if not full_name or not id_number or not password:
            st.error("Please fill in all fields.")
            return
        if not password_policy(password):
            st.error("Password must be at least 6 characters, include a number and a special character.")
            return

        password_hash = hash_password(password)
        c.execute('INSERT INTO patients (full_name, dob, id_number, language, password_hash) VALUES (?, ?, ?, ?, ?)',
                  (full_name, dob.isoformat(), id_number, language, password_hash))
        conn.commit()
        st.success("Patient registration successful! You can sign in from Home page.")

def patient_sign_in():
    st.header("Patient Sign In")
    id_number = st.text_input("ID Number")
    password = st.text_input("Password", type="password")

    if st.button("Login as Patient"):
        c.execute('SELECT id, password_hash, full_name FROM patients WHERE id_number=?', (id_number,))
        result = c.fetchone()

        if result and check_password(password, result[1]):
            st.session_state["role"] = "patient"
            st.session_state["patient_id"] = result[0]
            st.session_state["patient_name"] = result[2]
            st.success(f"Welcome {result[2]}!")
            st.rerun()
        else:
            st.error("Invalid credentials.")

def patient_dashboard():
    st.header(f"Welcome, {st.session_state['patient_name']}")

    st.subheader("Book Appointment")
    doctors = get_doctors()
    doctor_names = [f"{d[0]} - Dr. {d[1]} {d[2]}" for d in doctors]
    doctor_choice = st.selectbox("Select Doctor", doctor_names)
    date_choice = st.date_input("Appointment Date", min_value=datetime.today().date())
    time_choice = st.time_input("Appointment Time", value=(datetime.now() + timedelta(hours=2)).time())

    if st.button("Book Appointment"):
        doctor_id = int(doctor_choice.split(" - ")[0])
        appt_datetime = datetime.combine(date_choice, time_choice)
        c.execute('INSERT INTO appointments (patient_id, doctor_id, time, status) VALUES (?, ?, ?, ?)',
                  (st.session_state["patient_id"], doctor_id, appt_datetime.isoformat(), "Scheduled"))
        conn.commit()
        st.success("Appointment booked!")

    st.subheader("My Appointments")
    c.execute('''
        SELECT a.id, d.full_name, d.surname, a.time, a.status
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        WHERE a.patient_id=?
    ''', (st.session_state["patient_id"],))
    rows = c.fetchall()
    if rows:
        for r in rows:
            st.info(f"Doctor: Dr. {r[1]} {r[2]} | Time: {r[3]} | Status: {r[4]}")
    else:
        st.write("No appointments yet.")

    st.subheader("My Prescriptions")
    c.execute('SELECT medication, prescribed_on, refill_due FROM prescriptions WHERE patient_id=?',
              (st.session_state["patient_id"],))
    meds = c.fetchall()
    if meds:
        for m in meds:
            st.info(f"Medication: {m[0]} | Prescribed: {m[1]} | Refill Due: {m[2]}")
    else:
        st.write("No prescriptions.")

    st.subheader("Submit Complaint")
    complaint = st.text_area("Describe your complaint")
    if st.button("Submit Complaint"):
        c.execute('INSERT INTO complaints (patient_id, content, submitted_on, status) VALUES (?, ?, ?, ?)',
                  (st.session_state["patient_id"], complaint, datetime.now().isoformat(), "Pending"))
        conn.commit()
        st.success("Complaint submitted.")

    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

# ============================
# DOCTOR FUNCTIONS
# ============================

def doctor_register():
    st.header("Doctor Registration")
    full_name = st.text_input("First Name")
    surname = st.text_input("Surname")
    place_of_work = st.text_input("Place of Work")
    practice_number = st.text_input("13-digit Practice Number")
    password = st.text_input("Password", type="password")

    if st.button("Register as Doctor"):
        if not full_name or not surname or not place_of_work or not practice_number or not password:
            st.error("Please fill in all fields.")
            return
        if len(practice_number) != 13 or not practice_number.isdigit():
            st.error("Practice Number must be 13 digits.")
            return
        if not password_policy(password):
            st.error("Password must be at least 6 characters, include a number and a special character.")
            return

        password_hash = hash_password(password)
        c.execute('INSERT INTO doctors (full_name, surname, place_of_work, practice_number, password_hash) VALUES (?, ?, ?, ?, ?)',
                  (full_name, surname, place_of_work, practice_number, password_hash))
        conn.commit()
        st.success("Doctor registration successful!")

def doctor_sign_in():
    st.header("Doctor Sign In")
    practice_number = st.text_input("Practice Number")
    password = st.text_input("Password", type="password")

    if st.button("Login as Doctor"):
        c.execute('SELECT id, password_hash, full_name FROM doctors WHERE practice_number=?', (practice_number,))
        result = c.fetchone()

        if result and check_password(password, result[1]):
            st.session_state["role"] = "doctor"
            st.session_state["doctor_id"] = result[0]
            st.session_state["doctor_name"] = result[2]
            st.success(f"Welcome Dr. {result[2]}")
            st.rerun()
        else:
            st.error("Invalid credentials.")

def doctor_dashboard():
    st.header(f"Doctor Dashboard - Dr. {st.session_state['doctor_name']}")

    st.subheader("My Appointments")
    c.execute('''
        SELECT a.id, p.full_name, a.time, a.status 
        FROM appointments a 
        JOIN patients p ON a.patient_id = p.id
        WHERE a.doctor_id=?
    ''', (st.session_state["doctor_id"],))
    rows = c.fetchall()
    if rows:
        for r in rows:
            st.info(f"Patient: {r[1]} | Time: {r[2]} | Status: {r[3]}")
            prescribe = st.text_input(f"Prescription for Appointment {r[0]}", key=f"rx_{r[0]}")
            if st.button(f"Prescribe", key=f"btn_{r[0]}"):
                refill_due = datetime.now() + timedelta(days=30)
                c.execute('INSERT INTO prescriptions (patient_id, doctor_id, medication, prescribed_on, refill_due) VALUES (?, ?, ?, ?, ?)',
                          (r[0], st.session_state["doctor_id"], prescribe, datetime.now().isoformat(), refill_due.isoformat()))
                conn.commit()
                st.success("Medication prescribed.")

    else:
        st.write("No appointments yet.")

    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

# ============================
# MAIN
# ============================
st.set_page_config(page_title="KZN Healthcare Queue System", page_icon="💊")
st.title("KZN Public Healthcare Queue Management App")

menu = ["Patient Login", "Patient Register", "Doctor Login", "Doctor Register"]
choice = st.sidebar.selectbox("Navigation", menu)

if "role" not in st.session_state:
    if choice == "Patient Login":
        patient_sign_in()
    elif choice == "Patient Register":
        patient_register()
    elif choice == "Doctor Login":
        doctor_sign_in()
    elif choice == "Doctor Register":
        doctor_register()
else:
    if st.session_state["role"] == "patient":
        patient_dashboard()
    elif st.session_state["role"] == "doctor":
        doctor_dashboard()
