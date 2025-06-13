# Импорт необходимых модулей и классов
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, abort, current_app
from flask_login import LoginManager, login_user, login_required, logout_user, current_user  # Модули для аутентификации
from werkzeug.security import generate_password_hash, check_password_hash  # Хеширование паролей
from flask_sqlalchemy import SQLAlchemy  # ORM для работы с БД
from flask_wtf import FlaskForm  # Формы Flask
from wtforms import StringField, PasswordField, SelectField, SubmitField  # Поля форм
from wtforms.validators import DataRequired, Length, Regexp, EqualTo  # Валидаторы полей
from functools import wraps  # Для создания декораторов
from models import db, Role, User, VisitLog  # Импорт моделей БД

# Инициализация Flask-Login для управления аутентификацией
login_manager = LoginManager()

# Функция для создания и настройки Flask-приложения
def create_app():
    # Создание экземпляра приложения
    app = Flask(__name__)
    app.secret_key = 'my_secret_key'  # Секретный ключ для сессий
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'  # Путь к БД

    # Инициализация расширений
    db.init_app(app)  # Инициализация SQLAlchemy
    login_manager.init_app(app)  # Инициализация Flask-Login
    login_manager.login_view = 'login'  # Страница входа

    # Регистрация Blueprint для журнала посещений
    from blueprints.visit_logs import visit_logs_bp
    visit_logs_bp.db = db  # Передача экземпляра db в Blueprint
    app.register_blueprint(visit_logs_bp)

    # Регистрация маршрутов приложения
    register_routes(app)

    # Создание таблиц БД и тестовых данных при первом запуске
    with app.app_context():
        db.create_all()

    # Обработчик, выполняемый перед каждым запросом
    @app.before_request
    def initialize_database():
        if not hasattr(app, 'db_initialized'):
            db.create_all()  # Создание таблиц, если их нет
            app.db_initialized = True
            
            # Создание тестовых ролей, если их нет
            if not Role.query.first():
                roles = [
                    Role(name="Администратор", description="Полный доступ"),
                    Role(name="Пользователь", description="Ограниченный доступ")
                ]
                db.session.bulk_save_objects(roles)  # Массовое сохранение
                db.session.commit()
            
            # Создание тестового пользователя, если его нет
            if not User.query.filter_by(username="user").first():
                default_role = Role.query.filter_by(name="Пользователь").first()
                default_user = User(
                    username="user",
                    password_hash=generate_password_hash("kBj-d53-huA-3zC"),
                    first_name="Тест",
                    last_name="Пользователь",
                    middle_name="",
                    role_id=default_role.id
                )
                db.session.add(default_user)
                db.session.commit()
            print("Тестовые данные созданы: пользователь 'user' и роли.")

    return app

# Декоратор для проверки прав доступа
def check_rights(required_role):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Проверка аутентификации и роли пользователя
            if not current_user.is_authenticated or current_user.role.name != required_role:
                flash('У вас недостаточно прав для доступа к данной странице.', 'danger')
                return redirect(url_for('index'))
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Регистрация маршрутов приложения
def register_routes(app):
    # Импорт необходимых модулей
    from flask import render_template, redirect, url_for, request, flash, jsonify
    from flask_login import login_user, login_required, logout_user, current_user
    from werkzeug.security import generate_password_hash, check_password_hash
    from models import Role, User, VisitLog
    from forms import UserForm

    # Главная страница - список пользователей
    @app.route('/')
    def index():
        users = User.query.all()  # Получение всех пользователей из БД
        return render_template('index.html', users=users)

    # Страница входа
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            # Обработка данных формы
            username = request.form['username']
            password = request.form['password']
            remember = 'remember' in request.form  # Запомнить пользователя
            
            # Поиск пользователя в БД
            user = User.query.filter_by(username=username).first()
            
            # Проверка пароля
            if user and check_password_hash(user.password_hash, password):
                login_user(user, remember=remember)  # Вход пользователя
                flash('Вы успешно вошли в систему!', 'success')
                next_page = request.args.get('next')  # Перенаправление после входа
                return redirect(next_page or url_for('index'))
            else:
                flash('Неверное имя пользователя или пароль.', 'danger')
        return render_template('login.html', next=request.args.get('next'))

    # Выход из системы
    @app.route('/logout')
    @login_required  # Только для авторизованных
    def logout():
        logout_user()  # Выход пользователя
        flash('Вы вышли из системы.', 'info')
        return redirect(url_for('index'))

    # Создание пользователя
    @app.route('/user/create', methods=['GET', 'POST'])
    @login_required
    def create_user():
        form = UserForm()
        # Заполнение списка ролей для выбора
        form.role_id.choices = [(role.id, role.name) for role in Role.query.all()]
        
        if form.validate_on_submit():  # Если форма валидна
            try:
                # Создание нового пользователя
                user = User(
                    username=form.username.data,
                    password_hash=generate_password_hash(form.password.data),
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

    # Редактирование пользователя (только для админов)
    @app.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
    @login_required
    @check_rights('Администратор')
    def edit_user(user_id):
        user = User.query.get_or_404(user_id)  # 404 если пользователь не найден
        form = UserForm(obj=user)
        form.role_id.choices = [(role.id, role.name) for role in Role.query.all()]
        # Удаление ненужных полей для редактирования
        del form.username
        del form.password
        del form.confirm_password
        
        if form.validate_on_submit():
            try:
                # Обновление данных пользователя
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

    # Удаление пользователя
    @app.route('/user/<int:user_id>/delete', methods=['POST'])
    @login_required
    @check_rights('Администратор')
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

            # Проверка старого пароля
            if not check_password_hash(current_user.password_hash, old_password):
                flash('Старый пароль неверен.', 'danger')
            elif new_password != confirm_password:
                flash('Новые пароли не совпадают.', 'danger')
            elif len(new_password) < 8 or len(new_password) > 128:
                flash('Пароль должен быть от 8 до 128 символов.', 'danger')
            else:
                # Обновление пароля
                current_user.password_hash = generate_password_hash(new_password)
                db.session.commit()
                flash('Пароль успешно изменён.', 'success')
                return redirect(url_for('index'))
        return render_template('change_password.html')

    # Управление ролями
    @app.route('/roles', methods=['GET', 'POST'])
    @login_required
    @check_rights('Администратор')
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
        # Проверка, что роль не используется
        if User.query.filter_by(role_id=role.id).first():
            flash('Невозможно удалить роль, так как она связана с пользователями.', 'danger')
        else:
            db.session.delete(role)
            db.session.commit()
            flash('Роль успешно удалена.', 'success')
        return redirect(url_for('manage_roles'))

    # Просмотр профиля пользователя
    @app.route('/user/<int:user_id>', methods=['GET'])
    @login_required
    @check_rights('Администратор')
    def view_user(user_id):
        user = User.query.get_or_404(user_id)
        return render_template('view_user.html', user=user)

    # Журнал посещений
    @app.route('/visit_logs')
    @login_required
    @check_rights('Администратор')
    def visit_logs():
        return redirect(url_for('visit_logs.index'))

    # Журнал посещений текущего пользователя
    @app.route('/visit_logs/user')
    @login_required
    @check_rights('Пользователь')
    def user_visit_logs():
        logs = VisitLog.query.filter_by(user_id=current_user.id).order_by(VisitLog.created_at.desc()).all()
        return render_template('visit_logs/user_logs.html', logs=logs)

    # Профиль текущего пользователя
    @app.route('/profile', methods=['GET'])
    @login_required
    @check_rights('Пользователь')
    def view_profile():
        return render_template('view_user.html', user=current_user)

    # Редактирование профиля
    @app.route('/profile/edit', methods=['GET', 'POST'])
    @login_required
    @check_rights('Пользователь')
    def edit_profile():
        form = UserForm(obj=current_user)
        # Удаление ненужных полей
        del form.username
        del form.password
        del form.confirm_password
        del form.role_id
        
        if form.validate_on_submit():
            try:
                # Обновление профиля
                current_user.last_name = form.last_name.data
                current_user.first_name = form.first_name.data
                current_user.middle_name = form.middle_name.data
                db.session.commit()
                flash('Ваш профиль успешно обновлён.', 'success')
                return redirect(url_for('view_profile'))
            except Exception as e:
                flash('Ошибка при обновлении профиля.', 'danger')
        return render_template('user_form.html', form=form)

# Загрузчик пользователя для Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(int(user_id))

# Форма пользователя
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

# Запуск приложения
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)  # Запуск в режиме отладки