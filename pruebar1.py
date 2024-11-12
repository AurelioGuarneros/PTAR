import socket
import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from mysql.connector import Error
import threading
import RPi.GPIO as GPIO
import time

# Configuración de los pines GPIO
RELE_ELECTROVALVULA_PIN = 18  
RELE_PLACAS_PIN = 23  
pwm_pins = [20, 16]  
relay_pin = 26  

GPIO.setmode(GPIO.BCM)
GPIO.setup(RELE_ELECTROVALVULA_PIN, GPIO.OUT)
GPIO.setup(RELE_PLACAS_PIN, GPIO.OUT)
for pin in pwm_pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)
GPIO.setup(relay_pin, GPIO.OUT)
GPIO.output(relay_pin, GPIO.HIGH)

# Inicializar electroválvula y placas como desactivadas
GPIO.output(RELE_ELECTROVALVULA_PIN, GPIO.HIGH)
GPIO.output(RELE_PLACAS_PIN, GPIO.HIGH)

# Dirección IP del maestro
MAESTRO_IP = '192.168.0.101'
MAESTRO_PORT = 12345

# Variables globales
nivel_agua = 0
placas_activadas = False
freq = 100
duty = 50
running = False
time_left_1 = 0
time_left_2 = 0
root = None  # Definir root como variable global

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
        # Actualizar base de datos en un hilo separado
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
        

reactor_id = 'R1'

# Función para enviar orden de activación/desactivación de las bombas al maestro
def enviar_orden_bomba(mensaje):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((MAESTRO_IP, MAESTRO_PORT))
            mensaje_completo = f"{reactor_id}:{mensaje}"
            s.sendall(mensaje_completo.encode())
            print(f"Orden enviada: {mensaje_completo}")
    except Exception as e:
        print(f"Error al enviar la orden: {e}")
        
 # Funciones para los botones de las bombas       
def activar_bomba1():
    enviar_orden_bomba('ACTIVAR_BOMBA_1')

def desactivar_bomba1():
    enviar_orden_bomba('DESACTIVAR_BOMBA_1')

def activar_bomba2():
    enviar_orden_bomba('ACTIVAR_BOMBA_2')

def desactivar_bomba2():
    enviar_orden_bomba('DESACTIVAR_BOMBA_2')

# Función para PWM en un hilo separado
def pwm_thread():
    global running, period, on_time, off_time
    period = 1.0 / freq
    while running:
        on_time = (duty / 100.0) * period
        off_time = period - on_time
        delay = off_time / 2

        GPIO.output(pwm_pins[0], GPIO.HIGH)
        time.sleep(on_time)
        GPIO.output(pwm_pins[0], GPIO.LOW)
        time.sleep(delay)

        GPIO.output(pwm_pins[1], GPIO.HIGH)
        time.sleep(on_time)
        GPIO.output(pwm_pins[1], GPIO.LOW)
        time.sleep(delay)
  

# Actualizar PWM
def update_pwm():
    global freq, duty, running
    try:
        freq = float(freq_entry.get())
        duty = float(duty_entry.get())
        if duty > 100:
            duty = 100

        running = False
        time.sleep(0.1)

        running = True
        threading.Thread(target=pwm_thread).start()

    except ValueError:
        pass

# Controlar el relé
def toggle_relay():
    if GPIO.input(relay_pin) == GPIO.LOW:
        GPIO.output(relay_pin, GPIO.HIGH)
        relay_button.config(style="On.TButton", text="Relé Apagado")
    else:
        GPIO.output(relay_pin, GPIO.LOW)
        relay_button.config(style="Off.TButton", text="Relé Encendido")
        
 # Apagar PWM y limpiar GPIO
def shutdown():
    global running
    running = False
    time.sleep(0.1)
    for pin in pwm_pins:
        GPIO.output(pin, GPIO.LOW)
    GPIO.cleanup()
    root.quit()  # Cerrar la aplicación

# Función para activar válvula
def activar_valvula():
    GPIO.output(RELE_ELECTROVALVULA_PIN, GPIO.LOW)
    valvula_label.config(text="Estado Válvula: Abierta")
    print("Válvula activada")
    actualizar_db_en_hilo('valvula', 1)

# Desactivar válvula
def desactivar_valvula():
    GPIO.output(RELE_ELECTROVALVULA_PIN, GPIO.HIGH)
    valvula_label.config(text="Estado Válvula: Cerrada")
    print("Válvula desactivada")
    actualizar_db_en_hilo('valvula', 0)

# Simular llenado de agua
def simular_llenado():
    global nivel_agua
    nivel_agua = 100
    nivel_label.config(text=f"Nivel de Agua: {nivel_agua}%")
    print("Nivel llenado al 100%")
    actualizar_db_en_hilo('nivel', 100)

# Simular vaciado de agua
def simular_vaciado():
    global nivel_agua
    nivel_agua = 0
    nivel_label.config(text=f"Nivel de Agua: {nivel_agua}%")
    print("Nivel vaciado a 0%")
    actualizar_db_en_hilo('nivel', 0)

# Activar/Desactivar placas
def toggle_placas():
    global placas_activadas
    if placas_activadas:
        GPIO.output(RELE_PLACAS_PIN, GPIO.HIGH)
        placas_label.config(text="Placas: Desactivadas")
        print("Placas desactivadas")
        actualizar_db_en_hilo('placas', 0)
    else:
        GPIO.output(RELE_PLACAS_PIN, GPIO.LOW)
        placas_label.config(text="Placas: Activadas")
        print("Placas activadas")
        actualizar_db_en_hilo('placas', 1)
    placas_activadas = not placas_activadas

# Funciones para cronómetros 1
def update_timer():
    global time_left
    if time_left > 0:
        minutes, seconds = divmod(time_left, 60)
        timer_label.config(text=f"{minutes:02}:{seconds:02}")
        time_left -= 1
        root.after(1000, update_timer)
    else:
        messagebox.showinfo("Tiempo Finalizado", "El tiempo ha terminado.")

# Función para iniciar el cronómetro
def start_timer_1():
    global time_left_1
    try:
        minutes = int(min_entry_1.get())
        seconds = int(sec_entry_1.get())
        time_left_1 = minutes * 60 + seconds
        update_timer_1()
    except ValueError:
        messagebox.showerror("Entrada no válida", "Introduce minutos y segundos válidos.")

# Función para reiniciar el cronómetro
def reset_timer_1():
    global time_left_1
    time_left_1 = 0
    cronometro_1_label.config(text="00:00")

# Función para iniciar el cronómetro
def update_timer_2():
    global time_left_2
    if time_left_2 > 0:
        minutes, seconds = divmod(time_left_2, 60)
        cronometro_2_label.config(text=f"{minutes:02}:{seconds:02}")
        time_left_2 -= 1
        root.after(1000, update_timer_2)
    else:
        messagebox.showinfo("Cronómetro 2", "El tiempo ha terminado.")

# Función para iniciar el cronómetro
def start_timer_2():
    global time_left_2
    try:
        minutes = int(min_entry_2.get())
        seconds = int(sec_entry_2.get())
        time_left_2 = minutes * 60 + seconds
        update_timer_2()
    except ValueError:
        messagebox.showerror("Entrada no válida", "Introduce minutos y segundos válidos.")

# Función para reiniciar el cronómetro
def reset_timer_2():
    global time_left_2
    time_left_2 = 0
    cronometro_2_label.config(text="00:00")

# Cerrar programa
def shutdown():
    global running
    running = False
    time.sleep(0.1)
    for pin in pwm_pins:
        GPIO.output(pin, GPIO.LOW)
    GPIO.cleanup()
    root.quit()

# Interfaz gráfica
def interfaz_reactor():
    global root, freq_entry, duty_entry, valvula_label, nivel_label, placas_label, cronometro_1_label, cronometro_2_label
    root = tk.Tk()
    root.title("Control con Base de Datos")
    root.attributes("-fullscreen", True)  # Pantalla completa

    # Control de Bombas (Izquierda)
    bombas_frame = ttk.Frame(root)
    bombas_frame.grid(row=0, column=0, sticky="ns", padx=20, pady=20)
    ttk.Label(bombas_frame, text="Control de Bombas", font=("Arial", 14)).pack(pady=10)
    ttk.Button(bombas_frame, text="Activar Bomba 1", command=activar_bomba1).pack(fill="x", pady=5)
    ttk.Button(bombas_frame, text="Desactivar Bomba 1", command=desactivar_bomba1).pack(fill="x", pady=5)
    ttk.Button(bombas_frame, text="Activar Bomba 2", command=activar_bomba2).pack(fill="x", pady=5)
    ttk.Button(bombas_frame, text="Desactivar Bomba 2", command=desactivar_bomba2).pack(fill="x", pady=5)

    # Control de Válvulas y Placas (Centro)
    valvulas_frame = ttk.Frame(root)
    valvulas_frame.grid(row=0, column=1, sticky="ns", padx=20, pady=20)
    ttk.Label(valvulas_frame, text="Control de Válvulas", font=("Arial", 14)).pack(pady=10)
    valvula_label = ttk.Label(valvulas_frame, text="Estado Válvula: Cerrada", font=("Arial", 12))
    valvula_label.pack(pady=5)
    ttk.Button(valvulas_frame, text="Abrir Válvula", command=activar_valvula).pack(fill="x", pady=5)
    ttk.Button(valvulas_frame, text="Cerrar Válvula", command=desactivar_valvula).pack(fill="x", pady=5)
    placas_label = ttk.Label(valvulas_frame, text="Placas: Desactivadas", font=("Arial", 12))
    placas_label.pack(pady=5)
    ttk.Button(valvulas_frame, text="Activar Placas", command=toggle_placas).pack(fill="x", pady=5)

    # Simulación de Niveles (Centro)
    simulacion_frame = ttk.Frame(root)
    simulacion_frame.grid(row=0, column=2, sticky="ns", padx=20, pady=20)
    ttk.Label(simulacion_frame, text="Simulación de Niveles", font=("Arial", 14)).pack(pady=10)
    nivel_label = ttk.Label(simulacion_frame, text="Nivel de Agua: 0%", font=("Arial", 12))
    nivel_label.pack(pady=5)
    ttk.Button(simulacion_frame, text="Llenar", command=simular_llenado).pack(fill="x", pady=5)
    ttk.Button(simulacion_frame, text="Vaciar", command=simular_vaciado).pack(fill="x", pady=5)

    # Control de PWM (Derecha)
    pwm_frame = ttk.Frame(root)
    pwm_frame.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=20, pady=20)
    ttk.Label(pwm_frame, text="Control de PWM", font=("Arial", 14)).grid(row=0, column=0, columnspan=2, pady=10)
    ttk.Label(pwm_frame, text="Frecuencia:").grid(row=1, column=0, sticky="w")
    freq_entry = ttk.Entry(pwm_frame)
    freq_entry.grid(row=1, column=1)
    freq_entry.insert(0, "100")  # valor por defecto
    ttk.Label(pwm_frame, text="Ancho de Pulso:").grid(row=2, column=0, sticky="w")
    duty_entry = ttk.Entry(pwm_frame)
    duty_entry.grid(row=2, column=1)
    duty_entry.insert(0, "50")  # valor por defecto
    ttk.Button(pwm_frame, text="Iniciar PWM", command=update_pwm).grid(row=3, column=0, columnspan=2, pady=5)
    ttk.Button(pwm_frame, text="Relé Apagado", command=update_pwm).grid(row=3, column=1, columnspan=2, pady=5)

    # Cronómetros (Derecha)
    cronometro_frame = ttk.Frame(root)
    cronometro_frame.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=20, pady=20)
    ttk.Label(cronometro_frame, text="Buffer", font=("Arial", 14)).grid(row=0, column=0, pady=10)
    cronometro_1_label = ttk.Label(cronometro_frame, text="00:00", font=("Arial", 12))
    cronometro_1_label.grid(row=1, column=0, pady=5)
    min_entry_1 = ttk.Entry(cronometro_frame)
    min_entry_1.grid(row=2, column=0, sticky="w")
    sec_entry_1 = ttk.Entry(cronometro_frame)
    sec_entry_1.grid(row=2, column=0, sticky="e")
    ttk.Button(cronometro_frame, text="Iniciar", command=start_timer_1).grid(row=4, column=0, pady=5)
    ttk.Button(cronometro_frame, text="Reiniciar", command=reset_timer_1).grid(row=5, column=0, pady=5)

    # Cronómetro 2
    ttk.Label(cronometro_frame, text="Reactor", font=("Arial", 14)).grid(row=0, column=1, pady=10)
    cronometro_2_label = ttk.Label(cronometro_frame, text="00:00", font=("Arial", 12))
    cronometro_2_label.grid(row=1, column=1, pady=5)
    min_entry_2 = ttk.Entry(cronometro_frame)
    min_entry_2.grid(row=2, column=1, sticky="w")
    sec_entry_2 = ttk.Entry(cronometro_frame)
    sec_entry_2.grid(row=2, column=1, sticky="e")
    ttk.Button(cronometro_frame, text="Iniciar", command=start_timer_2).grid(row=4, column=1, pady=5)
    ttk.Button(cronometro_frame, text="Reiniciar", command=reset_timer_2).grid(row=5, column=1, pady=5)

    # Botón de salida
    ttk.Button(root, text="Salir", command=shutdown).grid(row=4, column=0, columnspan=3, pady=20)

    root.protocol("WM_DELETE_WINDOW", shutdown)
    root.mainloop()

if __name__ == '__main__':
    interfaz_reactor()
