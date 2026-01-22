from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'ColorHada_Secret_Key'

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
    conn = sqlite3.connect('libreria.db')
    conn.row_factory = sqlite3.Row
    return conn

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
    logout_user()
    return redirect(url_for('login'))

# --- RUTAS DEL SISTEMA ---

@app.route('/')
@login_required
def index():
    conn = conectar()
    productos = conn.execute('SELECT * FROM productos ORDER BY categoria').fetchall()
    secciones = {}
    
    for p in productos:
        if p['stock'] <= p['stock_minimo']:
            flash(f"⚠️ ¡Stock Bajo! Quedan solo {p['stock']} unidades de: {p['nombre']}", "warning")
            
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
    conn = conectar()
    conn.execute('INSERT INTO productos (nombre, categoria, stock, precio, stock_minimo) VALUES (?, ?, ?, ?, ?)',
                 (nombre, categoria, stock, precio, 5))
    conn.commit()
    conn.close()
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
            conn.execute('UPDATE productos SET stock = stock - ? WHERE id = ?', (cant, id_prod))
            conn.commit()
            flash(f"✅ Venta exitosa: {p['nombre']} (x{cant})", "success")
        else:
            flash(f"❌ Error: No hay stock suficiente de {p['nombre']}. Solo quedan {p['stock']}.", "danger")
    
    conn.close()
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

@app.route('/borrar/<int:id>')
@login_required
def borrar(id):
    conn = conectar()
    conn.execute('DELETE FROM productos WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

# NO AGREGAR MAS RUTAS ABAJO DE ESTA LÍNEA POR EL app.run(debug=True)