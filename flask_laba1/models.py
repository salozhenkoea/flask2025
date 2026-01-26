from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'doctor' or 'patient'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_username = db.Column(db.String(80), nullable=False)
    patient_username = db.Column(db.String(80), nullable=False)
    appointment_date = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD
    time_slot = db.Column(db.String(20), nullable=False)         # HH:00-HH:00
    
    __table_args__ = (
        db.UniqueConstraint('doctor_username', 'appointment_date', 'time_slot', name='uq_appointment'),
    )