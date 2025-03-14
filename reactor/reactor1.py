import socket
import tkinter as tk
from tkinter import ttk
import mysql.connector
from mysql.connector import Error
import threading
import RPi.GPIO as GPIO
import time

# Configuración de GPIO
GPIO.setmode(GPIO.BCM)

# Pines de relevadores y PWM
RELE_ELECTROVALVULA_PIN = 18
RELE_PLACAS_PIN = 23
pwm_pins = [20, 16]
relay_pin = 26

# Configurar pines como salida
GPIO.setup(RELE_ELECTROVALVULA_PIN, GPIO.OUT)
GPIO.setup(RELE_PLACAS_PIN, GPIO.OUT)
for pin in pwm_pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)
GPIO.setup(relay_pin, GPIO.OUT)
GPIO.output(relay_pin, GPIO.HIGH)

# Configuración inicial
GPIO.output(RELE_ELECTROVALVULA_PIN, GPIO.HIGH)
GPIO.output(RELE_PLACAS_PIN, GPIO.HIGH)

# Configuración de sockets
MAESTRO_IP = '192.168.0.101'
MAESTRO_PORT = 12345
reactor_id = 'R1'

# Conexión a la base de datos
def conectar_db():
    try:
        conn = mysql.connector.connect(
            host='192.168.0.101',
            user='Aurelio',
            password='RG980320',
            database='planta'
        )
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

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

# Función para enviar órdenes al maestro
def enviar_orden_bomba(mensaje):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((MAESTRO_IP, MAESTRO_PORT))
            mensaje_completo = f"{reactor_id}:{mensaje}"
            s.sendall(mensaje_completo.encode())
            print(f"Orden enviada: {mensaje_completo}")
    except Exception as e:
        print(f"Error al enviar la orden: {e}")

# Funciones de control de relevadores y nivel
def activar_valvula():
    GPIO.output(RELE_ELECTROVALVULA_PIN, GPIO.LOW)
    valvula_label.config(text="Estado Válvula: Abierta")
    actualizar_db_en_hilo('valvula', 1)

def desactivar_valvula():
    GPIO.output(RELE_ELECTROVALVULA_PIN, GPIO.HIGH)
    valvula_label.config(text="Estado Válvula: Cerrada")
    actualizar_db_en_hilo('valvula', 0)

def simular_llenado():
    nivel_agua.set(100)
    nivel_label.config(text=f"Nivel de Agua: {nivel_agua.get()}%")
    actualizar_db_en_hilo('nivel', 100)

def simular_vaciado():
    nivel_agua.set(0)
    nivel_label.config(text=f"Nivel de Agua: {nivel_agua.get()}%")
    actualizar_db_en_hilo('nivel', 0)

def toggle_placas():
    if placas_activadas.get():
        GPIO.output(RELE_PLACAS_PIN, GPIO.HIGH)
        placas_label.config(text="Placas: Desactivadas")
        actualizar_db_en_hilo('placas', 0)
    else:
        GPIO.output(RELE_PLACAS_PIN, GPIO.LOW)
        placas_label.config(text="Placas: Activadas")
        actualizar_db_en_hilo('placas', 1)
    placas_activadas.set(not placas_activadas.get())

# PWM en un hilo
freq = 100
duty = 50
running = False

def pwm_thread():
    global running
    period = 1.0 / freq
    on_time = (duty / 100.0) * period
    while running:
        GPIO.output(pwm_pins[0], GPIO.HIGH)
        time.sleep(on_time)
        GPIO.output(pwm_pins[0], GPIO.LOW)
        time.sleep(period - on_time)
        GPIO.output(pwm_pins[1], GPIO.HIGH)
        time.sleep(on_time)
        GPIO.output(pwm_pins[1], GPIO.LOW)
        time.sleep(period - on_time)

def update_pwm():
    global running, freq, duty
    freq = float(freq_entry.get())
    duty = float(duty_entry.get())
    running = False
    time.sleep(0.1)
    running = True
    threading.Thread(target=pwm_thread).start()

def toggle_relay():
    if GPIO.input(relay_pin) == GPIO.LOW:
        GPIO.output(relay_pin, GPIO.HIGH)
        relay_button.config(style="On.TButton", text="Relé Apagado")
    else:
        GPIO.output(relay_pin, GPIO.LOW)
        relay_button.config(style="Off.TButton", text="Relé Encendido")

# Interfaz Tkinter
def interfaz_reactor():
    root = tk.Tk()
    root.title("Reactor - Control Completo")

    global valvula_label, nivel_label, placas_label, freq_entry, duty_entry, relay_button
    valvula_label = ttk.Label(root, text="Estado Válvula: Cerrada")
    valvula_label.grid(row=0, column=0, padx=10, pady=10)
    nivel_label = ttk.Label(root, text="Nivel de Agua: 0%")
    nivel_label.grid(row=1, column=0, padx=10, pady=10)
    placas_label = ttk.Label(root, text="Placas: Desactivadas")
    placas_label.grid(row=2, column=0, padx=10, pady=10)

    activar_valvula_button = ttk.Button(root, text="Activar Válvula", command=activar_valvula)
    activar_valvula_button.grid(row=3, column=0, padx=10, pady=5)
    desactivar_valvula_button = ttk.Button(root, text="Desactivar Válvula", command=desactivar_valvula)
    desactivar_valvula_button.grid(row=4, column=0, padx=10, pady=5)
    llenar_button = ttk.Button(root, text="Llenar", command=simular_llenado)
    llenar_button.grid(row=5, column=0, padx=10, pady=5)
    vaciar_button = ttk.Button(root, text="Vaciar", command=simular_vaciado)
    vaciar_button.grid(row=6, column=0, padx=10, pady=5)
    placas_button = ttk.Button(root, text="Activar/Desactivar Placas", command=toggle_placas)
    placas_button.grid(row=7, column=0, padx=10, pady=5)

    ttk.Label(root, text="Frecuencia (Hz):").grid(row=8, column=0, padx=10, pady=5)
    freq_entry = ttk.Entry(root)
    freq_entry.insert(0, "100")
    freq_entry.grid(row=8, column=1, padx=10, pady=5)
    ttk.Label(root, text="Ciclo de Trabajo (%):").grid(row=9, column=0, padx=10, pady=5)
    duty_entry = ttk.Entry(root)
    duty_entry.insert(0, "50")
    duty_entry.grid(row=9, column=1, padx=10, pady=5)
    update_pwm_button = ttk.Button(root, text="Actualizar PWM", command=update_pwm)
    update_pwm_button.grid(row=10, column=0, padx=10, pady=5)

    relay_button = ttk.Button(root, text="Relé Encendido", command=toggle_relay)
    relay_button.grid(row=11, column=0, padx=10, pady=5)
    
    salir_button = ttk.Button(root, text="Salir", command=lambda: (GPIO.cleanup(), root.quit()))
    salir_button.grid(row=12, column=0, padx=10, pady=5)

    root.mainloop()

nivel_agua = tk.IntVar(value=0)
placas_activadas = tk.BooleanVar(value=False)

interfaz_reactor()
