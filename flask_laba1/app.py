from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Надёжный случайный ключ

# Простое "хранилище" пользователей в памяти (в реальном проекте — база данных!)
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
        
        if not username or not password:
            flash('Логин и пароль не могут быть пустыми!', 'error')
        elif username in users_db:
            flash('Пользователь с таким логином уже существует!', 'error')
        else:
            # Хешируем пароль!
            hashed_pw = generate_password_hash(password)
            users_db[username] = hashed_pw
            flash('Регистрация успешна! Теперь вы можете войти.', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html')

# === ВХОД ===
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in users_db and check_password_hash(users_db[username], password):
            session['user'] = username
            flash('Добро пожаловать!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Неверный логин или пароль!', 'error')
    
    return render_template('login.html')

# === ЛИЧНЫЙ КАБИНЕТ ===
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        flash('Пожалуйста, войдите в систему.', 'error')
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['user'])

# === ВЫХОД ===
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)