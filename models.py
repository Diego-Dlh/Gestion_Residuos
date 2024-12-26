#models.py
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import UserMixin

db = SQLAlchemy()
bcrypt = Bcrypt()

class TipoUsuario(db.Model):
    __tablename__ = 'tipos_usuario'
    id_tipo_usuario = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id_usuario = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    contraseña = db.Column(db.String(255), nullable=False)
    id_tipo = db.Column(db.Integer, db.ForeignKey('tipos_usuario.id_tipo_usuario'), nullable=False)
    tipo_usuario = db.relationship('TipoUsuario', backref=db.backref('usuarios', lazy=True))
    
# Propiedad para Flask-Login
    @property
    def id(self):
        return self.id_usuario

    def set_password(self, password):
        self.contraseña = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.contraseña, password)

class TipoResiduo(db.Model):
    __tablename__ = 'tipos_residuos'
    id_tipo_residuo = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)

class Unidad(db.Model):
    __tablename__ = 'unidades'
    id_unidad = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    asociacion_id = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)
    asociacion = db.relationship('Usuario', backref=db.backref('unidades', lazy=True))

class Recoleccion(db.Model):
    __tablename__ = 'recolecciones'
    id_recoleccion = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    unidad_id = db.Column(db.Integer, db.ForeignKey('unidades.id_unidad'), nullable=False)
    unidad = db.relationship('Unidad', backref=db.backref('recolecciones', lazy=True))

class RecoleccionResiduo(db.Model):
    __tablename__ = 'recoleccion_residuos'
    id_recoleccion = db.Column(db.Integer, db.ForeignKey('recolecciones.id_recoleccion'), primary_key=True)
    id_tipo_residuo = db.Column(db.Integer, db.ForeignKey('tipos_residuos.id_tipo_residuo'), primary_key=True)
    cantidad = db.Column(db.Numeric(10, 2), default=0.00)
    recoleccion = db.relationship('Recoleccion', backref=db.backref('residuos', lazy=True))
    tipo_residuo = db.relationship('TipoResiduo', backref=db.backref('recolecciones_residuos', lazy=True))

   
