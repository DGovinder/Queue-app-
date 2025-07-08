import streamlit as st
import sqlite3
import hashlib
from datetime import datetime, timedelta

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="The Health Line",
    page_icon="🩺",
    layout="centered"
)

# =========================
# STYLE / CSS
# =========================
st.markdown(
    """
    <style>
    .big-title {
        font-size: 3em;
        color: #7a0014;
        text-align: center;
        margin-bottom: 20px;
    }
    .subtitle {
        font-size: 1.5em;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

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
        full_name TEXT NOT NULL,
        dob TEXT NOT NULL,
        id_number TEXT NOT NULL UNIQUE,
        language TEXT NOT NULL,
        password_hash TEXT NOT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        surname TEXT NOT NULL,
        place_of_work TEXT NOT NULL,
        practice_number TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        doctor_id INTEGER NOT NULL,
        time TEXT NOT NULL,
        status TEXT NOT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS prescriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        doctor_id INTEGER NOT NULL,
        medication TEXT NOT NULL,
        prescribed_on TEXT NOT NULL,
        refill_due TEXT NOT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        submitted_on TEXT NOT NULL,
        status TEXT NOT NULL
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
    st.markdown('<div class="big-title">🩺 Patient Registration</div>', unsafe_allow_html=True)
    st.divider()
    name = st.text_input("Full Name")
    dob = st.date_input("Date of Birth", min_value=datetime(1910, 1, 1).date(), max_value=datetime.today().date())
    id_number = st.text_input("ID Number")
    language = st.selectbox("Language", get_languages())
    password = st.text_input("Password", type="password")

    if st.button("Register"):
        if not name.strip() or not id_number.strip() or not password.strip():
            st.error("All fields are required.")
            return
        if not password_policy(password):
            st.error("Password must have at least 6 characters, a number, and a special character.")
            return
        hashed = hash_password(password)
        try:
            c.execute(
                "INSERT INTO patients (full_name, dob, id_number, language, password_hash) VALUES (?, ?, ?, ?, ?)",
                (name.strip(), dob.isoformat(), id_number.strip(), language, hashed)
            )
            conn.commit()
            st.success("✅ Patient registered successfully!")
        except sqlite3.IntegrityError:
            st.error("❌ ID Number already registered. Please log in instead.")
        except Exception as e:
            st.error(f"Database error: {e}")

def patient_login():
    st.markdown('<div class="big-title">🩺 Patient Login</div>', unsafe_allow_html=True)
    st.divider()
    id_number = st.text_input("ID Number")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if not id_number.strip() or not password.strip():
            st.error("All fields are required.")
            return
        c.execute("SELECT id, full_name, password_hash FROM patients WHERE id_number=?", (id_number.strip(),))
        data = c.fetchone()
        if data and check_password(password, data[2]):
            st.session_state.user_role = "patient"
            st.session_state.user_id = data[0]
            st.session_state.user_name = data[1]
            st.rerun()
        else:
            st.error("❌ Invalid ID Number or password.")

def doctor_register():
    st.markdown('<div class="big-title">🩺 Doctor Registration</div>', unsafe_allow_html=True)
    st.divider()
    first_name = st.text_input("First Name")
    surname = st.text_input("Surname")
    work = st.text_input("Place of Work")
    practice = st.text_input("13-digit Practice Number")
    password = st.text_input("Password", type="password")

    if st.button("Register"):
        if not first_name.strip() or not surname.strip() or not work.strip() or not practice.strip() or not password.strip():
            st.error("All fields are required.")
            return
        if len(practice.strip()) != 13 or not practice.strip().isdigit():
            st.error("Practice Number must be exactly 13 digits.")
            return
        if not password_policy(password):
            st.error("Password must have at least 6 characters, a number, and a special character.")
            return
        hashed = hash_password(password)
        try:
            c.execute(
                "INSERT INTO doctors (first_name, surname, place_of_work, practice_number, password_hash) VALUES (?, ?, ?, ?, ?)",
                (first_name.strip(), surname.strip(), work.strip(), practice.strip(), hashed)
            )
            conn.commit()
            st.success("✅ Doctor registered successfully!")
        except sqlite3.IntegrityError:
            st.error("❌ Practice Number already registered. Please log in instead.")
        except Exception as e:
            st.error(f"Database error: {e}")

def doctor_login():
    st.markdown('<div class="big-title">🩺 Doctor Login</div>', unsafe_allow_html=True)
    st.divider()
    practice = st.text_input("Practice Number")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if not practice.strip() or not password.strip():
            st.error("All fields are required.")
            return
        c.execute("SELECT id, first_name, password_hash FROM doctors WHERE practice_number=?", (practice.strip(),))
        data = c.fetchone()
        if data and check_password(password, data[2]):
            st.session_state.user_role = "doctor"
            st.session_state.user_id = data[0]
            st.session_state.user_name = data[1]
            st.rerun()
        else:
            st.error("❌ Invalid Practice Number or password.")

def patient_dashboard():
    st.markdown(f'<div class="big-title">👋 Welcome, {st.session_state.user_name}</div>', unsafe_allow_html=True)
    st.divider()

    st.markdown('<div class="subtitle">🗓️ Book Appointment</div>', unsafe_allow_html=True)
    doctors = get_doctors()
    if not doctors:
        st.warning("⚠️ No doctors available.")
        return

    options = [f"{doc[0]} - Dr. {doc[1]} {doc[2]} ({doc[3]})" for doc in doctors]
    doctor = st.selectbox("Choose Doctor", options)
    date = st.date_input("Date", min_value=datetime.today().date())
    time = st.time_input("Time")
    dt = datetime.combine(date, time)

    if st.button("Book Appointment"):
        doc_id = int(doctor.split(" - ")[0])
        try:
            c.execute(
                "INSERT INTO appointments (patient_id, doctor_id, time, status) VALUES (?, ?, ?, ?)",
                (st.session_state.user_id, doc_id, dt.isoformat(), "Scheduled")
            )
            conn.commit()
            st.success("✅ Appointment booked!")
        except Exception as e:
            st.error(f"Error booking appointment: {e}")

    st.divider()
    st.markdown('<div class="subtitle">📋 My Appointments</div>', unsafe_allow_html=True)
    c.execute('''
        SELECT a.time, d.first_name, d.surname 
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        WHERE a.patient_id=?
        ORDER BY a.time DESC
    ''', (st.session_state.user_id,))
    rows = c.fetchall()
    if rows:
        for row in rows:
            st.info(f"Doctor: Dr. {row[1]} {row[2]} | Time: {row[0]}")
    else:
        st.write("No appointments yet.")

    st.divider()
    st.markdown('<div class="subtitle">💊 My Prescriptions</div>', unsafe_allow_html=True)
    c.execute(
        "SELECT medication, prescribed_on, refill_due FROM prescriptions WHERE patient_id=? ORDER BY prescribed_on DESC",
        (st.session_state.user_id,)
    )
    meds = c.fetchall()
    if meds:
        for med in meds:
            st.success(f"{med[0]} | Prescribed: {med[1]} | Refill Due: {med[2]}")
    else:
        st.write("No prescriptions yet.")

def doctor_dashboard():
    st.markdown(f'<div class="big-title">🩺 Doctor Dashboard - Dr. {st.session_state.user_name}</div>', unsafe_allow_html=True)
    st.divider()

    c.execute('''
        SELECT a.id, p.id, p.full_name, a.time
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        WHERE a.doctor_id=?
        ORDER BY a.time DESC
    ''', (st.session_state.user_id,))
    appointments = c.fetchall()
    if not appointments:
        st.write("No appointments scheduled.")
    else:
        for appt in appointments:
            appointment_id, patient_id, patient_name, appointment_time = appt
            st.info(f"Patient: {patient_name} | Time: {appointment_time}")

            prescription_key = f"med_{appointment_id}"
            medication = st.text_input(f"Prescription for {patient_name}", key=prescription_key)

            prescribe_button_key = f"btn_{appointment_id}"
            if st.button("Prescribe", key=prescribe_button_key):
                if not medication.strip():
                    st.error("Please enter medication name before prescribing.")
                    continue
                today = datetime.now().date().isoformat()
                refill_due = (datetime.now() + timedelta(days=30)).date().isoformat()
                try:
                    c.execute(
                        "INSERT INTO prescriptions (patient_id, doctor_id, medication, prescribed_on, refill_due) VALUES (?, ?, ?, ?, ?)",
                        (patient_id, st.session_state.user_id, medication.strip(), today, refill_due)
                    )
                    conn.commit()
                    st.success(f"✅ Prescription for {patient_name} saved!")
                except Exception as e:
                    st.error(f"Error saving prescription: {e}")

    st.divider()
    st.subheader("⚠️ Danger Zone")
    if st.button("Delete My Doctor Account"):
        confirm = st.checkbox("Yes, I really want to delete my account permanently.")
        if confirm:
            try:
                c.execute("DELETE FROM doctors WHERE id=?", (st.session_state.user_id,))
                conn.commit()
                st.success("Your doctor account has been deleted.")
                st.session_state.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Error deleting account: {e}")

# =========================
# MAIN
# =========================
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
        st.markdown('<div class="big-title">🩺 The Health Line</div>', unsafe_allow_html=True)
        st.markdown("Welcome to **The Health Line**. Use the sidebar to register or log in.")
else:
    if st.session_state.user_role == "patient":
        patient_dashboard()
    elif st.session_state.user_role == "doctor":
        doctor_dashboard()

    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()
