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
from flask import session  # Asegúrate de importar session

@app.route('/registrar_recoleccion', methods=['GET', 'POST'])
@login_required
def registrar_recoleccion():
    if 'recolecciones_temporales' not in session:
        session['recolecciones_temporales'] = []

    if request.method == 'POST':
        unidad_id = request.form['unidad_id']
        tipos_residuos = request.form.getlist('tipo_residuo[]')
        cantidades = request.form.getlist('cantidad[]')

        # Guardar en la base de datos
        nueva_recoleccion = Recoleccion(
            fecha=datetime.now(),
            unidad_id=unidad_id
        )
        db.session.add(nueva_recoleccion)
        db.session.commit()

        for tipo_residuo_id, cantidad in zip(tipos_residuos, cantidades):
            reco_residuo = RecoleccionResiduo(
                id_recoleccion=nueva_recoleccion.id_recoleccion,
                id_tipo_residuo=tipo_residuo_id,
                cantidad=cantidad
            )
            db.session.add(reco_residuo)

            # También guardamos en la sesión temporal para mostrar en pantalla
            session['recolecciones_temporales'].append({
                'unidad_id': unidad_id,
                'unidad_nombre': Unidad.query.get(unidad_id).nombre,
                'tipo_residuo_id': tipo_residuo_id,
                'tipo_residuo_nombre': TipoResiduo.query.get(tipo_residuo_id).nombre,
                'cantidad': cantidad
            })

        db.session.commit()
        session.modified = True  # Necesario para actualizar la sesión
        flash('Recolección registrada exitosamente.', 'success')
        return redirect(url_for('registrar_recoleccion'))

    unidades = current_user.unidades
    tipos_residuos = TipoResiduo.query.all()
    recolecciones_temporales = session.get('recolecciones_temporales', [])
    return render_template('registrar_recoleccion.html', unidades=unidades, tipos_residuos=tipos_residuos, recolecciones_temporales=recolecciones_temporales)

@app.route('/cancelar_registro')
@login_required
def cancelar_registro():
    session.pop('recolecciones_temporales', None)  # Elimina los registros temporales de sesión
    return redirect(url_for('usuario_dashboard'))


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
@login_required
@role_required(1)  # Asegúrate de que el usuario sea admin
def view_recoleccion():
    # Obtener los parámetros de la consulta
    mes = request.args.get('mes', '')  # Si no hay mes, se usa una cadena vacía
    asociacion_id = request.args.get('asociacion', '')

    # Convertir asociacion_id a entero si está presente
    if asociacion_id:
        try:
            asociacion_id = int(asociacion_id)
        except ValueError:
            flash('ID de asociación no válido', 'error')
            return redirect(url_for('view_recoleccion'))

    # Consultar las recolecciones, solo filtrando por asociación si se proporciona
    query = db.session.query(Recoleccion).join(Unidad)

    if asociacion_id:
        query = query.filter(Unidad.asociacion_id == asociacion_id)

    # Filtrar por mes si se proporciona
    if mes:
        try:
            mes = int(mes)
            query = query.filter(db.extract('month', Recoleccion.fecha) == mes)
        except ValueError:
            flash('Mes no válido', 'error')
            return redirect(url_for('view_recoleccion'))

    # Obtener las asociaciones de la base de datos
    asociaciones = db.session.query(Usuario).all()

    # Obtener los resultados de la consulta
    recolecciones = query.all()

    return render_template('view_recoleccion.html', 
                           recolecciones=recolecciones, 
                           mes=mes, 
                           asociacion_id=asociacion_id,
                           asociaciones=asociaciones)

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/admin_dashboard/asociaciones', methods=['GET'])
@role_required(1)  # Solo admin
def admin_asociaciones():
    asociaciones = Usuario.query.filter_by(id_tipo=2).all()  # Filtrar usuarios de tipo asociación
    return render_template('admin_asociaciones.html', asociaciones=asociaciones)


@app.route('/delete_recoleccion/<int:recoleccion_id>', methods=['POST'])
@login_required
def delete_recoleccion(recoleccion_id):
    recoleccion = db.session.get(Recoleccion, recoleccion_id)
    
    if not recoleccion:
        flash('Recolección no encontrada.', 'danger')
        return redirect(url_for('view_recoleccion'))

    try:
        # Eliminar manualmente los residuos antes de eliminar la recolección
        RecoleccionResiduo.query.filter_by(id_recoleccion=recoleccion_id).delete()

        # Ahora eliminar la recolección
        db.session.delete(recoleccion)
        db.session.commit()

        flash('Recolección eliminada exitosamente.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar la recolección: {str(e)}', 'danger')

    return redirect(url_for('view_recoleccion'))


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

from flask import request, make_response, send_file
import pandas as pd
from io import BytesIO
from datetime import datetime
from sqlalchemy import extract

@app.route('/download_recoleccion_excel', methods=['GET'])
@login_required
@role_required(1)  # Solo admin

def download_recoleccion_excel():
    # Obtener los filtros desde los argumentos GET
    mes = request.args.get('mes')
    asociacion = request.args.get('asociacion')

    # Construir la consulta base
    query = (
        db.session.query(Recoleccion)
        .join(Unidad)
        .join(Usuario, Unidad.asociacion_id == Usuario.id_usuario)
        .join(RecoleccionResiduo)
        .join(TipoResiduo)
    )

    # Aplicar filtro por mes si se proporciona
    if mes:
        try:
            filtro_mes = datetime.strptime(mes, '%Y-%m')
            query = query.filter(
                extract('year', Recoleccion.fecha) == filtro_mes.year,
                extract('month', Recoleccion.fecha) == filtro_mes.month
            )
        except ValueError:
            flash('Formato de mes inválido. Use YYYY-MM.', 'error')
            return redirect(url_for('view_recoleccion'))

    # Aplicar filtro por asociación si se proporciona
    if asociacion:
        try:
            asociacion_id = int(asociacion)
            query = query.filter(Unidad.asociacion_id == asociacion_id)
        except ValueError:
            flash('ID de asociación no válido.', 'error')
            return redirect(url_for('view_recoleccion'))

    # Ejecutar la consulta
    recolecciones = query.all()

    # Crear el archivo Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Preparar los datos para el DataFrame
        data = []
        for reco in recolecciones:
            for residuo in reco.residuos:
                data.append({
                    'Asociación': reco.unidad.asociacion.nombre,
                    'Unidad': reco.unidad.nombre,
                    'Fecha': reco.fecha.strftime('%Y-%m-%d'),
                    'Residuo': residuo.tipo_residuo.nombre,
                    'Cantidad (kg)': residuo.cantidad
                })

        # Crear DataFrame
        df = pd.DataFrame(data)

        # Exportar a Excel
        df.to_excel(writer, index=False, sheet_name='Recolección')

        # Ajustar formato del Excel
        workbook = writer.book
        worksheet = writer.sheets['Recolección']
        for idx, column in enumerate(df.columns):
            worksheet.set_column(idx, idx, max(len(column), 20))

    output.seek(0)

    # Devolver el archivo Excel como respuesta
    return send_file(
        output,
        as_attachment=True,
        download_name=f"recoleccion_{mes or 'todo'}.xlsx",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )



if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Crea las tablas en la base de datos si no existen
        app.run(host='0.0.0.0', port=8080)
    app.run(debug=False)
