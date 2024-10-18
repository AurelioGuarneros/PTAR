import socket
import threading
import RPi.GPIO as GPIO
import mysql.connector
from mysql.connector import Error
import tkinter as tk
from tkinter import messagebox

# Configuración de GPIO
BOMBA1_PIN = 17  # Cambia al pin que estés utilizando para la bomba 1
BOMBA2_PIN = 27  # Cambia al pin que estés utilizando para la bomba 2

GPIO.setmode(GPIO.BCM)
GPIO.setup(BOMBA1_PIN, GPIO.OUT)
GPIO.setup(BOMBA2_PIN, GPIO.OUT)
GPIO.output(BOMBA1_PIN, GPIO.HIGH)  # Bomba 1 inicialmente apagada
GPIO.output(BOMBA2_PIN, GPIO.HIGH)  # Bomba 2 inicialmente apagada

# Variable global para el socket del servidor
servidor_socket = None

# Función para conectar a la base de datos
def conectar_db():
    try:
        conn = mysql.connector.connect(
            host='localhost',  # Cambia a la IP del servidor MariaDB
            user='Aurelio',
            password='RG980320',
            database='planta'
        )
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

# Función para guardar el estado de las bombas en la base de datos
def registrar_bomba_en_db(bomba, procedencia):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO estados (bomba, procedencia) VALUES (%s, %s)", (bomba, procedencia))
            conn.commit()
            cursor.close()
        except Error as e:
            print(f"Error al guardar en la base de datos: {e}")
        finally:
            conn.close()

# Función para manejar las órdenes de las bombas
def manejar_orden_bomba(orden):
    if orden == 'ACTIVAR_BOMBA_1':
        GPIO.output(BOMBA1_PIN, GPIO.LOW)
        print("Bomba 1 activada")
        registrar_bomba_en_db(1, 'Maestro')  # Registrar activación de bomba 1 en DB
    elif orden == 'DESACTIVAR_BOMBA_1':
        GPIO.output(BOMBA1_PIN, GPIO.HIGH)
        print("Bomba 1 desactivada")
        registrar_bomba_en_db(1, 'Maestro')  # Registrar desactivación de bomba 1 en DB
    elif orden == 'ACTIVAR_BOMBA_2':
        GPIO.output(BOMBA2_PIN, GPIO.LOW)
        print("Bomba 2 activada")
        registrar_bomba_en_db(2, 'Maestro')  # Registrar activación de bomba 2 en DB
    elif orden == 'DESACTIVAR_BOMBA_2':
        GPIO.output(BOMBA2_PIN, GPIO.HIGH)
        print("Bomba 2 desactivada")
        registrar_bomba_en_db(2, 'Maestro')  # Registrar desactivación de bomba 2 en DB

# Función para escuchar órdenes desde el esclavo
def escuchar_ordenes():
    global servidor_socket
    servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor_socket.bind(('192.168.0.102', 12345))  # IP del maestro
    servidor_socket.listen(5)
    print("Esperando conexiones en 192.168.0.102:12345")

    while True:
        conn, addr = servidor_socket.accept()
        print(f"Conexión recibida de {addr}")
        orden = conn.recv(1024).decode()
        if orden:
            manejar_orden_bomba(orden)
        conn.close()

# Función para cerrar el socket y limpiar GPIO
def salir():
    global servidor_socket
    if servidor_socket:
        servidor_socket.close()  # Cerrar el socket
        print("Socket cerrado")
    GPIO.cleanup()  # Limpiar la configuración de GPIO
    print("GPIO limpio")
    exit(0)  # Terminar el programa

# Interfaz gráfica con Tkinter
def iniciar_interfaz():
    ventana = tk.Tk()
    ventana.title("Control de Bombas")
    
    # Botón para salir
    boton_salir = tk.Button(ventana, text="Salir", command=confirmar_salida, bg="red", fg="white", padx=20, pady=10)
    boton_salir.pack(pady=20)
    
    ventana.protocol("WM_DELETE_WINDOW", confirmar_salida)
    ventana.mainloop()

# Función para confirmar la salida
def confirmar_salida():
    if messagebox.askokcancel("Salir", "¿Seguro que deseas salir?"):
        salir()

# Iniciar hilo para escuchar órdenes
hilo_escucha = threading.Thread(target=escuchar_ordenes)
hilo_escucha.start()

# Iniciar la interfaz gráfica
iniciar_interfaz()

