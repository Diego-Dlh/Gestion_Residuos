# config.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'una_llave_secreta_para_flask'
    #SQLALCHEMY_DATABASE_URI = 'postgresql+pg8000://postgres:123456@localhost/Sistema_recoleccion'
    #SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql://gestionresiduosbd_user:MXfrd6DNzK0o2iRzdWnvubhDuuAnW7Az@dpg-ctmtthhopnds73fildpg-a/gestionresiduosbd")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql://gestionresiduosbdv2_user:xCmhebEXoYnHf4J2fdgCwRqYy0JdwL4F@dpg-cu9qvvaj1k6c73e0eotg-a/gestionresiduosbdv2")
    SQLALCHEMY_TRACK_MODIFICATIONS = False