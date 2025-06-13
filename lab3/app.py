# Импорт необходимых модулей Flask и связанных библиотек
from flask import Flask, render_template, session, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

# Создание экземпляра Flask приложения
app = Flask(__name__)
# Установка секретного ключа для подписи сессий 
app.secret_key = 'my_secret_key'  
# Установка времени жизни постоянной сессии (1 день)
app.permanent_session_lifetime = datetime.timedelta(days=1)

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)  # Инициализация LoginManager с приложением
login_manager.login_view = 'login'  # Указание view для страницы входа

# Простое хранилище пользователей в памяти 
users = {
    "user": generate_password_hash("qwerty"),
    "inga": generate_password_hash("inga")  # Хранение пароля в виде хеша
}

# Класс пользователя, наследуемый от UserMixin (предоставляет стандартные методы для Flask-Login)
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# Функция загрузки пользователя (требуется для Flask-Login)
@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Главная страница
@app.route('/')
def index():
    return render_template('index.html')

# Страница счетчика посещений (использует сессии)
@app.route('/counter')
def counter():
    if 'visit_count' not in session:
        session['visit_count'] = 0
    session['visit_count'] += 1
    return render_template('count.html', count=session['visit_count'])

# Страница входа с обработкой GET и POST запросов
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = 'remember' in request.form  # Флаг "запомнить меня"
        
        # Проверка существования пользователя и соответствия пароля
        if username in users and check_password_hash(users[username], password):
            user = User(username)
            login_user(user, remember=remember)  # Вход пользователя
            flash('Вы успешно вошли в систему!', 'success')
            next_page = request.args.get('next')
            # Перенаправление на запрашиваемую страницу или главную
            return redirect(next_page or url_for('index'))  
        else:
            flash('Неверное имя пользователя или пароль.', 'danger')
    return render_template('login.html', next=request.args.get('next'))

# Выход из системы (доступен только авторизованным пользователям)
@app.route('/logout')
@login_required
def logout():
    logout_user()  # Выход пользователя
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('index'))

# Защищенная страница (только для авторизованных)
@app.route('/secret')
@login_required
def secret():
    return render_template('secret_page.html')

# Обработчик для неавторизованных запросов
@login_manager.unauthorized_handler
def unauthorized():
    flash('Для доступа к запрашиваемой странице необходимо пройти процедуру аутентификации.', 'warning')
    next_page = request.args.get('next') or request.full_path
    # Перенаправление на страницу входа с сохранением запрашиваемого URL
    return redirect(url_for('login', next=next_page))


if __name__ == '__main__':
    app.run(debug=True)