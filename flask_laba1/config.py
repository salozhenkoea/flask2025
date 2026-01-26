import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'very-secret-key-for-clinic'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///clinic.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # макс 16 МБ