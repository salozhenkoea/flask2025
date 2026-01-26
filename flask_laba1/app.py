
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'very_secret_key_for_clinic_app'

def init_db():
    conn = sqlite3.connect('clinic.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doctor_username TEXT NOT NULL,
        patient_username TEXT NOT NULL,
        appointment_date TEXT NOT NULL,
        time_slot TEXT NOT NULL,
        UNIQUE(doctor_username, appointment_date, time_slot)
    )''')
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('clinic.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_time_slots():
    return [f"{hour:02d}:00-{hour+1:02d}:00" for hour in range(8, 16)]

def get_available_dates():
    today = datetime.today()
    return [(today + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(14)]

init_db()

@app.route('/')
def index():
    return render_template('base.html')

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
                conn.execute('INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)',
                             (username, hashed_pw, role))
                conn.commit()
                conn.close()
                flash('Регистрация успешна!', 'success')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash('Пользователь с таким логином уже существует!', 'error')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role')
        
        if not username or not password or not role:
            flash('Заполните все поля!', 'error')
            return render_template('login.html')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if not user:
            flash('Неверный логин или пароль.', 'error')
        elif user['role'] != role:
            flash('Выбрана неверная роль для этого пользователя.', 'error')
        elif not check_password_hash(user['password_hash'], password):
            flash('Неверный логин или пароль.', 'error')
        else:
            session['user'] = username
            session['role'] = role
            flash('Вход выполнен!', 'success')
            return redirect(url_for('dashboard'))
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    username = session['user']
    role = session['role']
    if role == 'doctor':
        # Показываем только список дат
        return render_template('doctor_dates.html', dates=get_available_dates(), username=username)
    else:
        conn = get_db_connection()
        appointments = conn.execute(
            'SELECT id, appointment_date, time_slot, doctor_username FROM appointments WHERE patient_username = ? ORDER BY appointment_date, time_slot',
            (username,)
        ).fetchall()
        conn.close()
        return render_template('dashboard.html', username=username, role=role, appointments=appointments)

# === НОВЫЙ МАРШРУТ: расписание врача на конкретную дату ===
@app.route('/doctor_schedule/<date>')
def doctor_schedule(date):
    if 'user' not in session or session['role'] != 'doctor':
        flash('Доступ запрещён.', 'error')
        return redirect(url_for('login'))
    
    if date not in get_available_dates():
        flash('Недопустимая дата.', 'error')
        return redirect(url_for('dashboard'))
    
    username = session['user']
    conn = get_db_connection()
    appointments = conn.execute(
        'SELECT time_slot, patient_username FROM appointments WHERE doctor_username = ? AND appointment_date = ?',
        (username, date)
    ).fetchall()
    conn.close()
    
    # Создаём полное расписание на эту дату
    appt_dict = {appt['time_slot']: appt['patient_username'] for appt in appointments}
    schedule = []
    for slot in get_time_slots():
        patient = appt_dict.get(slot, 'Не назначено')
        schedule.append({'time_slot': slot, 'patient': patient})
    
    return render_template('doctor_single_day.html', date=date, schedule=schedule, username=username)

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
        date = request.form['date']
        time_slot = request.form['time_slot']
        if date not in get_available_dates():
            flash('Недопустимая дата.', 'error')
            return redirect(url_for('book_appointment'))
        try:
            conn = get_db_connection()
            conn.execute(
                'INSERT INTO appointments (doctor_username, patient_username, appointment_date, time_slot) VALUES (?, ?, ?, ?)',
                (doctor, session['user'], date, time_slot)
            )
            conn.commit()
            conn.close()
            flash('Вы успешно записаны на приём!', 'success')
            return redirect(url_for('dashboard'))
        except sqlite3.IntegrityError:
            flash('Это время уже занято!', 'error')
    return render_template('book_appointment.html', 
                          doctors=doctors, 
                          dates=get_available_dates(), 
                          time_slots=get_time_slots())

@app.route('/cancel/<int:appt_id>', methods=['POST'])
def cancel_appointment(appt_id):
    if 'user' not in session or session['role'] != 'patient':
        flash('Доступ запрещён.', 'error')
        return redirect(url_for('dashboard'))
    conn = get_db_connection()
    appt = conn.execute(
        'SELECT id FROM appointments WHERE id = ? AND patient_username = ?',
        (appt_id, session['user'])
    ).fetchone()
    if appt:
        conn.execute('DELETE FROM appointments WHERE id = ?', (appt_id,))
        conn.commit()
        flash('Запись отменена.', 'info')
    else:
        flash('Запись не найдена.', 'error')
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/reschedule/<int:appt_id>', methods=['GET', 'POST'])
def reschedule_appointment(appt_id):
    if 'user' not in session or session['role'] != 'patient':
        flash('Доступ запрещён.', 'error')
        return redirect(url_for('dashboard'))
    conn = get_db_connection()
    appt = conn.execute(
        'SELECT * FROM appointments WHERE id = ? AND patient_username = ?',
        (appt_id, session['user'])
    ).fetchone()
    if not appt:
        conn.close()
        flash('Запись не найдена.', 'error')
        return redirect(url_for('dashboard'))
    doctors = conn.execute('SELECT username FROM users WHERE role = "doctor"').fetchall()
    conn.close()
    if request.method == 'POST':
        doctor = request.form['doctor']
        date = request.form['date']
        time_slot = request.form['time_slot']
        if date not in get_available_dates():
            flash('Недопустимая дата.', 'error')
        else:
            try:
                conn = get_db_connection()
                conn.execute('DELETE FROM appointments WHERE id = ?', (appt_id,))
                conn.execute(
                    'INSERT INTO appointments (doctor_username, patient_username, appointment_date, time_slot) VALUES (?, ?, ?, ?)',
                    (doctor, session['user'], date, time_slot)
                )
                conn.commit()
                conn.close()
                flash('Запись успешно перенесена!', 'success')
                return redirect(url_for('dashboard'))
            except sqlite3.IntegrityError:
                flash('Выбранное время уже занято!', 'error')
    return render_template('reschedule.html',
                          appt=appt,
                          doctors=doctors,
                          dates=get_available_dates(),
                          time_slots=get_time_slots())

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)