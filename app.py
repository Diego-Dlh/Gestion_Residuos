#app.py
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from config import Config
from models import db, Usuario, TipoUsuario, Recoleccion,Unidad,RecoleccionResiduo
from datetime import datetime
from flask_migrate import Migrate
from functools import wraps

from flask import render_template, make_response

app = Flask(__name__, static_folder='Static')

app.config.from_object(Config)
db.init_app(app)
migrate = Migrate(app, db)

# Configuración de Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))

@app.route('/', methods=['GET', 'POST'])
def home():
    return redirect(url_for('login'))

# Ruta para el registro de usuario
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        contraseña = request.form['contraseña']

        # Crear nuevo usuario con id_tipo=1
        usuario = Usuario(id_tipo=2, nombre=nombre, correo=correo)
        usuario.set_password(contraseña)  # Aquí el hash debería ser guardado correctamente
        db.session.add(usuario)
        db.session.commit()
        
        flash('Registro exitoso, ahora puedes iniciar sesión.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Ruta para el inicio de sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Verificación de usuario y contraseña
        correo = request.form['correo']
        contraseña = request.form['contraseña']
        
        # Buscar el usuario por correo (o por otro atributo de autenticación)
        usuario = Usuario.query.filter_by(correo=correo).first()
        
        # Verifica si el usuario existe y si la contraseña es correcta
        if usuario and usuario.check_password(contraseña):  # Suponiendo que tienes el método check_password
            login_user(usuario)  # Aquí debes pasar la instancia del usuario, no la clase
            # Redirigir al dashboard correspondiente según el tipo de usuario
            if usuario.id_tipo == 1:
                return redirect(url_for('admin_dashboard'))
            elif usuario.id_tipo == 2:
                return redirect(url_for('usuario_dashboard'))
        else:
            flash('Correo o contraseña incorrectos.', 'danger')

    return render_template('login.html')

# Ruta para el cierre de sesión
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión.')
    return redirect(url_for('login'))

def role_required(role_id):
    def wrapper(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated or current_user.id_tipo != role_id:
                flash("Acceso denegado.", "warning")
                return redirect(url_for('login'))
            return func(*args, **kwargs)
        return decorated_view
    return wrapper

@app.route('/admin_dashboard')
@role_required(1)  # Solo admin
def admin_dashboard():
    return render_template('admin_dashboard.html')

#================================================================================================================================================================================================


from datetime import datetime
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Usuario, Unidad, Recoleccion, TipoResiduo, RecoleccionResiduo

from flask import render_template, redirect, url_for, request, flash
from datetime import datetime
from models import db, Usuario, Recoleccion, RecoleccionResiduo, Unidad, TipoResiduo

# Ruta del dashboard del usuario (asociación)
@app.route('/usuario_dashboard')
@login_required
def usuario_dashboard():
    # Obtener la información de la asociación (usuario)
    asociaciones = current_user.unidades
    
    # Obtener el total de recolecciones por tipo de residuo
    total_recolecciones = {}
    for reco in RecoleccionResiduo.query.join(Recoleccion).join(TipoResiduo).filter(Recoleccion.unidad_id.in_([u.id_unidad for u in asociaciones])).all():
        tipo_residuo = reco.tipo_residuo.nombre
        total_recolecciones[tipo_residuo] = total_recolecciones.get(tipo_residuo, 0) + reco.cantidad
    
    return render_template('usuario_dashboard.html', total_recolecciones=total_recolecciones)

# Ruta para registrar una nueva recolección
@app.route('/registrar_recoleccion', methods=['GET', 'POST'])
@login_required
def registrar_recoleccion():
    if request.method == 'POST':
        unidad_id = request.form['unidad_id']
        tipos_residuos = request.form.getlist('tipo_residuo[]')  # Obtén todos los tipos de residuos
        cantidades = request.form.getlist('cantidad[]')  # Obtén todas las cantidades
        
        # Crear una nueva recolección
        nueva_recoleccion = Recoleccion(
            fecha=datetime.now(),
            unidad_id=unidad_id
        )
        db.session.add(nueva_recoleccion)
        db.session.commit()

        # Registrar cada tipo de residuo y su cantidad asociada
        for tipo_residuo_id, cantidad in zip(tipos_residuos, cantidades):
            reco_residuo = RecoleccionResiduo(
                id_recoleccion=nueva_recoleccion.id_recoleccion,
                id_tipo_residuo=tipo_residuo_id,
                cantidad=cantidad
            )
            db.session.add(reco_residuo)
        
        db.session.commit()
        
        flash('Recolecciones registradas exitosamente.')
        return redirect(url_for('usuario_dashboard'))
    
    # Obtener unidades asignadas para el formulario
    unidades = current_user.unidades
    tipos_residuos = TipoResiduo.query.all()
    return render_template('registrar_recoleccion.html', unidades=unidades, tipos_residuos=tipos_residuos)

from sqlalchemy import extract
from datetime import datetime

@app.route('/recoleccion_por_mes', methods=['GET'])
@login_required
def recoleccion_por_mes():
    # Obtener el mes desde la solicitud GET, si está presente
    mes_filtrado = request.args.get('mes')

    # Si el mes no está especificado, tomamos el mes actual
    if mes_filtrado:
        mes_filtrado = datetime.strptime(mes_filtrado, '%Y-%m')
    else:
        mes_filtrado = datetime.now()

    # Filtrar las recolecciones por mes usando extract()
    recolecciones_mes = {}
    for reco in RecoleccionResiduo.query.join(Recoleccion).join(TipoResiduo).filter(
            extract('month', Recoleccion.fecha) == mes_filtrado.month,
            extract('year', Recoleccion.fecha) == mes_filtrado.year
    ).all():
        mes = reco.recoleccion.fecha.strftime('%Y-%m')
        tipo_residuo = reco.tipo_residuo.nombre
        if mes not in recolecciones_mes:
            recolecciones_mes[mes] = {}
        recolecciones_mes[mes][tipo_residuo] = recolecciones_mes[mes].get(tipo_residuo, 0) + reco.cantidad

    return render_template('recoleccion_por_mes.html', recolecciones_mes=recolecciones_mes)




# Ruta para ver las unidades asignadas a la asociación
@app.route('/view_unidades')
@login_required
def ver_unidades():
    # Asegurarse de que el usuario es una asociación (tipo usuario = 1)
    if current_user.id_tipo != 1:
        flash("Acceso denegado. Solo las asociaciones pueden ver sus unidades.", "warning")
        return redirect(url_for('usuario_dashboard'))

    # Obtener las unidades asignadas al usuario actual (asociación)
    unidades = Unidad.query.filter_by(asociacion_id=current_user.id).all()

    return render_template('view_unidades.html', unidades=unidades)


#================================================================================================================================================================================================

@app.route('/admin_dashboard/create_unidad', methods=['GET', 'POST'])
@role_required(1)  # Solo admin
def create_unidad():
    asociaciones = Usuario.query.filter_by(id_tipo=2).all()  # Obtener todas las asociaciones

    if request.method == 'POST':
        nombre_unidad = request.form['nombre']
        asociacion_id = request.form['asociacion_id']

        if not nombre_unidad or not asociacion_id:
            flash('Todos los campos son obligatorios.', 'danger')
            return redirect(url_for('create_unidad'))

        # Crear y guardar la nueva unidad
        nueva_unidad = Unidad(nombre=nombre_unidad, asociacion_id=asociacion_id)
        db.session.add(nueva_unidad)
        db.session.commit()

        flash('Unidad creada y asignada exitosamente.', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('create_unidad.html', asociaciones=asociaciones)

@app.route('/admin_dashboard/delete_unidad/<int:unidad_id>', methods=['POST'])
@role_required(1)  # Solo admin
def delete_unidad(unidad_id):
    unidad = Unidad.query.get(unidad_id)
    if not unidad:
        flash('Unidad no encontrada.', 'danger')
        return redirect(url_for('admin_dashboard'))

    db.session.delete(unidad)
    db.session.commit()

    flash('Unidad eliminada exitosamente.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin_dashboard/recoleccion', methods=['GET'])
@role_required(1)  # Solo admin
def view_recoleccion():
    asociaciones = Usuario.query.filter_by(id_tipo=1).all()
    recolecciones = Recoleccion.query.all()

    return render_template('view_recoleccion.html', asociaciones=asociaciones, recolecciones=recolecciones)

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/admin_dashboard/asociaciones', methods=['GET'])
@role_required(1)  # Solo admin
def admin_asociaciones():
    asociaciones = Usuario.query.filter_by(id_tipo=2).all()  # Filtrar usuarios de tipo asociación
    return render_template('admin_asociaciones.html', asociaciones=asociaciones)


@app.route('/admin_dashboard/unidades', methods=['GET', 'POST'])
@role_required(1)  # Solo admin
def admin_unidades():
    unidades = Unidad.query.all()
    asociaciones = Usuario.query.filter_by(id_tipo=2).all()  # Asociaciones para asignar a las unidades

    if request.method == 'POST':
        nombre = request.form['nombre']
        asociacion_id = request.form['asociacion_id']

        if not nombre or not asociacion_id:
            flash('Todos los campos son obligatorios.', 'danger')
            return redirect(url_for('admin_unidades'))

        nueva_unidad = Unidad(nombre=nombre, asociacion_id=asociacion_id)
        db.session.add(nueva_unidad)
        db.session.commit()
        flash('Unidad creada exitosamente.', 'success')
        return redirect(url_for('admin_unidades'))

    return render_template('admin_unidades.html', unidades=unidades, asociaciones=asociaciones)


@app.route('/admin_dashboard/unidades/eliminar/<int:unidad_id>', methods=['POST'])
@role_required(1)  # Solo admin
def eliminar_unidad(unidad_id):
    unidad = Unidad.query.get(unidad_id)
    if unidad:
        db.session.delete(unidad)
        db.session.commit()
        flash('Unidad eliminada exitosamente.', 'success')
    else:
        flash('Unidad no encontrada.', 'danger')
    return redirect(url_for('admin_unidades'))


@app.route('/admin_dashboard/unidades/editar/<int:unidad_id>', methods=['GET', 'POST'])
@role_required(1)  # Solo admin
def editar_unidad(unidad_id):
    unidad = Unidad.query.get(unidad_id)
    asociaciones = Usuario.query.filter_by(id_tipo=2).all()  # Asociaciones para asignar a las unidades

    if not unidad:
        flash('Unidad no encontrada.', 'danger')
        return redirect(url_for('admin_unidades'))

    if request.method == 'POST':
        unidad.nombre = request.form['nombre']
        unidad.asociacion_id = request.form['asociacion_id']
        db.session.commit()
        flash('Unidad actualizada exitosamente.', 'success')
        return redirect(url_for('admin_unidades'))

    return render_template('editar_unidad.html', unidad=unidad, asociaciones=asociaciones)

@app.route('/admin_dashboard/asociaciones/eliminar/<int:asociacion_id>', methods=['POST'])
@role_required(1)  # Solo admin
def eliminar_asociacion(asociacion_id):
    asociacion = Usuario.query.get(asociacion_id)
    if asociacion:
        db.session.delete(asociacion)
        db.session.commit()
        flash('Asociación eliminada exitosamente.', 'success')
    else:
        flash('Asociación no encontrada.', 'danger')
    return redirect(url_for('admin_asociaciones'))


@app.route('/admin_dashboard/asociaciones/editar/<int:asociacion_id>', methods=['GET', 'POST'])
@role_required(1)  # Solo admin
def editar_asociacion(asociacion_id):
    asociacion = Usuario.query.get(asociacion_id)

    if not asociacion:
        flash('Asociación no encontrada.', 'danger')
        return redirect(url_for('admin_asociaciones'))

    if request.method == 'POST':
        asociacion.nombre = request.form['nombre']
        asociacion.correo = request.form['correo']
        db.session.commit()
        flash('Asociación actualizada exitosamente.', 'success')
        return redirect(url_for('admin_asociaciones'))

    return render_template('editar_asociacion.html', asociacion=asociacion)

@app.route('/configuracion', methods=['GET', 'POST'])
@login_required
def configuracion():
    if request.method == 'POST':
        # Obtener la nueva contraseña del formulario
        nueva_contraseña = request.form['nueva_contraseña']
        
        # Validar que la contraseña no esté vacía
        if not nueva_contraseña:
            flash("La nueva contraseña no puede estar vacía.", "danger")
            return redirect(url_for('configuracion'))

        # Establecer la nueva contraseña
        current_user.set_password(nueva_contraseña)
        db.session.commit()
        
        flash("Contraseña cambiada exitosamente.", "success")
        return redirect(url_for('usuario_dashboard'))

    return render_template('configuracion.html')

@app.route('/cambiar_contraseña', methods=['GET', 'POST'])
@login_required
def cambiar_contraseña():
    if request.method == 'POST':
        nueva_contraseña = request.form['nueva_contraseña']
        confirmacion_contraseña = request.form['confirmacion_contraseña']
        
        if nueva_contraseña == confirmacion_contraseña:
            current_user.set_password(nueva_contraseña)
            db.session.commit()
            flash('Contraseña cambiada con éxito.')
            return redirect(url_for('usuario_dashboard'))
        else:
            flash('Las contraseñas no coinciden.', 'danger')
    
    return render_template('cambiar_contraseña.html')


#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Crea las tablas en la base de datos si no existen
        app.run(host='0.0.0.0', port=8080)
    app.run(debug=False)
