from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_cors import CORS
import sqlite3
from datetime import datetime
import os 

app = Flask(__name__, template_folder='.')
app.secret_key = 'ColorHada_Secret_Key'
CORS(app)

# --- CONFIGURACIÓN DE LOGIN ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

def conectar():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(base_dir, 'libreria.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# -- INICIALIZACION DE BASE DE DATOS --
def inicializar_db():
    conn = conectar()
    conn.execute('''
                 CREATE TABLE IF NOT EXISTS servicios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo TEXT NOT NULL,
                    monto REAL NOT NULL,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
    conn.execute('''
                 CREATE TABLE IF NOT EXISTS ventas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    producto_nombre TEXT NOT NULL,
                    cantidad INTEGER NOT NULL,
                    monto_total REAL NOT NULL,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
    # Tabla usuarios por si no existe
    conn.execute('''
                 CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )
            ''')
            
    try:
        conn.execute('ALTER TABLE productos ADD COLUMN stock_minimo INTEGER DEFAULT 5')
    except:
        pass
    conn.commit()
    conn.close()

inicializar_db()

# --- RUTAS DE ACCESO ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']
        conn = conectar()
        user_db = conn.execute("SELECT * FROM usuarios WHERE username = ? AND password = ?", (usuario, password)).fetchone()
        conn.close()
        if user_db:
            login_user(User(user_db['id']))
            return redirect(url_for('index'))
        flash('Usuario o contraseña incorrectos')
    return render_template('login.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']
        conn = conectar()
        try:
            conn.execute("INSERT INTO usuarios (username, password) VALUES (?, ?)", (usuario, password))
            conn.commit()
            return redirect(url_for('login'))
        except:
            flash('Error: El usuario ya existe')
        finally:
            conn.close()
    return render_template('registro.html')

@app.route('/logout')
def logout():
    session.pop('alertas_mostradas', None)
    logout_user()
    return redirect(url_for('login'))

# --- RUTAS DEL SISTEMA ---

@app.route('/')
@login_required
def index():
    conn = conectar()
    productos = conn.execute('SELECT * FROM productos ORDER BY categoria').fetchall()
    secciones = {}
    
    if 'alertas_mostradas' not in session:
        for p in productos:
            if p['stock'] <= p['stock_minimo']:
                flash(f"⚠️ ¡Stock Bajo! Quedan solo {p['stock']} de: {p['nombre']}", "warning")
        session['alertas_mostradas'] = True
    
    for p in productos:
        cat = p['categoria']
        if cat not in secciones: secciones[cat] = []
        secciones[cat].append(p)
        
    conn.close()
    return render_template('index.html', secciones=secciones)

@app.route('/agregar', methods=['POST'])
@login_required
def agregar():
    nombre = request.form['nombre']
    categoria = request.form['categoria']
    stock = int(request.form['stock'])
    precio = float(request.form['precio'])
    try:
        stock_minimo_raw = request.form.get('stock_minimo')
        stock_minimo = int(stock_minimo_raw) if stock_minimo_raw else 0
    except ValueError:
        stock_minimo = 0
    conn = conectar()
    conn.execute('INSERT INTO productos (nombre, categoria, stock, precio, stock_minimo) VALUES (?, ?, ?, ?, ?)',
                 (nombre, categoria, stock, precio, stock_minimo))
    conn.commit()
    conn.close()
    flash(f"✨ {nombre} agregado correctamente", "success")
    return redirect(url_for('index'))

@app.route('/vender', methods=['POST'])
@login_required
def vender():
    id_prod = int(request.form['id'])
    cant = int(request.form['cantidad'])
    conn = conectar()
    p = conn.execute('SELECT * FROM productos WHERE id = ?', (id_prod,)).fetchone()
    if p:
        if p['stock'] >= cant:
            total_venta = p['precio'] * cant
            conn.execute('UPDATE productos SET stock = stock - ? WHERE id = ?', (cant, id_prod))
            conn.execute('INSERT INTO ventas (producto_nombre, cantidad, monto_total) VALUES (?, ?, ?)',
                         (p['nombre'], cant, total_venta))
            conn.commit()
            flash(f"✅ Venta exitosa: {p['nombre']} (x{cant})", "success")
        else:
            flash(f"❌ Error: No hay stock suficiente de {p['nombre']}.", "danger")
    conn.close()
    return redirect(url_for('index'))

@app.route('/registrar_servicio', methods=['POST'])
@login_required
def registrar_servicio():
    tipo = request.form.get('tipo_servicio')
    try:
        monto = float(request.form.get('monto'))
        conn = conectar()
        conn.execute('INSERT INTO servicios (tipo, monto) VALUES (?, ?)', (tipo, monto))
        conn.commit()
        conn.close()
        flash(f"✅ Servicio '{tipo}' registrado por ${monto:.2f}", "success")
    except:
        flash("❌ Error al registrar el servicio. Verifique los datos ingresados.", "danger")
    return redirect(url_for('index'))

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    conn = conectar()
    if request.method == 'POST':
        nombre = request.form['nombre']
        precio = float(request.form['precio'])
        stock = int(request.form['stock'])
        stock_minimo = int(request.form['stock_minimo'])
        conn.execute('UPDATE productos SET nombre = ?, precio = ?, stock = ?, stock_minimo = ? WHERE id = ?',
                     (nombre, precio, stock, stock_minimo, id))
        conn.commit()
        conn.close()
        flash(f"✅ {nombre} actualizado correctamente", "success")
        return redirect(url_for('index'))
    producto = conn.execute('SELECT * FROM productos WHERE id = ?', (id,)).fetchone()
    conn.close()
    return render_template('editar.html', p=producto)

@app.route('/buscar_precio', methods=['GET', 'POST'])
@login_required
def buscar_precio():
    resultados = []
    busqueda = ""
    if request.method == 'POST':
        busqueda = request.form.get('busqueda', '')
        conn = conectar()
        query = "SELECT * FROM productos WHERE nombre LIKE ? ORDER BY categoria"
        resultados = conn.execute(query, ('%' + busqueda + '%',)).fetchall()
        conn.close()
    return render_template('buscar_precio.html', resultados=resultados, busqueda=busqueda)

@app.route('/historial')
@login_required
def historial():
    conn = conectar()
    hoy = datetime.now().strftime('%Y-%m-%d')
    ventas = conn.execute('SELECT * FROM ventas WHERE date(fecha) = ?', (hoy,)).fetchall()
    servicios = conn.execute('SELECT * FROM servicios WHERE date(fecha) = ?', (hoy,)).fetchall()
    total_v = sum(v['monto_total'] for v in ventas)
    total_s = sum(s['monto'] for s in servicios)
    conn.close()
    return render_template('historial.html', ventas=ventas, servicios=servicios, 
                           total_v=total_v, total_s=total_s, total_dia=total_v+total_s, fecha=hoy)

@app.route('/borrar/<int:id>')
@login_required
def borrar(id):
    conn = conectar()
    conn.execute('DELETE FROM productos WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# --- NUEVA SECCIÓN: API PARA REACT NATIVE (JSON) ---
# Estas rutas sirven para que el celu pida datos sin cargar el HTML

@app.route('/api/productos', methods=['GET'])
def api_productos():
    conn = conectar()
    productos = conn.execute('SELECT * FROM productos').fetchall()
    conn.close()
    return jsonify([dict(p) for p in productos])

@app.route('/api/historial', methods=['GET'])
def api_historial():
    conn = conectar()
    hoy = datetime.now().strftime('%Y-%m-%d')
    ventas = conn.execute('SELECT * FROM ventas WHERE date(fecha) = ?', (hoy,)).fetchall()
    conn.close()
    return jsonify([dict(v) for v in ventas])

# --- CONFIGURACIÓN PARA NUBE ---
if __name__ == '__main__':
    # Usamos el puerto que nos dé el servidor o el 5000 por defecto
    puerto = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=puerto, debug=True)