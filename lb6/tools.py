
import hashlib  # Для хеширования файлов
import uuid  # Для генерации уникальных ID
import os  # Для работы с файловой системой
from werkzeug.utils import secure_filename  # Для безопасного сохранения файлов
from flask import current_app  # Для доступа к конфигурации Flask
from models import db, Course, Image  # Модели базы данных

# Класс для фильтрации курсов
class CoursesFilter:
    def __init__(self, name, category_ids):
        self.name = name  # Название курса для поиска
        self.category_ids = category_ids  # ID категорий для фильтрации
        self.query = db.select(Course)  # Базовый SQL-запрос

    def perform(self):
        # Применяем все фильтры и сортируем по дате создания
        self.__filter_by_name()
        self.__filter_by_category_ids()
        return self.query.order_by(Course.created_at.desc())

    def __filter_by_name(self):
        # Фильтрация по имени (регистронезависимый поиск)
        if self.name:
            self.query = self.query.filter(
                Course.name.ilike('%' + self.name + '%'))

    def __filter_by_category_ids(self):
        # Фильтрация по ID категорий
        if self.category_ids:
            self.query = self.query.filter(
                Course.category_id.in_(self.category_ids))

# Класс для сохранения изображений
class ImageSaver:
    def __init__(self, file):
        self.file = file  # Файл изображения

    def save(self):
        # Проверяем, есть ли такое изображение уже в базе
        self.img = self.__find_by_md5_hash()
        if self.img is not None:
            return self.img  # Возвращаем существующее изображение
        
        # Создаем новую запись об изображении
        file_name = secure_filename(self.file.filename)  # Безопасное имя файла
        self.img = Image(
            id=str(uuid.uuid4()),  # Генерируем уникальный ID
            file_name=file_name,
            mime_type=self.file.mimetype,
            md5_hash=self.md5_hash)
        
        self.file.save(
            os.path.join(current_app.config['UPLOAD_FOLDER'],
                         self.img.storage_filename))
        
        # Сохраняем данные в БД
        db.session.add(self.img)
        db.session.commit()
        return self.img

    def __find_by_md5_hash(self):
        # для проверки дубликатов
        self.md5_hash = hashlib.md5(self.file.read()).hexdigest()
        self.file.seek(0)  # Возвращаем указатель файла в начало
        # Ищем изображение с таким же хешем в БД
        return db.session.execute(db.select(Image).filter(Image.md5_hash == self.md5_hash)).scalar()