from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Формат: { username: { 'password_hash': ..., 'role': 'doctor' or 'patient' } }
users_db = {}

@app.route('/')
def index():
    return render_template('base.html')

# === РЕГИСТРАЦИЯ ===
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role')  # 'doctor' или 'patient'

        if not username or not password or not role:
            flash('Все поля обязательны!', 'error')
        elif username in users_db:
            flash('Пользователь с таким логином уже существует!', 'error')
        elif role not in ['doctor', 'patient']:
            flash('Неверная роль!', 'error')
        else:
            hashed_pw = generate_password_hash(password)
            users_db[username] = {
                'password_hash': hashed_pw,
                'role': role
            }
            flash('Регистрация успешна! Теперь вы можете войти.', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html')

# === ВХОД ===
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role')

        if not username or not password or not role:
            flash('Заполните все поля!', 'error')
        elif username not in users_db:
            flash('Неверный логин или пароль!', 'error')
        else:
            user = users_db[username]
            # Проверяем пароль И роль
            if user['role'] != role:
                flash('Неверная роль для этого пользователя!', 'error')
            elif check_password_hash(user['password_hash'], password):
                session['user'] = username
                session['role'] = role
                flash('Вход выполнен успешно!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Неверный логин или пароль!', 'error')
    
    return render_template('login.html')

# === ЛИЧНЫЙ КАБИНЕТ ===
@app.route('/dashboard')
def dashboard():
    if 'user' not in session or 'role' not in session:
        flash('Пожалуйста, войдите в систему.', 'error')
        return redirect(url_for('login'))
    
    username = session['user']
    role = session['role']
    role_name = 'Врач' if role == 'doctor' else 'Пациент'
    
    return render_template('dashboard.html', username=username, role=role, role_name=role_name)

# === ВЫХОД ===
@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)