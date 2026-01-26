from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'doctor', 'patient', 'admin'
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
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

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    patient_username = db.Column(db.String(80), nullable=False)
    upload_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    file_type = db.Column(db.String(50))
    file_size = db.Column(db.Integer)  # размер в байтах
    
    def get_file_size_mb(self):
        """Возвращает размер файла в МБ"""
        return round(self.file_size / (1024 * 1024), 2) if self.file_size else 0
    
    def get_file_type_icon(self):
        """Возвращает иконку в зависимости от типа файла"""
        if self.file_type in ['pdf']:
            return '📄'
        elif self.file_type in ['jpg', 'jpeg', 'png', 'gif']:
            return '🖼️'
        elif self.file_type in ['doc', 'docx']:
            return '📝'
        elif self.file_type in ['xls', 'xlsx']:
            return '📊'
        else:
            return '📁'