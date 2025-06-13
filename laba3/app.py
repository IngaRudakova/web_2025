
# Импорт необходимых модулей
import random
from flask import Flask, render_template
from faker import Faker  # Библиотека для генерации фейковых данных
from flask import Flask, request, render_template
# Flask - основной класс для создания веб-приложения
# request - объект для работы с входящими HTTP-запросами
# render_template - функция для генерации HTML из шаблонов (Передавать переменные в шаблоны/Наследовать шаблоны (базовый шаблон + дочерние))

# inja2 - шаблонизатор
# Генерирует HTML на сервере, подставляя динамические данные.

# {{ выражение }}	Вывод значения	{{ user.name }}
# {% команда %}	Логика (циклы, условия, блоки)	{% for item in list %}
# {# комментарий #}	Комментарии (не выводятся в HTML)	{# Это не отобразится #}

# 	{{ }}	            {% %}
# Вывод значений	    Управляющие конструкции
# {{ variable }}	         {% if ... %}, {% for %}
# Результат выводится в HTML	 Не выводится, только логика



# Инициализация Faker для генерации тестовых данных
fake = Faker()

# Создание Flask-приложения
app = Flask(__name__)
application = app  # Для совместимости с некоторыми хостингами

# Список идентификаторов изображений для постов
images_ids = [
    '7d4e9175-95ea-4c5f-8be5-92a6b708bb3c',
    '2d2ab7df-cdbc-48a8-a936-35bba702def5',
    '6e12f3de-d5fd-4ebb-855b-8cbc485278b7',
    'afc2cfe7-5cac-4b80-9b9a-d5c65ef0c728',
    'cab5b7f2-774e-4884-a200-0c0180fa777f'
]

def generate_comments(replies=True):
    """
    Генерирует список случайных комментариев
    :param replies: флаг, указывающий нужно ли генерировать ответы на комментарии
    :return: список комментариев
    """
    comments = []
    # Генерация от 1 до 3 комментариев
    for i in range(random.randint(1, 3)):
        comment = {
            'author': fake.name(),  # Случайное имя автора
            'text': fake.text()     # Случайный текст комментария
        }
        # Рекурсивно генерируем ответы, если нужно
        if replies:
            comment['replies'] = generate_comments(replies=False)
        comments.append(comment)
    return comments

def generate_post(i):
    """
    Генерирует данные для поста
    :param i: индекс поста (для выбора изображения)
    :return: словарь с данными поста
    """
    return {
        'title': fake.sentence(),  # Случайный заголовок
        'text': fake.paragraph(nb_sentences=100),  # Длинный случайный текст
        'author': fake.name(),  # Случайное имя автора
        'date': fake.date_time_between(start_date='-2y', end_date='now'),  # Дата за последние 2 года
        'image_id': f'{images_ids[i]}.jpg',  # ID изображения с расширением
        'comments': generate_comments()  # Сгенерированные комментарии
    }

# Генерация списка из 5 постов, отсортированных по дате (новые сначала)
posts_list = sorted(
    [generate_post(i) for i in range(5)],
    key=lambda p: p['date'],
    reverse=True
)

# Браузер делает запрос → Flask обрабатывает маршрут
# View-функция получает данные (из БД/API и т.д.)
# Данные передаются в шаблон через render_template()
# Jinja2 рендерит HTML с подставленными значениями
# Готовый HTML отправляется клиенту

# Маршрут для главной страницы
# Декораторы в Python — это функции, которые принимают другую функцию в качестве аргумента,
#  добавляют к ней дополнительную функциональность и возвращают функцию с измененным поведением.

# Декоратор @app.route() связывает URL-адрес с функцией, которая должна обрабатывать запрос к этому адресу.
@app.route('/')  # Декоратор для определения маршрута / Функции-обёртки, модифицирующие поведение других функций.
def index():
    return render_template('index.html')

# Маршрут для страницы со списком постов
@app.route('/posts')
def posts():
    return render_template(
        'posts.html',
        title='Посты',
        posts=posts_list  # Передаем список постов в шаблон
    )

# Маршрут для страницы конкретного поста
@app.route('/posts/<int:index>')
def post(index):
    p = posts_list[index]  # Получаем пост по индексу
    return render_template(
        'post.html',
        title=p['title'],  # Передаем заголовок поста
        post=p            # Передаем весь пост
    )

# Маршрут для страницы "Об авторе"
@app.route('/about')
def about():
    return render_template('about.html', title='Об авторе')

# Запуск приложения
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=9999, debug=True)

    # фласк - недостатки - нет админ панели как в джанго
    #  приемущества - Поддерживает наследование шаблонов /  интегрирован во Flasк



    # Маршруты (routes) в Flask — это механизм, который связывает URL-адреса с функциями-обработчиками (views).
    #  Они определяют, какая функция будет выполняться при переходе пользователя на определённый путь (например,
    #  /, /about, /user/123).