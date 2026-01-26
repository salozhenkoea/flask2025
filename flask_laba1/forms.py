from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField, FileField
from wtforms.validators import DataRequired, Length, ValidationError
from models import User

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
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    # Поле роли убрано - всегда "Пациент"
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
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    # Поле роли убрано - всегда "Врач"
    submit = SubmitField('Создать врача')

    def validate_username(self, username):
        if User.query.filter_by(username=username.data).first():
            raise ValidationError('Пользователь с таким логином уже существует.')