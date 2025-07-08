import streamlit as st
import sqlite3
import hashlib
from datetime import datetime, timedelta

# =========================
# DATABASE CONNECTION
# =========================
conn = sqlite3.connect('queue_system.db', check_same_thread=False)
c = conn.cursor()

# =========================
# DATABASE CREATION
# =========================
def create_tables():
    c.execute('''CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT,
        dob TEXT,
        id_number TEXT,
        language TEXT,
        password_hash TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT,
        surname TEXT,
        place_of_work TEXT,
        practice_number TEXT,
        password_hash TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        doctor_id INTEGER,
        time TEXT,
        status TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS prescriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        doctor_id INTEGER,
        medication TEXT,
        prescribed_on TEXT,
        refill_due TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        content TEXT,
        submitted_on TEXT,
        status TEXT
    )''')
    conn.commit()

create_tables()

# =========================
# UTILS
# =========================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(password, hashed):
    return hashlib.sha256(password.encode()).hexdigest() == hashed

def password_policy(password):
    special = "!@#$%^&*()-_=+[{]}\\|;:'\",<.>/?`~"
    return (
        len(password) >= 6
        and any(char.isdigit() for char in password)
        and any(char in special for char in password)
    )

def get_languages():
    return ["English", "Afrikaans", "isiNdebele", "isiXhosa", "isiZulu",
            "Sepedi", "Sesotho", "Setswana", "siSwati", "Tshivenẓa", "Xitsonga"]

def get_doctors():
    c.execute("SELECT * FROM doctors")
    return c.fetchall()

# =========================
# PAGES
# =========================
def patient_register():
    st.title("Patient Registration")
    name = st.text_input("Full Name")
    dob = st.date_input("Date of Birth", min_value=datetime(1910, 1, 1).date(), max_value=datetime.today().date())
    id_number = st.text_input("ID Number")
    language = st.selectbox("Language", get_languages())
    password = st.text_input("Password", type="password")

    if st.button("Register"):
        if not password_policy(password):
            st.error("Password must have at least 6 characters, a number and a special character.")
        else:
            hashed = hash_password(password)
            c.execute("INSERT INTO patients (full_name, dob, id_number, language, password_hash) VALUES (?, ?, ?, ?, ?)",
                      (name, dob.isoformat(), id_number, language, hashed))
            conn.commit()
            st.success("Patient registered successfully!")

def patient_login():
    st.title("Patient Login")
    id_number = st.text_input("ID Number")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        c.execute("SELECT id, full_name, password_hash FROM patients WHERE id_number=?", (id_number,))
        data = c.fetchone()
        if data and check_password(password, data[2]):
            st.session_state.user_role = "patient"
            st.session_state.user_id = data[0]
            st.session_state.user_name = data[1]
            st.experimental_rerun()
        else:
            st.error("Invalid credentials.")

def doctor_register():
    st.title("Doctor Registration")
    first_name = st.text_input("First Name")
    surname = st.text_input("Surname")
    work = st.text_input("Place of Work")
    practice = st.text_input("13-digit Practice Number")
    password = st.text_input("Password", type="password")

    if st.button("Register"):
        if len(practice) != 13 or not practice.isdigit():
            st.error("Practice number must be 13 digits.")
        elif not password_policy(password):
            st.error("Password must have at least 6 characters, a number and a special character.")
        else:
            hashed = hash_password(password)
            c.execute("INSERT INTO doctors (first_name, surname, place_of_work, practice_number, password_hash) VALUES (?, ?, ?, ?, ?)",
                      (first_name, surname, work, practice, hashed))
            conn.commit()
            st.success("Doctor registered successfully!")

def doctor_login():
    st.title("Doctor Login")
    practice = st.text_input("Practice Number")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        c.execute("SELECT id, first_name, password_hash FROM doctors WHERE practice_number=?", (practice,))
        data = c.fetchone()
        if data and check_password(password, data[2]):
            st.session_state.user_role = "doctor"
            st.session_state.user_id = data[0]
            st.session_state.user_name = data[1]
            st.experimental_rerun()
        else:
            st.error("Invalid credentials.")

def patient_dashboard():
    st.title(f"Welcome, {st.session_state.user_name}")

    st.subheader("Book Appointment")
    doctors = get_doctors()
    options = [f"{doc[0]} - Dr. {doc[1]} {doc[2]} ({doc[3]})" for doc in doctors]
    doctor = st.selectbox("Choose Doctor", options)
    date = st.date_input("Date", min_value=datetime.today().date())
    time = st.time_input("Time")
    dt = datetime.combine(date, time)

    if st.button("Book"):
        doc_id = int(doctor.split(" - ")[0])
        c.execute("INSERT INTO appointments (patient_id, doctor_id, time, status) VALUES (?, ?, ?, ?)",
                  (st.session_state.user_id, doc_id, dt.isoformat(), "Scheduled"))
        conn.commit()
        st.success("Appointment booked!")

    st.subheader("My Appointments")
    c.execute('''SELECT a.time, d.first_name, d.surname FROM appointments a 
                 JOIN doctors d ON a.doctor_id = d.id WHERE a.patient_id=?''',
              (st.session_state.user_id,))
    for row in c.fetchall():
        st.info(f"Doctor: Dr. {row[1]} {row[2]} | Time: {row[0]}")

    st.subheader("My Prescriptions")
    c.execute("SELECT medication, prescribed_on, refill_due FROM prescriptions WHERE patient_id=?", (st.session_state.user_id,))
    for med in c.fetchall():
        st.success(f"{med[0]} | Prescribed: {med[1]} | Refill Due: {med[2]}")

def doctor_dashboard():
    st.title(f"Doctor Dashboard - Dr. {st.session_state.user_name}")

    c.execute('''SELECT a.id, p.full_name, a.time FROM appointments a 
                 JOIN patients p ON a.patient_id = p.id WHERE a.doctor_id=?''',
              (st.session_state.user_id,))
    for row in c.fetchall():
        st.info(f"Patient: {row[1]} | Time: {row[2]}")
        med = st.text_input(f"Prescription for {row[1]} at {row[2]}", key=f"med_{row[0]}")
        if st.button("Prescribe", key=f"btn_{row[0]}"):
            today = datetime.now().date().isoformat()
            refill = (datetime.now() + timedelta(days=30)).date().isoformat()
            c.execute("INSERT INTO prescriptions (patient_id, doctor_id, medication, prescribed_on, refill_due) VALUES (?, ?, ?, ?, ?)",
                      (row[0], st.session_state.user_id, med, today, refill))
            conn.commit()
            st.success("Medication prescribed.")

# =========================
# MAIN
# =========================
st.set_page_config(page_title="KZN Health App", layout="centered")

menu = ["Home", "Register (Patient)", "Register (Doctor)", "Login (Patient)", "Login (Doctor)"]
choice = st.sidebar.selectbox("Menu", menu)

if "user_role" not in st.session_state:
    if choice == "Register (Patient)":
        patient_register()
    elif choice == "Register (Doctor)":
        doctor_register()
    elif choice == "Login (Patient)":
        patient_login()
    elif choice == "Login (Doctor)":
        doctor_login()
    else:
        st.title("Welcome to KZN Public Healthcare Queue App")
        st.markdown("Use the sidebar to log in or register.")
else:
    if st.session_state.user_role == "patient":
        patient_dashboard()
    elif st.session_state.user_role == "doctor":
        doctor_dashboard()

    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.experimental_rerun()
