# Формы для работы с пользователями.
# - UserForm: форма для создания и редактирования пользователей.

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp, EqualTo

class UserForm(FlaskForm):
    username = StringField('Логин', validators=[
        DataRequired(), Length(min=5), Regexp(r'^[a-zA-Z0-9]+$')
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(), Length(min=8, max=128),
        Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z\d~!?@#$%^&*_\-+()\[\]{}><\/\\|"\',.:;]+$')
    ])
    confirm_password = PasswordField('Повторите пароль', validators=[
        DataRequired(), EqualTo('password', message='Пароли должны совпадать.')
    ])
    last_name = StringField('Фамилия')
    first_name = StringField('Имя', validators=[DataRequired()])
    middle_name = StringField('Отчество')
    role_id = SelectField('Роль', coerce=int)
    submit = SubmitField('Сохранить')
