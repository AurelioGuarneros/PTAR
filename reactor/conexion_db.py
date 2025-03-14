import mysql.connector
from mysql.connector import Error
import threading

# Función para conectar a la base de datos
def conectar_db():
    try:
        conn = mysql.connector.connect(
            host='192.168.1.78',  # IP del servidor MariaDB
            user='Aurelio',
            password='RG980320',
            database='planta'
        )
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

# Función para actualizar la base de datos en un hilo separado
def actualizar_db_en_hilo(columna, valor):
    def actualizar():
        conn = conectar_db()
        if conn:
            try:
                cursor = conn.cursor()
                #query = f"UPDATE estadosr SET {columna}=%s WHERE id=1"
                query = f"INSERT INTO estadosr ({columna}) VALUES (%s)"
                cursor.execute(query, (valor,))
                conn.commit()
                cursor.close()
            except Error as e:
                print(f"Error al actualizar la base de datos: {e}")
            finally:
                conn.close()

    hilo = threading.Thread(target=actualizar)
    hilo.start()
    
