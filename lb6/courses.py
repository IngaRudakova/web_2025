# Импорт необходимых модулей
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user  # Для работы с аутентификацией
from sqlalchemy.exc import IntegrityError  # Ошибки целостности БД
from models import db, Course, Category, User, Review  # Модели данных
from tools import CoursesFilter, ImageSaver  # Вспомогательные инструменты
from sqlalchemy import desc  # Сортировка по убыванию

# Создание Blueprint для маршрутов курсов
bp = Blueprint('courses', __name__, url_prefix='/courses')

# Параметры курса, которые можно получить из формы
COURSE_PARAMS = [
    'author_id', 'name', 'category_id', 'short_desc', 'full_desc'
]

# Функция для получения параметров курса из формы
def params():
    return { p: request.form.get(p) or None for p in COURSE_PARAMS }

# Функция для получения параметров поиска
def search_params():
    return {
        'name': request.args.get('name'),  # Поиск по названию
        'category_ids': [x for x in request.args.getlist('category_ids') if x],  # Фильтр по категориям
    }

# Главная страница со списком курсов
@bp.route('/')
def index():
    # Применяем фильтры к курсам
    courses = CoursesFilter(**search_params()).perform()
    # Пагинация результатов
    pagination = db.paginate(courses)
    courses = pagination.items
    # Получаем все категории для фильтра
    categories = db.session.execute(db.select(Category)).scalars()
    return render_template('courses/index.html',
                           courses=courses,
                           categories=categories,
                           pagination=pagination,
                           search_params=search_params())

# Страница создания нового курса
@bp.route('/new')
@login_required  # Только для авторизованных пользователей
def new():
    # Создаем пустой курс
    course = Course()
    # Получаем все категории и пользователей для выбора
    categories = db.session.execute(db.select(Category)).scalars()
    users = db.session.execute(db.select(User)).scalars()
    return render_template('courses/new.html',
                           categories=categories,
                           users=users,
                           course=course)

# Обработчик создания курса
@bp.route('/create', methods=['POST'])
@login_required
def create():
    # Получаем загруженное изображение
    f = request.files.get('background_img')
    img = None
    course = Course()
    try:
        # Если изображение загружено - сохраняем его
        if f and f.filename:
            img = ImageSaver(f).save()

        # Создаем курс с параметрами из формы
        image_id = img.id if img else None
        course = Course(**params(), background_image_id=image_id)
        db.session.add(course)
        db.session.commit()
    except IntegrityError as err:
        # Обработка ошибок целостности БД
        flash(f'Возникла ошибка при записи данных в БД. Проверьте корректность введённых данных. ({err})', 'danger')
        db.session.rollback()
        # Повторно показываем форму с введенными данными
        categories = db.session.execute(db.select(Category)).scalars()
        users = db.session.execute(db.select(User)).scalars()
        return render_template('courses/new.html',
                            categories=categories,
                            users=users,
                            course=course)

    # Сообщение об успешном создании
    flash(f'Курс {course.name} был успешно добавлен!', 'success')
    return redirect(url_for('courses.index'))

# Страница отзывов о курсе
@bp.route('/<int:course_id>/reviews', methods=['GET', 'POST'])
def reviews(course_id):
    # Получаем курс или 404
    course = db.get_or_404(Course, course_id)
    # Параметр сортировки отзывов
    sort_order = request.args.get('sort', 'new')
    query = db.select(Review).filter_by(course_id=course_id)

    # Применяем сортировку
    if sort_order == 'positive':
        query = query.order_by(Review.rating.desc())  # Сначала положительные
    elif sort_order == 'negative':
        query = query.order_by(Review.rating.asc())  # Сначала отрицательные
    else:
        query = query.order_by(desc(Review.created_at))  #  новые

    # Пагинация отзывов
    pagination = db.paginate(query)
    reviews = pagination.items

    # Обработка отправки нового отзыва
    if request.method == 'POST':
        if current_user.is_authenticated:
            rating = int(request.form.get('rating'))
            text = request.form.get('text')
            # Проверяем, не оставлял ли пользователь уже отзыв
            existing_review = db.session.execute(
                db.select(Review).filter_by(course_id=course_id, user_id=current_user.id)
            ).scalar()

            if existing_review:
                flash('Вы уже оставили отзыв для этого курса.', 'warning')
            else:
                # Создаем новый отзыв и обновляем рейтинг курса
                review = Review(rating=rating, text=text, course_id=course_id, user_id=current_user.id)
                course.rating_sum += rating
                course.rating_num += 1
                db.session.add(review)
                db.session.commit()
                flash('Ваш отзыв был успешно добавлен!', 'success')
                return redirect(url_for('courses.reviews', course_id=course_id))

    return render_template('courses/reviews.html', 
                         course=course, 
                         reviews=reviews, 
                         pagination=pagination, 
                         sort_order=sort_order)

# Страница просмотра курса
@bp.route('/<int:course_id>')
def show(course_id):
    # Получаем курс или 404
    course = db.get_or_404(Course, course_id)
    # Получаем 5 последних отзывов
    reviews = db.session.execute(
        db.select(Review).filter_by(course_id=course_id).order_by(desc(Review.created_at)).limit(5)
    ).scalars()
    return render_template('courses/show.html', course=course, reviews=reviews)