import RPi.GPIO as GPIO
import time
import threading
import tkinter as tk
from tkinter import ttk

# Configuración de pines GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

pin1 = 20  # GPIO 20 - Parte alta del IR2213
pin2 = 16  # GPIO 16 - Parte baja del IR2213
relay_pin = 26

GPIO.setup(pin1, GPIO.OUT)
GPIO.setup(pin2, GPIO.OUT)
GPIO.setup(relay_pin, GPIO.OUT)

# Variables del PWM
frecuencia = 100  # Hz
duty_cycle = 0  # %
dead_time = 0.0005  # Tiempo muerto en segundos
running = False  # Bandera para controlar el hilo
relay_timer_running = False
running = True

def pwm_loop():
    """Bucle que genera las señales PWM en un hilo separado."""
    global running
    while running:
        periodo = 1.0 / frecuencia
        tiempo_encendido = (duty_cycle / 100) * periodo
        tiempo_apagado = periodo - tiempo_encendido - (2 * dead_time)

        if tiempo_apagado < 0:  # Evitar valores negativos
            tiempo_apagado = 0

        # *Encender pin1 y apagar pin2*
        GPIO.output(pin1, GPIO.HIGH)
        GPIO.output(pin2, GPIO.LOW)
        time.sleep(tiempo_encendido / 2)

        # *Tiempo muerto: Ambos pines en LOW*
        GPIO.output(pin1, GPIO.LOW)
        GPIO.output(pin2, GPIO.LOW)
        time.sleep(dead_time)

        # *Encender pin2 y apagar pin1*
        GPIO.output(pin1, GPIO.LOW)
        GPIO.output(pin2, GPIO.HIGH)
        time.sleep(tiempo_encendido / 2)

        # *Tiempo muerto nuevamente*
        GPIO.output(pin1, GPIO.LOW)
        GPIO.output(pin2, GPIO.LOW)
        time.sleep(dead_time)

        # *Tiempo de apagado para respetar el período fijo*
        time.sleep(tiempo_apagado)

def actualizar_pwm():
    """Actualiza las variables y reinicia el proceso de PWM en un hilo separado."""
    global root, freq_entry, time_entry, duty_cycle, dead_time, running, duty_entry, dead_time_entry, relay_button, placas_label, actualizar_db_en_hilo

    try:
        frecuencia = float(freq_entry.get())
        duty_cycle = float(duty_entry.get())
        dead_time = float(dead_time_entry.get())
    except ValueError:
        return

    if duty_cycle < 0 or duty_cycle > 100:
        return  # Evitar valores inválidos

    if running:
        detener_pwm()

    running = True
    thread = threading.Thread(target=pwm_loop)
    thread.daemon = True  # Se cierra automáticamente con la app
    thread.start()

def detener_pwm():
    """Detiene el bucle de PWM y apaga los pines."""
    global running
    running = False
    time.sleep(0.1)  # Pequeña pausa para asegurar que el hilo termine
    GPIO.output(pin1, GPIO.LOW)
    GPIO.output(pin2, GPIO.LOW)

def toggle_relay_with_timer():
    global relay_timer_running
    if relay_timer_running:
        return  # Evita múltiples hilos

    try:
        time_minutes = float(time_entry.get())
        time_seconds = time_minutes * 60

        GPIO.output(relay_pin, GPIO.LOW)
        relay_button.config(text="Relé Encendido", state=tk.DISABLED)
        relay_timer_running = True
        placas_label.config(text="Placas: Activadas")
        actualizar_db_en_hilo('placas', 1)

        threading.Thread(target=relay_timer, args=(time_seconds,), daemon=True).start()
    except ValueError:
        print("Error: Tiempo inválido")

def relay_timer(time_seconds):
    global relay_timer_running
    while time_seconds > 0:
        relay_button.config(text=f"Relé Encendido ({int(time_seconds)}s)")
        time.sleep(1)
        time_seconds -= 1
    GPIO.output(relay_pin, GPIO.HIGH)
    relay_button.config(text="Relé Apagado", state=tk.NORMAL)
    relay_timer_running = False
    placas_label.config(text="Placas: Desactivadas")
    actualizar_db_en_hilo('placas', 0)

def cerrar_programa():
    """Cierra el programa correctamente liberando los pines."""
    detener_pwm()
    GPIO.cleanup()
    root.destroy()

def programa_PWM():
    root = tk.Tk()
    root.title("Control de Puente H")

    mainframe = ttk.Frame(root, padding="10")
    mainframe.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    # Botón para activar el relé con temporizador

    freq_label = ttk.Label(mainframe, text="Frecuencia (Hz):")
    freq_label.grid(column=1, row=1, sticky=tk.W)
    freq_entry = ttk.Entry(mainframe, width=10)
    freq_entry.grid(column=2, row=1, sticky=(tk.W, tk.E))
    freq_entry.insert(0, "100")

    duty_label = ttk.Label(mainframe, text="Ciclo de trabajo (%):")
    duty_label.grid(column=1, row=2, sticky=tk.W)
    duty_entry = ttk.Entry(mainframe, width=10)
    duty_entry.grid(column=2, row=2, sticky=(tk.W, tk.E))
    duty_entry.insert(0, "0")

    time_label = ttk.Label(mainframe, text="Tiempo (min)")
    time_label.grid(column=1, row=3, sticky=tk.W)
    time_entry = ttk.Entry(mainframe, width=10)
    time_entry.grid(column=2, row=3, sticky=(tk.W, tk.E))
    time_entry.insert(0, "0")

    dead_time_label = ttk.Label(mainframe, text="Tiempo Muerto (s):")
    dead_time_label.grid(column=1, row=4, sticky=tk.W)
    dead_time_entry = ttk.Entry(mainframe, width=10)
    dead_time_entry.grid(column=2, row=4, sticky=(tk.W, tk.E))
    dead_time_entry.insert(0, "0.0005")

    actualizar_button = ttk.Button(mainframe, text="Iniciar PWM", command=actualizar_pwm)
    actualizar_button.grid(column=1, row=5, sticky=tk.W)

    detener_button = ttk.Button(mainframe, text="Detener PWM", command=detener_pwm)
    detener_button.grid(column=2, row=6, sticky=tk.W)

    relay_button = ttk.Button(mainframe, text="Relé Apagado", command=toggle_relay_with_timer)
    relay_button.grid(row=5, column=0, columnspan=2, pady=10)

    cerrar_button = ttk.Button(mainframe, text="Cerrar Programa", command=cerrar_programa)
    cerrar_button.grid(column=1, row=7, columnspan=2, sticky=tk.W+tk.E)

    root.mainloop()
