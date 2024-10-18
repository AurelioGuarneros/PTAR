import tkinter as tk
from tkinter import ttk
import mysql.connector
from mysql.connector import Error
import threading
import RPi.GPIO as GPIO

# Configuración de los pines GPIO
RELE_ELECTROVALVULA_PIN = 18  # Pin GPIO para la electroválvula
RELE_PLACAS_PIN = 23  # Pin GPIO para las placas

GPIO.setmode(GPIO.BCM)
GPIO.setup(RELE_ELECTROVALVULA_PIN, GPIO.OUT)
GPIO.setup(RELE_PLACAS_PIN, GPIO.OUT)

# Inicializar la electroválvula y las placas como desactivadas
GPIO.output(RELE_ELECTROVALVULA_PIN, GPIO.HIGH)
GPIO.output(RELE_PLACAS_PIN, GPIO.HIGH)

# Variables de nivel de agua
nivel_agua = 0  # 0% como nivel inicial
placas_activadas = False  # Estado inicial de las placas

# Conexión a la base de datos
def conectar_db():
    try:
        conn = mysql.connector.connect(
            host='192.168.0.101',  # IP del servidor MariaDB
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
                query = f"UPDATE estadosr SET {columna}=%s WHERE id=1"
                cursor.execute(query, (valor,))
                conn.commit()
                cursor.close()
            except Error as e:
                print(f"Error al actualizar la base de datos: {e}")
            finally:
                conn.close()

    hilo = threading.Thread(target=actualizar)
    hilo.start()

# Función para activar la válvula
def activar_valvula():
    GPIO.output(RELE_ELECTROVALVULA_PIN, GPIO.LOW)  # Activar válvula
    valvula_label.config(text="Estado Válvula: Abierta")
    print("Válvula activada")
    actualizar_db_en_hilo('valvula', 1)  # Actualizar columna "valvula" en la base de datos

# Función para desactivar la válvula
def desactivar_valvula():
    GPIO.output(RELE_ELECTROVALVULA_PIN, GPIO.HIGH)  # Desactivar válvula
    valvula_label.config(text="Estado Válvula: Cerrada")
    print("Válvula desactivada")
    actualizar_db_en_hilo('valvula', 0)  # Actualizar columna "valvula" en la base de datos

# Función para simular el llenado del nivel de agua
def simular_llenado():
    global nivel_agua
    nivel_agua = 100  # Llenar al 100%
    nivel_label.config(text=f"Nivel de Agua: {nivel_agua}%")
    print("Nivel llenado al 100%")
    actualizar_db_en_hilo('nivel', 100)  # Actualizar columna "nivel" en la base de datos

# Función para simular el vaciado del nivel de agua
def simular_vaciado():
    global nivel_agua
    nivel_agua = 0  # Vaciar al 0%
    nivel_label.config(text=f"Nivel de Agua: {nivel_agua}%")
    print("Nivel vaciado a 0%")
    actualizar_db_en_hilo('nivel', 0)  # Actualizar columna "nivel" en la base de datos

# Función para activar/desactivar placas
def toggle_placas():
    global placas_activadas
    if placas_activadas:
        GPIO.output(RELE_PLACAS_PIN, GPIO.HIGH)  # Desactivar placas
        placas_label.config(text="Placas: Desactivadas")
        print("Placas desactivadas")
        actualizar_db_en_hilo('placas', 0)  # Actualizar columna "placas" en la base de datos
    else:
        GPIO.output(RELE_PLACAS_PIN, GPIO.LOW)  # Activar placas
        placas_label.config(text="Placas: Activadas")
        print("Placas activadas")
        actualizar_db_en_hilo('placas', 1)  # Actualizar columna "placas" en la base de datos
    placas_activadas = not placas_activadas

# Interfaz gráfica (Tkinter)
def interfaz_reactor():
    root = tk.Tk()
    root.title("Reactor - Control con Base de Datos")

    # Widgets
    global valvula_label, nivel_label, placas_label

    valvula_label = ttk.Label(root, text="Estado Válvula: Cerrada")
    valvula_label.grid(row=0, column=0, padx=10, pady=10)

    nivel_label = ttk.Label(root, text="Nivel de Agua: 0%")
    nivel_label.grid(row=1, column=0, padx=10, pady=10)

    placas_label = ttk.Label(root, text="Placas: Desactivadas")
    placas_label.grid(row=2, column=0, padx=10, pady=10)

    # Botones para controlar la válvula
    activar_valvula_button = ttk.Button(root, text="Activar Válvula", command=activar_valvula)
    activar_valvula_button.grid(row=3, column=0, padx=10, pady=5)

    desactivar_valvula_button = ttk.Button(root, text="Desactivar Válvula", command=desactivar_valvula)
    desactivar_valvula_button.grid(row=4, column=0, padx=10, pady=5)

    # Botones para simular el llenado y vaciado
    llenar_button = ttk.Button(root, text="Llenar", command=simular_llenado)
    llenar_button.grid(row=5, column=0, padx=10, pady=5)

    vaciar_button = ttk.Button(root, text="Vaciar", command=simular_vaciado)
    vaciar_button.grid(row=6, column=0, padx=10, pady=5)

    # Botón para activar/desactivar placas
    placas_button = ttk.Button(root, text="Activar/Desactivar Placas", command=toggle_placas)
    placas_button.grid(row=7, column=0, padx=10, pady=5)

    # Botón de salida
    salir_button = ttk.Button(root, text="Salir", command=lambda: (GPIO.cleanup(), root.quit()))
    salir_button.grid(row=8, column=0, padx=10, pady=5)

    # Iniciar la interfaz
    root.mainloop()

# Ejecutar la interfaz del reactor
interfaz_reactor()

# Limpiar GPIO al salir
GPIO.cleanup()
