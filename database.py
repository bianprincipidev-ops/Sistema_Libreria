import sqlite3

def crear_base_datos():
    # Establece la conexión con el archivo (se creará si no existe)
    conexion = sqlite3.connect('libreria.db')
    cursor = conexion.cursor()

    # 1. Crear tabla de productos (el inventario)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            stock INTEGER NOT NULL,
            stock_minimo INTEGER NOT NULL,
            precio REAL NOT NULL
        )
    ''')

    # 2. Crear tabla de ventas (el historial para el balance)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER,
            cantidad INTEGER,
            total REAL,
            fecha TEXT,
            FOREIGN KEY (producto_id) REFERENCES productos (id)
        )
    ''')

    conexion.commit()
    conexion.close()
    print("✅ Base de datos configurada correctamente.")

if __name__ == "__main__":
    crear_base_datos()
