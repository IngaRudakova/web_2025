# Импорт необходимых модулей и компонентов
from flask import Flask, render_template, send_from_directory
from flask_migrate import Migrate
from sqlalchemy.exc import SQLAlchemyError
from models import db, Category, Image  # Модели БД
from auth import bp as auth_bp, init_login_manager  # Авторизация
from courses import bp as courses_bp  # Логика курсов

# Создание Flask-приложения
app = Flask(__name__)
application = app  # Для совместимости с WSGI-серверами (например, Gunicorn)

# Загрузка конфигурации из файла config.py
app.config.from_pyfile('config.py')

# Инициализация базы данных и миграций
db.init_app(app)
migrate = Migrate(app, db)

# Настройка менеджера аутентификации
init_login_manager(app)

# Обработчик ошибок SQLAlchemy (БД)
@app.errorhandler(SQLAlchemyError)
def handle_sqlalchemy_error(err):
    error_msg = ('Возникла ошибка при подключении к базе данных. '
                 'Повторите попытку позже.')
    return f'{error_msg} (Подробнее: {err})', 500  # Возврат ошибки 500

# Регистрация модулей приложения)
app.register_blueprint(auth_bp)  # Авторизация
app.register_blueprint(courses_bp)  # Курсы

# Главная страница
@app.route('/')
def index():
    # Получаем все категории из БД
    categories = db.session.execute(db.select(Category)).scalars()
    # Рендерим шаблон index.html, передавая категории
    return render_template('index.html', categories=categories)

# Загрузка изображения по ID
@app.route('/images/<image_id>')
def image(image_id):
    # Получаем изображение из БД или возвращаем 404
    img = db.get_or_404(Image, image_id)
    # Отправляем файл из папки загрузок
    return send_from_directory(app.config['UPLOAD_FOLDER'], img.storage_filename)