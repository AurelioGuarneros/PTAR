import tkinter as tk
from tkinter import ttk
import RPi.GPIO as GPIO
import time
import threading
import mysql.connector
from mysql.connector import Error
import socket

# Configuración de GPIO
GPIO.setmode(GPIO.BCM)

# Pines para el programa 1 (PWM y relé)
pwm_pins = [20, 16]  # Pines GPIO 20 y 16
relay_pin_pwm = 26  # Pin GPIO para el relé de las fases

# Pines para el programa 2 (relevadores y electroválvula)
RELE_ELECTROVALVULA_PIN = 18  # Pin GPIO para la electroválvula
RELE_PLACAS_PIN = 23  # Pin GPIO para las placas

# Pines para las bombas
BOMBA1_PIN = 24  # Pin GPIO para Bomba 1
BOMBA2_PIN = 25  # Pin GPIO para Bomba 2

# Inicializar pines
GPIO.setup(pwm_pins[0], GPIO.OUT)
GPIO.setup(pwm_pins[1], GPIO.OUT)
GPIO.setup(relay_pin_pwm, GPIO.OUT)
GPIO.setup(RELE_ELECTROVALVULA_PIN, GPIO.OUT)
GPIO.setup(RELE_PLACAS_PIN, GPIO.OUT)
GPIO.setup(BOMBA1_PIN, GPIO.OUT)
GPIO.setup(BOMBA2_PIN, GPIO.OUT)

# Inicializar todos los pines a estado bajo
GPIO.output(pwm_pins[0], GPIO.LOW)
GPIO.output(pwm_pins[1], GPIO.LOW)
GPIO.output(relay_pin_pwm, GPIO.HIGH)
GPIO.output(RELE_ELECTROVALVULA_PIN, GPIO.HIGH)
GPIO.output(RELE_PLACAS_PIN, GPIO.HIGH)
GPIO.output(BOMBA1_PIN, GPIO.HIGH)
GPIO.output(BOMBA2_PIN, GPIO.HIGH)

# Variables globales de PWM
freq = 100
duty = 50
running = False

# Variables para base de datos
nivel_agua = 0
placas_activadas = False

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

# Función para actualizar la base de datos
def actualizar_db(columna, valor):
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

# Función de PWM en un hilo separado
def pwm_thread():
    global running, period, on_time, off_time
    period = 1.0 / freq
    while running:
        on_time = (duty / 100.0) * period
        off_time = period - on_time
        delay = off_time / 2

        # Pin 38 (pwm_pins[0])
        GPIO.output(pwm_pins[0], GPIO.HIGH)
        time.sleep(on_time)
        GPIO.output(pwm_pins[0], GPIO.LOW)
        time.sleep(delay)

        # Pin 36 (pwm_pins[1]), desfaseado
        GPIO.output(pwm_pins[1], GPIO.HIGH)
        time.sleep(on_time)
        GPIO.output(pwm_pins[1], GPIO.LOW)
        time.sleep(delay)

# Función para actualizar PWM
def update_pwm():
    global freq, duty, running
    try:
        freq = float(freq_entry.get())
        duty = float(duty_entry.get())
        # Asegurar que el ciclo de trabajo esté entre 0 y 100%
        if duty > 100:
            duty = 100

        # Detener el hilo anterior si está corriendo
        running = False
        time.sleep(0.1)  # Esperar un momento para asegurar que el hilo se detenga

        # Iniciar un nuevo hilo de PWM
        running = True
        threading.Thread(target=pwm_thread).start()

    except ValueError:
        pass  # Maneja errores en caso de entrada no válida

# Función para controlar el relé del PWM
def toggle_relay_pwm():
    if GPIO.input(relay_pin_pwm) == GPIO.LOW:
        GPIO.output(relay_pin_pwm, GPIO.HIGH)
        relay_button_pwm.config(style="On.TButton", text="Relé Apagado")
    else:
        GPIO.output(relay_pin_pwm, GPIO.LOW)
        relay_button_pwm.config(style="Off.TButton", text="Relé Encendido")

# Funciones para activar/desactivar la válvula
def activar_valvula():
    GPIO.output(RELE_ELECTROVALVULA_PIN, GPIO.LOW)  # Activar válvula
    valvula_label.config(text="Estado Válvula: Abierta")
    actualizar_db('valvula', 1)

def desactivar_valvula():
    GPIO.output(RELE_ELECTROVALVULA_PIN, GPIO.HIGH)  # Desactivar válvula
    valvula_label.config(text="Estado Válvula: Cerrada")
    actualizar_db('valvula', 0)

# Función para simular el llenado del nivel de agua
def simular_llenado():
    global nivel_agua
    nivel_agua = 100  # Llenar al 100%
    nivel_label.config(text=f"Nivel de Agua: {nivel_agua}%")
    actualizar_db('nivel', 100)

# Función para simular el vaciado del nivel de agua
def simular_vaciado():
    global nivel_agua
    nivel_agua = 0  # Vaciar al 0%
    nivel_label.config(text=f"Nivel de Agua: {nivel_agua}%")
    actualizar_db('nivel', 0)

# Función para activar/desactivar las placas
def toggle_placas():
    global placas_activadas
    if placas_activadas:
        GPIO.output(RELE_PLACAS_PIN, GPIO.HIGH)  # Desactivar placas
        placas_label.config(text="Placas: Desactivadas")
        actualizar_db('placas', 0)
    else:
        GPIO.output(RELE_PLACAS_PIN, GPIO.LOW)  # Activar placas
        placas_label.config(text="Placas: Activadas")
        actualizar_db('placas', 1)
    placas_activadas = not placas_activadas

# Funciones para control de bombas
def enviar_instruccion_bomba(bomba, accion):
    try:
        # Conectar con el maestro
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('192.168.0.102', 12345))  # IP y puerto del maestro
            mensaje = f"{bomba}:{accion}"
            s.sendall(mensaje.encode())
            s.close()
    except Exception as e:
        print(f"Error al conectar con el maestro: {e}")

# Función para encender bomba 1
def encender_bomba1():
    enviar_instruccion_bomba('bomba1', 'on')

# Función para apagar bomba 1
def apagar_bomba1():
    enviar_instruccion_bomba('bomba1', 'off')

# Función para encender bomba 2
def encender_bomba2():
    enviar_instruccion_bomba('bomba2', 'on')

# Función para apagar bomba 2
def apagar_bomba2():
    enviar_instruccion_bomba('bomba2', 'off')

# Función para salir del programa limpiando GPIO
def salir():
    global running
    running = False
    GPIO.cleanup()
    root.quit()

# Interfaz gráfica
root = tk.Tk()
root.title("Control PWM, Reactor y Bombas")

# Frame para el control PWM
pwm_frame = ttk.Frame(root, padding="10 10 10 10")
pwm_frame.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

ttk.Label(pwm_frame, text="Frecuencia (Hz)").grid(column=1, row=1, sticky=tk.W)
freq_entry = tk.StringVar()
ttk.Entry(pwm_frame, width=7, textvariable=freq_entry).grid(column=2, row=1, sticky=(tk.W, tk.E))

ttk.Label(pwm_frame, text="Ancho de pulso (%)").grid(column=1, row=2, sticky=tk.W)
duty_entry = tk.StringVar()
ttk.Entry(pwm_frame, width=7, textvariable=duty_entry).grid(column=2, row=2, sticky=(tk.W, tk.E))

ttk.Button(pwm_frame, text="Actualizar PWM", command=update_pwm).grid(column=2, row=3, sticky=tk.W)
relay_button_pwm = ttk.Button(pwm_frame, text="Relé Apagado", command=toggle_relay_pwm)
relay_button_pwm.grid(column=2, row=4, sticky=tk.W)

# Frame para el control del reactor
reactor_frame = ttk.Frame(root, padding="10 10 10 10")
reactor_frame.grid(column=1, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

valvula_label = ttk.Label(reactor_frame, text="Estado Válvula: Cerrada")
valvula_label.grid(column=1, row=1, sticky=tk.W)
ttk.Button(reactor_frame, text="Abrir Válvula", command=activar_valvula).grid(column=1, row=2, sticky=tk.W)
ttk.Button(reactor_frame, text="Cerrar Válvula", command=desactivar_valvula).grid(column=1, row=3, sticky=tk.W)

nivel_label = ttk.Label(reactor_frame, text="Nivel de Agua: 0%")
nivel_label.grid(column=1, row=4, sticky=tk.W)
ttk.Button(reactor_frame, text="Llenar Tanque", command=simular_llenado).grid(column=1, row=5, sticky=tk.W)
ttk.Button(reactor_frame, text="Vaciar Tanque", command=simular_vaciado).grid(column=1, row=6, sticky=tk.W)

placas_label = ttk.Label(reactor_frame, text="Placas: Desactivadas")
placas_label.grid(column=1, row=7, sticky=tk.W)
ttk.Button(reactor_frame, text="Activar/Desactivar Placas", command=toggle_placas).grid(column=1, row=8, sticky=tk.W)

# Frame para el control de las bombas
bomba_frame = ttk.Frame(root, padding="10 10 10 10")
bomba_frame.grid(column=2, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

ttk.Button(bomba_frame, text="Encender Bomba 1", command=encender_bomba1).grid(column=1, row=1, sticky=tk.W)
ttk.Button(bomba_frame, text="Apagar Bomba 1", command=apagar_bomba1).grid(column=1, row=2, sticky=tk.W)

ttk.Button(bomba_frame, text="Encender Bomba 2", command=encender_bomba2).grid(column=1, row=3, sticky=tk.W)
ttk.Button(bomba_frame, text="Apagar Bomba 2", command=apagar_bomba2).grid(column=1, row=4, sticky=tk.W)

# Botón de salida
ttk.Button(root, text="Salir", command=salir).grid(column=2, row=5, sticky=tk.W)

root.mainloop()

# Limpiar los pines GPIO al cerrar el programa
GPIO.cleanup()

