import os

SECRET_KEY = 'secret-key'

SQLALCHEMY_DATABASE_URI = 'sqlite:///project.db' # Путь к SQL
SQLALCHEMY_ECHO = True
SQLALCHEMY_TRACK_MODIFICATIONS = False

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media', 'images')