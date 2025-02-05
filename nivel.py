import tkinter as tk
from tkinter import ttk
import mysql.connector
from mysql.connector import Error
import RPi.GPIO as GPIO
import time

# Configuración de GPIO
RELAY_PIN = 17  # Cambia esto al pin que estés utilizando para el relevador
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT)
GPIO.output(RELAY_PIN, GPIO.HIGH)  # Inicialmente apagado

# Conexión a la base de datos
def conectar_db():
    try:
        conn = mysql.connector.connect(
            host='192.168.0.101',  # Cambia a la IP del servidor MariaDB
            user='Aurelio',
            password='RG980320',
            database='planta'
        )
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

# Función para activar o desactivar la bomba y el relevador basado en las condiciones de la tabla estadosr
def verificar_condiciones_y_controlar_bomba():
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()

            # Leer estado de la tabla estadosr
            cursor.execute("SELECT valvula, nivel FROM estadosr WHERE id=1")  # Cambia el id según tu lógica
            result = cursor.fetchone()

            if result:
                valvula, nivel = result

                # Condiciones para activar la bomba
                if valvula == 1 and nivel == 0:
                    # Activar el relevador
                    GPIO.output(RELAY_PIN, GPIO.LOW)  # Activar la bomba
                    cursor.execute("INSERT INTO estados (bomba, procedencia) VALUES (%s, %s)", (1, 'r1'))
                    conn.commit()
                    label_status.config(text="Bomba activada y registrada en estados por: r1")
                # Condiciones para desactivar la bomba
                elif valvula == 0 and nivel == 100:
                    # Desactivar el relevador
                    GPIO.output(RELAY_PIN, GPIO.HIGH)  # Desactivar la bomba
                    cursor.execute("INSERT INTO estados (bomba, procedencia) VALUES (%s, %s)", (0, 'r1'))
                    conn.commit()
                    label_status.config(text="Bomba desactivada y registrada en estados por: r1")
                else:
                    label_status.config(text="Condiciones no cumplidas para activar o desactivar la bomba")
            else:
                label_status.config(text="No se encontraron datos en estadosr")

            cursor.close()
        except Error as e:
            print(f"Error al controlar la bomba: {e}")
        finally:
            conn.close()

    # Verificar nuevamente después de 5 segundos
    root.after(5000, verificar_condiciones_y_controlar_bomba)  # Vuelve a comprobar cada 5 segundos

# Función para salir de la aplicación
def salir():
    GPIO.output(RELAY_PIN, GPIO.HIGH)  # Asegúrate de desactivar el relevador
    GPIO.cleanup()  # Limpiar la configuración de GPIO
    root.quit()

# Configuración de la ventana principal de tkinter
root = tk.Tk()
root.title("Control de Bomba - Maestro")

# Barra de progreso
progress = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
progress.pack(pady=20)

# Etiqueta de estado
label_status = tk.Label(root, text="Esperando...")
label_status.pack(pady=10)

# Iniciar el chequeo de condiciones
verificar_condiciones_y_controlar_bomba()

# Botón para salir
btn_salir = tk.Button(root, text="Salir", command=salir)
btn_salir.pack(pady=10)

root.mainloop()

