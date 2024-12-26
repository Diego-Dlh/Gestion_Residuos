# config.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'una_llave_secreta_para_flask'
    SQLALCHEMY_DATABASE_URI = 'postgresql+pg8000://postgres:123456@localhost/Sistema_recoleccion'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
