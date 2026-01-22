from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'LauraColorHada'

# Configuración de Login
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

# --- RUTAS DE ACCESO Y REGISTRO ---

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
        else:
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
            flash('¡Cuenta creada! Ahora puedes ingresar.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Ese nombre de usuario ya existe.')
        finally:
            conn.close()
    return render_template('registro.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- RUTAS DEL SISTEMA (PROTEGIDAS) ---

@app.route('/')
@login_required
def index():
    conn = conectar()
    productos = conn.execute('SELECT * FROM productos ORDER BY categoria').fetchall()
    secciones = {}
    for p in productos:
        cat = p['categoria']
        if cat not in secciones: secciones[cat] = []
        secciones[cat].append(p)
    alertas = [p for p in productos if p['stock'] <= p['stock_minimo']]
    conn.close()
    return render_template('index.html', secciones=secciones, alertas=alertas)

@app.route('/buscar_precio')
@login_required
def buscar_precio():
    query = request.args.get('q', '')
    conn = conectar()
    resultados = conn.execute("SELECT * FROM productos WHERE nombre LIKE ?", ('%' + query + '%',)).fetchall()
    conn.close()
    return render_template('precios.html', resultados=resultados, busqueda=query)

@app.route('/vender', methods=['POST'])
@login_required
def vender():
    id_prod = int(request.form['id'])
    cant = int(request.form['cantidad'])
    conn = conectar()
    p = conn.execute('SELECT * FROM productos WHERE id = ?', (id_prod,)).fetchone()
    if p and p['stock'] >= cant:
        nuevo_stock = p['stock'] - cant
        conn.execute('UPDATE productos SET stock = ? WHERE id = ?', (nuevo_stock, id_prod))
        conn.execute('INSERT INTO ventas (producto_id, cantidad, total, fecha) VALUES (?, ?, ?, ?)',
                     (id_prod, cant, p['precio']*cant, datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/agregar', methods=['POST'])
@login_required
def agregar():
    nombre = request.form['nombre']
    categoria = request.form['categoria'].strip() or "General"
    stock = int(request.form['stock'])
    precio = float(request.form['precio'])
    conn = conectar()
    conn.execute('INSERT INTO productos (nombre, categoria, stock, stock_minimo, precio) VALUES (?, ?, ?, 5, ?)',
                 (nombre, categoria, stock, precio))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)