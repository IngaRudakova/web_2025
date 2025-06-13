

from flask import Blueprint, render_template, request, make_response, current_app, flash, redirect, url_for
from flask_login import current_user, login_required
from models import VisitLog, User  
from sqlalchemy import func
from app import check_rights 
import csv
import io

# Создание Blueprint для работы с журналом посещений
visit_logs_bp = Blueprint('visit_logs', __name__, url_prefix='/visit_logs')
db = None  

# Логирование посещений перед каждым запросом
@visit_logs_bp.before_app_request
def log_visit():
    if request.endpoint != 'static':  
        with current_app.app_context():  
            log = VisitLog(
                path=request.path, 
                user_id=current_user.id if current_user.is_authenticated else None  
            )
            visit_logs_bp.db.session.add(log) 
            visit_logs_bp.db.session.commit()  

# Главная страница журнала посещений с пагинацией
@visit_logs_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int) 
    logs = visit_logs_bp.db.session.query(VisitLog).order_by(VisitLog.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('visit_logs/index.html', logs=logs)

# Отчет по страницам с количеством посещений
@visit_logs_bp.route('/by_pages')
@login_required
@check_rights('Администратор')  
def by_pages():
    stats = visit_logs_bp.db.session.query(
        VisitLog.path, func.count(VisitLog.id).label('visits')
    ).group_by(VisitLog.path).order_by(func.count(VisitLog.id).desc()).all()
    return render_template('visit_logs/by_pages.html', stats=stats)

# Отчет по пользователям с количеством посещений
@visit_logs_bp.route('/by_users')
@login_required
@check_rights('Администратор')  
def by_users():
    stats = visit_logs_bp.db.session.query(
        VisitLog.user_id, func.count(VisitLog.id).label('visits')
    ).group_by(VisitLog.user_id).order_by(func.count(VisitLog.id).desc()).all()

    # Обработка данных для включения имен пользователей
    processed_stats = []
    for stat in stats:
        user = visit_logs_bp.db.session.query(User).get(stat[0])
        full_name = user.full_name if user else 'Неаутентифицированный пользователь'
        processed_stats.append((full_name, stat[1]))

    return render_template('visit_logs/by_users.html', stats=processed_stats)

# Экспорт отчета по страницам в CSV
@visit_logs_bp.route('/export_pages')
@login_required
@check_rights('Администратор') 
def export_pages():
    stats = visit_logs_bp.db.session.query(
        VisitLog.path, func.count(VisitLog.id).label('visits')
    ).group_by(VisitLog.path).all()
    output = io.StringIO()  
    writer = csv.writer(output)
    writer.writerow(['Страница', 'Количество посещений'])
    writer.writerows(stats)
    response = make_response(output.getvalue().encode('utf-8-sig'))
    response.headers['Content-Disposition'] = 'attachment; filename=pages_report.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response

# Экспорт отчета по пользователям в CSV
@visit_logs_bp.route('/export_users')
@login_required
@check_rights('Администратор') 
def export_users():
    stats = visit_logs_bp.db.session.query(
        VisitLog.user_id, func.count(VisitLog.id).label('visits')
    ).group_by(VisitLog.user_id).all()
    output = io.StringIO() 
    writer = csv.writer(output)
    writer.writerow(['Пользователь', 'Количество посещений'])
    for stat in stats:
        user = visit_logs_bp.db.session.query(User).get(stat[0])
        writer.writerow([user.full_name if user else 'Неаутентифицированный пользователь', stat[1]])
    response = make_response(output.getvalue().encode('utf-8-sig')) # Получение содержимого CSV
    response.headers['Content-Disposition'] = 'attachment; filename=users_report.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response

# Очистка журнала посещений
@visit_logs_bp.route('/clear', methods=['POST'])
@login_required
@check_rights('Администратор')  
def clear_logs():
    with current_app.app_context():
        visit_logs_bp.db.session.query(VisitLog).delete()  # Удаление всех записей журнала
        visit_logs_bp.db.session.commit()
        flash('Журнал посещений успешно очищен.', 'success')
    return redirect(url_for('visit_logs.index'))
