from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField, FileField
from wtforms.validators import DataRequired, Length, ValidationError
from models import User
import re

class PasswordComplexity:
    """Валидатор для проверки сложности пароля"""
    def __init__(self, message=None):
        if not message:
            message = 'Пароль должен содержать не менее 6 символов, включая заглавные буквы, строчные буквы, цифры и спецсимволы.'
        self.message = message

    def __call__(self, form, field):
        password = field.data
        
        # Проверка длины
        if len(password) < 6:
            raise ValidationError('Пароль должен содержать не менее 6 символов.')
        
        # Проверка заглавных букв
        if not re.search(r'[A-Z]', password):
            raise ValidationError('Пароль должен содержать хотя бы одну заглавную букву.')
        
        # Проверка строчных букв
        if not re.search(r'[a-z]', password):
            raise ValidationError('Пароль должен содержать хотя бы одну строчную букву.')
        
        # Проверка цифр
        if not re.search(r'\d', password):
            raise ValidationError('Пароль должен содержать хотя бы одну цифру.')
        
        # Проверка спецсимволов
        if not re.search(r'[!@#$%^&*]', password):
            raise ValidationError('Пароль должен содержать хотя бы один спецсимвол (!@#$%^&*).')

class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField('Пароль', validators=[DataRequired()])
    role = SelectField('Роль', choices=[
        ('doctor', 'Врач'), 
        ('patient', 'Пациент'), 
        ('admin', 'Администратор')
    ], validators=[DataRequired()])
    submit = SubmitField('Войти')

class RegistrationForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField('Пароль', validators=[
        DataRequired(), 
        PasswordComplexity()
    ])
    submit = SubmitField('Зарегистрироваться')

    def validate_username(self, username):
        if User.query.filter_by(username=username.data).first():
            raise ValidationError('Пользователь с таким логином уже существует.')

class AppointmentForm(FlaskForm):
    doctor = SelectField('Врач', validators=[DataRequired()])
    date = SelectField('Дата', validators=[DataRequired()])
    time_slot = SelectField('Время', validators=[DataRequired()])
    submit = SubmitField('Записаться')

class UploadFileForm(FlaskForm):
    file = FileField('Файл', validators=[DataRequired()])
    submit = SubmitField('Загрузить')

class CreateUserForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField('Пароль', validators=[
        DataRequired(), 
        PasswordComplexity()
    ])
    submit = SubmitField('Создать врача')

    def validate_username(self, username):
        if User.query.filter_by(username=username.data).first():
            raise ValidationError('Пользователь с таким логином уже существует.')