from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('clinic.db')
    c = conn.cursor()
    # Таблица пользователей
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL
    )''')
    # Таблица записей на приём
    c.execute('''CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doctor_username TEXT NOT NULL,
        patient_username TEXT NOT NULL,
        time_slot TEXT NOT NULL,  -- например: "12:00-13:00"
        UNIQUE(doctor_username, time_slot)
    )''')
    conn.commit()
    conn.close()

# Вызов при запуске
init_db()

# === Вспомогательные функции ===
def get_db_connection():
    conn = sqlite3.connect('clinic.db')
    conn.row_factory = sqlite3.Row  # Позволяет обращаться по имени колонки
    return conn

def get_time_slots():
    """Возвращает список временных слотов с 8:00 до 16:00"""
    slots = []
    for hour in range(8, 16):
        start = f"{hour:02d}:00"
        end = f"{hour + 1:02d}:00"
        slots.append(f"{start}-{end}")
    return slots

# === Маршруты ===
@app.route('/')
def index():
    return render_template('base.html')

# === РЕГИСТРАЦИЯ ===
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role')

        if not username or not password or not role:
            flash('Все поля обязательны!', 'error')
        elif role not in ['doctor', 'patient']:
            flash('Неверная роль!', 'error')
        else:
            try:
                conn = get_db_connection()
                hashed_pw = generate_password_hash(password)
                conn.execute(
                    'INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)',
                    (username, hashed_pw, role)
                )
                conn.commit()
                conn.close()
                flash('Регистрация успешна!', 'success')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash('Пользователь с таким логином уже существует!', 'error')
    
    return render_template('register.html')

# === ВХОД ===
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role')

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and user['role'] == role and check_password_hash(user['password_hash'], password):
            session['user'] = username
            session['role'] = role
            flash('Вход выполнен!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Неверный логин, пароль или роль!', 'error')
    
    return render_template('login.html')


# === ЛИЧНЫЙ КАБИНЕТ ===
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    username = session['user']
    role = session['role']
    conn = get_db_connection()
    
    if role == 'doctor':
        # Получаем все записи к этому врачу
        appointments = conn.execute(
            'SELECT time_slot, patient_username FROM appointments WHERE doctor_username = ? ORDER BY time_slot',
            (username,)
        ).fetchall()
    else:
        # Пациент: показываем его записи
        appointments = conn.execute(
            'SELECT time_slot, doctor_username FROM appointments WHERE patient_username = ? ORDER BY time_slot',
            (username,)
        ).fetchall()
    
    conn.close()
    return render_template('dashboard.html', username=username, role=role, appointments=appointments)

# === ЗАПИСЬ НА ПРИЁМ (только для пациента) ===
@app.route('/book', methods=['GET', 'POST'])
def book_appointment():
    if 'user' not in session or session['role'] != 'patient':
        flash('Только пациенты могут записываться на приём.', 'error')
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    doctors = conn.execute('SELECT username FROM users WHERE role = "doctor"').fetchall()
    conn.close()

    if request.method == 'POST':
        doctor = request.form['doctor']
        time_slot = request.form['time_slot']
        patient = session['user']

        try:
            conn = get_db_connection()
            conn.execute(
                'INSERT INTO appointments (doctor_username, patient_username, time_slot) VALUES (?, ?, ?)',
                (doctor, patient, time_slot)
            )
            conn.commit()
            conn.close()
            flash('Вы успешно записаны на приём!', 'success')
            return redirect(url_for('dashboard'))
        except sqlite3.IntegrityError:
            flash('Это время уже занято!', 'error')

    # GET: показываем форму
    time_slots = get_time_slots()
    return render_template('book_appointment.html', doctors=doctors, time_slots=time_slots)

# === ВЫХОД ===
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
