from flask import Flask, request, render_template
import re
from flask import redirect, url_for

app = Flask(__name__)  # Создаем экземпляр Flask-приложения


@app.route("/url-params", methods=["GET"])  # Определяем маршрут для отображения параметров URL
def url_params():
    params = request.args  # Получаем параметры URL из запроса  
    return render_template('url_params.html', params=params)  # Отображаем шаблон с параметрами URL

@app.route("/headers", methods=["GET"])  # Определяем маршрут для отображения заголовков запроса
# /хэдерс - это обьект запроса Request - тут заголовки
def headers():
    headers = request.headers  # Получаем заголовки запроса <- это объект Request - содержит информацию о входящем HTTP-запросе.
    return render_template('headers.html', headers=headers)  # Отображаем шаблон с заголовками запроса

@app.route("/cookies", methods=["GET"])  # Определяем маршрут для отображения cookies
def cookies():
    cookies = request.cookies  # Получаем cookies из запроса <- это объект Request - содержит информацию о входящем HTTP-запросе.
    return render_template('cookies.html', cookies=cookies)  # Отображаем шаблон с cookies


@app.route("/")  # Определяем маршрут для корневого URL
def index():
    return redirect(url_for('url_params'))  # Перенаправляем на страницу с параметрами URL

@app.route("/form-data", methods=["GET", "POST"])  # Определяем маршрут для отображения параметров формы
def form_data():
    form_data = request.form if request.method == "POST" else {}  # Получаем данные формы, если метод POST
    return render_template('form_data.html', form_data=form_data)  # Отображаем шаблон с данными формы

@app.route("/phone-validation", methods=["GET", "POST"])  # Определяем маршрут для валидации номера телефона
def phone_validation():
    phone = ""  # Инициализируем переменную для хранения номера телефона
    error = None  # Инициализируем переменную для хранения сообщения об ошибке
    formatted_phone = None  # Инициализируем переменную для хранения отформатированного номера

    if request.method == "POST":  # Если метод запроса POST
        phone = request.form.get("phone", "")  # Получаем номер телефона из формы
        error = validate_phone(phone)  # Проверяем корректность номера

        if not error:  # Если ошибок нет
            formatted_phone = format_phone(phone)  # Форматируем номер

    return render_template('phone_validation.html', phone=phone, error=error, formatted_phone=formatted_phone)  # Отображаем шаблон с данными

def validate_phone(phone):
    """Проверяет корректность введенного номера телефона."""
    # Разрешённые символы: цифры, пробелы, круглые скобки, дефисы, точки, +
    if not re.match(r'^[\d\s\(\)\-\.\\+]+$', phone): # Объект Response (re.) используется для отправки ответа клиенту.
        return "Недопустимый ввод. В номере телефона встречаются недопустимые символы."

    # Извлекаем только цифры
    digits = re.sub(r'\D', '', phone)

    # Проверка количества цифр
    if digits.startswith("7") or digits.startswith("8"):
        if len(digits) != 11:
            return "Недопустимый ввод. Неверное количество цифр."
    elif len(digits) != 10:
        return "Недопустимый ввод. Неверное количество цифр."

    return None  # Ошибок нет

def format_phone(digits):
    """Преобразует номер к формату 8-***-***-**-**"""
    digits = re.sub(r'\D', '', digits)  # Убираем всё, кроме цифр
    if len(digits) == 10:
        digits = "8" + digits  # Добавляем 8 в начало, если длина 10
    elif digits.startswith("7"):
        digits = "8" + digits[1:]  # Заменяем +7 на 8

    return f"{digits[0]}-{digits[1:4]}-{digits[4:7]}-{digits[7:9]}-{digits[9:11]}"

if __name__ == '__main__':
    app.run(debug=True)  # Запускаем приложение в режиме отладки
