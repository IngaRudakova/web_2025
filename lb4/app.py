# Импорт необходимых модулей Flask и связанных библиотек
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash  # Для хеширования и проверки паролей
from flask_sqlalchemy import SQLAlchemy  # ORM для работы с базой данных
from flask_wtf import FlaskForm  # Для работы с формами
from wtforms import StringField, PasswordField, SelectField, SubmitField  # Поля форм
from wtforms.validators import DataRequired, Length, Regexp, EqualTo  # Валидаторы полей форм

# Создание экземпляра Flask-приложения
app = Flask(__name__)
app.secret_key = 'my_secret_key'  # Секретный ключ для сессий

# Настройка Flask-Login для аутентификации пользователей
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Указываем endpoint для страницы входа

# Настройка базы данных (используем SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
db = SQLAlchemy(app)

# Модель данных для ролей пользователей
class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Первичный ключ
    name = db.Column(db.String(50), nullable=False)  # Название роли
    description = db.Column(db.String(255))  # Описание роли

# Модель данных для пользователей
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Первичный ключ
    username = db.Column(db.String(50), unique=True, nullable=False)  # Уникальное имя пользователя
    password_hash = db.Column(db.String(128), nullable=False)  # Хеш пароля
    last_name = db.Column(db.String(50))  # Фамилия
    first_name = db.Column(db.String(50), nullable=False)  # Имя (обязательное поле)
    middle_name = db.Column(db.String(50))  # Отчество
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))  # Внешний ключ для связи с ролями
    role = db.relationship('Role', backref=db.backref('users', lazy=True))  # Связь с моделью Role
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())  # Дата создания

    # Методы, необходимые для Flask-Login
    @property
    def is_authenticated(self):
        return True  # Пользователь аутентифицирован

    @property
    def is_active(self):
        return True  # Учетная запись активна

    @property
    def is_anonymous(self):
        return False  # Это не анонимный пользователь

    def get_id(self):
        return str(self.id)  # Возвращаем ID как строку

# Загрузчик пользователя для Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))  # Загружаем пользователя по ID

# Форма для создания/редактирования пользователя
class UserForm(FlaskForm):
    username = StringField('Логин', validators=[
        DataRequired(), Length(min=5), Regexp(r'^[a-zA-Z0-9]+$')  # Валидация логина
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(), Length(min=8, max=128),  # Пароль должен быть от 8 до 128 символов
        Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z\d~!?@#$%^&*_\-+()\[\]{}><\/\\|"\',.:;]+$')  # Сложность пароля
    ])
    confirm_password = PasswordField('Повторите пароль', validators=[
        DataRequired(), EqualTo('password', message='Пароли должны совпадать.')  # Подтверждение пароля
    ])
    last_name = StringField('Фамилия')
    first_name = StringField('Имя', validators=[DataRequired()])  # Обязательное поле
    middle_name = StringField('Отчество')
    role_id = SelectField('Роль', coerce=int)  # Выпадающий список ролей
    submit = SubmitField('Сохранить')

# Главная страница - список пользователей
@app.route('/')
def index():
    users = User.query.all()
    return render_template('index.html', users=users)

# Страница входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = 'remember' in request.form  # Запомнить пользователя
        user = User.query.filter_by(username=username).first()
        
        # Проверяем пользователя и пароль
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            flash('Вы успешно вошли в систему!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))  # Редирект на запрошенную страницу или главную
        else:
            flash('Неверное имя пользователя или пароль.', 'danger')
    return render_template('login.html', next=request.args.get('next'))

# Выход из системы
@app.route('/logout')
@login_required  # Только для авторизованных пользователей
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('index'))

# Создание нового пользователя
@app.route('/user/create', methods=['GET', 'POST'])
@login_required
def create_user():
    form = UserForm()
    form.role_id.choices = [(role.id, role.name) for role in Role.query.all()]  # Заполняем список ролей
    if form.validate_on_submit():
        try:
            # Создаем нового пользователя
            user = User(
                username=form.username.data,
                password_hash=generate_password_hash(form.password.data),  # Хешируем пароль
                last_name=form.last_name.data,
                first_name=form.first_name.data,
                middle_name=form.middle_name.data,
                role_id=form.role_id.data
            )
            db.session.add(user)
            db.session.commit()
            flash('Пользователь успешно создан.', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash('Ошибка при создании пользователя.', 'danger')
    return render_template('user_form.html', form=form)

# Редактирование пользователя
@app.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)  # Получаем пользователя или 404
    form = UserForm(obj=user)
    form.role_id.choices = [(role.id, role.name) for role in Role.query.all()]
    del form.username  # Удаляем поля, которые нельзя редактировать
    del form.password
    del form.confirm_password
    if form.validate_on_submit():
        try:
            # Обновляем данные пользователя
            user.last_name = form.last_name.data
            user.first_name = form.first_name.data
            user.middle_name = form.middle_name.data
            user.role_id = form.role_id.data
            db.session.commit()
            flash('Пользователь успешно обновлён.', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash('Ошибка при обновлении пользователя.', 'danger')
    return render_template('user_form.html', form=form)

@app.route('/user/<int:user_id>', methods=['GET'])
@login_required
def view_user(user_id):
    
    user = User.query.get_or_404(user_id)  
    return render_template('view_user.html', user=user)

# Удаление пользователя
@app.route('/user/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Вы не можете удалить свою собственную учетную запись.', 'danger')
        return redirect(url_for('index'))
    try:
        db.session.delete(user)
        db.session.commit()
        flash('Пользователь успешно удалён.', 'success')
    except Exception as e:
        flash('Ошибка при удалении пользователя.', 'danger')
    return redirect(url_for('index'))

# Смена пароля
@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        # Проверяем старый пароль
        if not check_password_hash(current_user.password_hash, old_password):
            flash('Старый пароль неверен.', 'danger')
        elif new_password != confirm_password:
            flash('Новые пароли не совпадают.', 'danger')
        elif len(new_password) < 8 or len(new_password) > 128:
            flash('Пароль должен быть от 8 до 128 символов.', 'danger')
        else:
            # Обновляем пароль
            current_user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            flash('Пароль успешно изменён.', 'success')
            return redirect(url_for('index'))
    return render_template('change_password.html')

# Подтверждение удаления пользователя (AJAX)
@app.route('/user/<int:user_id>/confirm_delete', methods=['GET'])
@login_required
def confirm_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({'message': f'Вы уверены, что хотите удалить пользователя {user.last_name} {user.first_name}?'})

# Управление ролями
@app.route('/roles', methods=['GET', 'POST'])
@login_required
def manage_roles():
    if request.method == 'POST':
        # Создание новой роли
        role_name = request.form.get('role_name')
        role_description = request.form.get('role_description')
        if role_name:
            new_role = Role(name=role_name, description=role_description)
            db.session.add(new_role)
            db.session.commit()
            flash('Роль успешно добавлена.', 'success')
        else:
            flash('Название роли не может быть пустым.', 'danger')
    roles = Role.query.all()
    return render_template('roles.html', roles=roles)

# Удаление роли
@app.route('/roles/<int:role_id>/delete', methods=['POST'])
@login_required
def delete_role(role_id):
    role = Role.query.get_or_404(role_id)
    if User.query.filter_by(role_id=role.id).first():
        flash('Невозможно удалить роль, так как она связана с пользователями.', 'danger')
    else:
        db.session.delete(role)
        db.session.commit()
        flash('Роль успешно удалена.', 'success')
    return redirect(url_for('manage_roles'))

# Инициализация базы данных перед первым запросом
@app.before_request
def initialize_database():
    if not hasattr(app, 'db_initialized'):
        db.create_all()  # Создаем таблицы, если их нет
        app.db_initialized = True
        
        # Создаем тестовые роли, если их нет
        if not Role.query.first():
            roles = [
                Role(name="Администратор", description="Полный доступ"),
                Role(name="Пользователь", description="Ограниченный доступ")
            ]
            db.session.bulk_save_objects(roles)
            db.session.commit()
        
        # Создаем тестового пользователя, если его нет
        if not User.query.filter_by(username="user").first():
            default_role = Role.query.filter_by(name="Пользователь").first()
            default_user = User(
                username="user",
                password_hash=generate_password_hash("kBj-d53-huA-3zC", method='pbkdf2:sha256'),
                first_name="Тест",
                last_name="Пользователь",
                middle_name="",
                role_id=default_role.id
            )
            db.session.add(default_user)
            db.session.commit()
        print("Тестовые данные созданы: пользователь 'user' и роли.")


# Запуск приложения в режиме отладки
if __name__ == '__main__':
    app.run(debug=True)



# Y78-Oi9-t6U-iu8    