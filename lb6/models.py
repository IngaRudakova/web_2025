# Импорт необходимых модулей
import os
from typing import Optional, Union, List  # Аннотации типов
from datetime import datetime  # Работа с датой и временем
import sqlalchemy as sa  # SQLAlchemy core
from werkzeug.security import check_password_hash, generate_password_hash  # Хеширование паролей
from flask_login import UserMixin  # Миксин для пользователей Flask-Login
from flask import url_for  # Генерация URL
from flask_sqlalchemy import SQLAlchemy  # Flask-SQLAlchemy интеграция
from sqlalchemy.orm import DeclarativeBase  # Базовый класс для моделей
from sqlalchemy.orm import Mapped, mapped_column, relationship  # ORM mapping
from sqlalchemy import String, ForeignKey, DateTime, Text, Integer, MetaData  # Типы полей


# Базовый класс для всех моделей с настройкой именования ограничений
class Base(DeclarativeBase):
    metadata = MetaData(naming_convention={
        "ix": 'ix_%(column_0_label)s',  # Именование индексов
        "uq": "uq_%(table_name)s_%(column_0_name)s",  # Уникальные ограничения
        "ck": "ck_%(table_name)s_%(constraint_name)s",  # Check-ограничения
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",  # Внешние ключи
        "pk": "pk_%(table_name)s"  # Первичные ключи
    })

# Инициализация SQLAlchemy с нашим базовым классом
db = SQLAlchemy(model_class=Base)


# Модель категорий (иерархическая структура)
class Category(Base):
    __tablename__ = 'categories'

    id = mapped_column(Integer, primary_key=True)  # ID категории
    name: Mapped[str] = mapped_column(String(100))  # Название категории
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"))  # Родительская категория (для иерархии)

    def __repr__(self):
        return '<Category %r>' % self.name  # Строковое представление


# Модель пользователя с поддержкой Flask-Login
class User(Base, UserMixin):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)  # ID пользователя
    first_name: Mapped[str] = mapped_column(String(100))  # Имя
    last_name: Mapped[str] = mapped_column(String(100))  # Фамилия
    middle_name: Mapped[Optional[str]] = mapped_column(String(100))  # Отчество (необязательное)
    login: Mapped[str] = mapped_column(String(100), unique=True)  # Логин (уникальный)
    password_hash: Mapped[str] = mapped_column(String(200))  # Хеш пароля
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)  # Дата создания

    # Установка пароля (с хешированием)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Проверка пароля
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Полное имя пользователя (фамилия + имя + отчество)
    @property
    def full_name(self):
        return ' '.join([self.last_name, self.first_name, self.middle_name or ''])

    def __repr__(self):
        return '<User %r>' % self.login  # Строковое представление


# Модель курса
class Course(Base):
    __tablename__ = 'courses'

    id: Mapped[int] = mapped_column(primary_key=True)  # ID курса
    name: Mapped[str] = mapped_column(String(100))  # Название курса
    short_desc: Mapped[str] = mapped_column(Text)  # Краткое описание
    full_desc: Mapped[str] = mapped_column(Text)  # Полное описание
    rating_sum: Mapped[int] = mapped_column(default=0)  # Сумма оценок
    rating_num: Mapped[int] = mapped_column(default=0)  # Количество оценок
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))  # ID категории
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))  # ID автора
    background_image_id: Mapped[str] = mapped_column(ForeignKey("images.id"))  # ID фонового изображения
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)  # Дата создания

    # Связи с другими моделями
    author: Mapped["User"] = relationship()  # Автор курса
    category: Mapped["Category"] = relationship(lazy=False)  # Категория (загружается сразу)
    bg_image: Mapped["Image"] = relationship()  # Фоновое изображение

    def __repr__(self):
        return '<Course %r>' % self.name  # Строковое представление

    # Средний рейтинг курса
    @property
    def rating(self):
        if self.rating_num > 0:
            return self.rating_sum / self.rating_num
        return 0  # Если нет оценок


# Модель изображения
class Image(db.Model):
    __tablename__ = 'images'

    id: Mapped[str] = mapped_column(String(100), primary_key=True)  # ID изображения 
    file_name: Mapped[str] = mapped_column(String(100))  # Оригинальное имя файла
    mime_type: Mapped[str] = mapped_column(String(100))  # MIME-тип
    md5_hash: Mapped[str] = mapped_column(String(100), unique=True)  # Хеш файла (для проверки дубликатов)
    object_id: Mapped[Optional[int]]  # ID связанного объекта
    object_type: Mapped[Optional[str]] = mapped_column(String(100))  # Тип связанного объекта
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)  # Дата создания

    def __repr__(self):
        return '<Image %r>' % self.file_name  # Строковое представление

    # Имя файла в хранилище 
    @property
    def storage_filename(self):
        _, ext = os.path.splitext(self.file_name)
        return self.id + ext

    # URL для доступа к изображению
    @property
    def url(self):
        return url_for('image', image_id=self.id)


# Модель отзыва о курсе
class Review(Base):
    __tablename__ = 'reviews'

    id: Mapped[int] = mapped_column(primary_key=True)  # ID отзыва
    rating: Mapped[int] = mapped_column(nullable=False)  # Оценка (1-5)
    text: Mapped[str] = mapped_column(Text, nullable=False)  # Текст отзыва
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)  # Дата создания
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))  # ID курса
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))  # ID пользователя

    # Связи с другими моделями
    course: Mapped["Course"] = relationship()  # Курс, к которому относится отзыв
    user: Mapped["User"] = relationship()  # Автор отзыва

    def __repr__(self):
        return f'<Review {self.id} - {self.rating}>'  # Строковое представление