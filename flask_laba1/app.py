from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from config import Config
from models import db, User, Appointment
from forms import LoginForm, RegistrationForm, AppointmentForm, UploadFileForm
import os
from datetime import datetime, timedelta

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    
    return app

app = create_app()

def get_time_slots():
    return [f"{hour:02d}:00-{hour+1:02d}:00" for hour in range(8, 16)]

def get_available_dates():
    today = datetime.today()
    return [(today + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(14)]

@app.route('/')
def index():
    return render_template('base.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Регистрация успешна!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data) and user.role == form.role.data:
            session['user'] = user.username
            session['role'] = user.role
            flash('Вход выполнен!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Неверный логин, пароль или роль.', 'error')
    return render_template('login.html', form=form)

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    username = session['user']
    role = session['role']
    if role == 'doctor':
        return render_template('doctor_dates.html', dates=get_available_dates(), username=username)
    else:
        appointments = Appointment.query.filter_by(patient_username=username).order_by(Appointment.appointment_date, Appointment.time_slot).all()
        return render_template('dashboard.html', username=username, role=role, appointments=appointments)

@app.route('/doctor_schedule/<date>')
def doctor_schedule(date):
    if 'user' not in session or session['role'] != 'doctor':
        flash('Доступ запрещён.', 'error')
        return redirect(url_for('login'))
    if date not in get_available_dates():
        flash('Недопустимая дата.', 'error')
        return redirect(url_for('dashboard'))
    username = session['user']
    appointments = Appointment.query.filter_by(doctor_username=username, appointment_date=date).all()
    appt_dict = {appt.time_slot: appt.patient_username for appt in appointments}
    schedule = [{'time_slot': slot, 'patient': appt_dict.get(slot, 'Не назначено')} for slot in get_time_slots()]
    return render_template('doctor_single_day.html', date=date, schedule=schedule, username=username)

@app.route('/book', methods=['GET', 'POST'])
def book_appointment():
    if 'user' not in session or session['role'] != 'patient':
        flash('Только пациенты могут записываться на приём.', 'error')
        return redirect(url_for('dashboard'))
    form = AppointmentForm()
    doctors = [(u.username, u.username) for u in User.query.filter_by(role='doctor').all()]
    form.doctor.choices = doctors
    form.date.choices = [(d, d) for d in get_available_dates()]
    form.time_slot.choices = [(s, s) for s in get_time_slots()]
    
    if form.validate_on_submit():
        try:
            appt = Appointment(
                doctor_username=form.doctor.data,
                patient_username=session['user'],
                appointment_date=form.date.data,
                time_slot=form.time_slot.data
            )
            db.session.add(appt)
            db.session.commit()
            flash('Вы успешно записаны на приём!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('❗ В это время врач уже занят. Пожалуйста, выберите другое время.', 'error')
    return render_template('book_appointment.html', form=form)

@app.route('/cancel/<int:appt_id>', methods=['POST'])
def cancel_appointment(appt_id):
    if 'user' not in session or session['role'] != 'patient':
        flash('Доступ запрещён.', 'error')
        return redirect(url_for('dashboard'))
    appt = Appointment.query.filter_by(id=appt_id, patient_username=session['user']).first()
    if appt:
        db.session.delete(appt)
        db.session.commit()
        flash('Запись отменена.', 'info')
    else:
        flash('Запись не найдена.', 'error')
    return redirect(url_for('dashboard'))

@app.route('/reschedule/<int:appt_id>', methods=['GET', 'POST'])
def reschedule_appointment(appt_id):
    if 'user' not in session or session['role'] != 'patient':
        flash('Доступ запрещён.', 'error')
        return redirect(url_for('dashboard'))
    appt = Appointment.query.filter_by(id=appt_id, patient_username=session['user']).first()
    if not appt:
        flash('Запись не найдена.', 'error')
        return redirect(url_for('dashboard'))
    
    form = AppointmentForm()
    doctors = [(u.username, u.username) for u in User.query.filter_by(role='doctor').all()]
    form.doctor.choices = doctors
    form.date.choices = [(d, d) for d in get_available_dates()]
    form.time_slot.choices = [(s, s) for s in get_time_slots()]
    
    if request.method == 'GET':
        form.doctor.data = appt.doctor_username
        form.date.data = appt.appointment_date
        form.time_slot.data = appt.time_slot
    
    if form.validate_on_submit():
        try:
            db.session.delete(appt)
            new_appt = Appointment(
                doctor_username=form.doctor.data,
                patient_username=session['user'],
                appointment_date=form.date.data,
                time_slot=form.time_slot.data
            )
            db.session.add(new_appt)
            db.session.commit()
            flash('Запись успешно перенесена!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('❗ В это время врач уже занят. Пожалуйста, выберите другое время.', 'error')
    return render_template('reschedule.html', form=form, appt=appt)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if 'user' not in session:
        return redirect(url_for('login'))
    form = UploadFileForm()
    if form.validate_on_submit():
        file = form.file.data
        filename = f"{session['user']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        flash('Файл успешно загружен!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('upload.html', form=form)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)