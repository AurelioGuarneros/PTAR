import tkinter as tk
from tkinter import ttk
import RPi.GPIO as GPIO
import time
import threading

# Configuración de GPIO
GPIO.setmode(GPIO.BCM)
pwm_pins = [20, 16]  # Pines GPIO 20 y 16 (pines físicos 38 y 36)
relay_pin = 26  # Pin GPIO para el relé (pines físicos 37)

# Configurar los pines como salida
for pin in pwm_pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)
# Configurar el pin del relé como salida
    GPIO.setup(relay_pin, GPIO.OUT)
    GPIO.output(relay_pin, GPIO.HIGH)

# Variables globales para frecuencia y ciclo de trabajo
freq = 100
duty = 50

# Bandera para controlar el hilo de PWM
running = False

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

        # Actualizar los valores en la caja de texto
        period_ms = period * 1000
        on_time_ms = on_time * 1000
        update_info(period_ms, on_time_ms)

    except ValueError:
        pass  # Maneja errores en caso de entrada no válida
        
# Función para controlar el relé
def toggle_relay():
    if GPIO.input(relay_pin) == GPIO.LOW:
        GPIO.output(relay_pin, GPIO.HIGH)
        relay_button.config(style="On.TButton", text="Relé Apagado")
    else:
        GPIO.output(relay_pin, GPIO.LOW)
        relay_button.config(style="Off.TButton", text="Relé Encendido")

# Función para apagar PWM y limpiar GPIO
def shutdown():
    global running
    running = False
    time.sleep(0.1)  # Esperar un momento para asegurar que el hilo se detenga
    for pin in pwm_pins:
        GPIO.output(pin, GPIO.LOW)
    GPIO.cleanup()
    root.destroy()

# Función para actualizar la información en la caja de texto
def update_info(period_ms, on_time_ms):
    info_text.config(state=tk.NORMAL)
    info_text.delete('1.0', tk.END)
    info_text.insert(tk.END, f"Frecuencia: {freq} Hz\n")
    info_text.insert(tk.END, f"Período: {period_ms:.2f} ms\n")
    info_text.insert(tk.END, f"Ancho de pulso: {on_time_ms:.2f} ms\n")
    info_text.config(state=tk.DISABLED)

# Configuración de la interfaz gráfica
root = tk.Tk()
root.title("Control de PWM con Desfase")

mainframe = ttk.Frame(root, padding="10 10 10 10")
mainframe.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

# Variables de Tkinter
freq_entry = tk.StringVar()
duty_entry = tk.StringVar()

# Elementos de la interfaz
ttk.Label(mainframe, text="Frecuencia (Hz)").grid(column=1, row=1, sticky=tk.W)
ttk.Entry(mainframe, width=7, textvariable=freq_entry).grid(column=2, row=1, sticky=(tk.W, tk.E))

ttk.Label(mainframe, text="Ancho de pulso (%)").grid(column=1, row=2, sticky=tk.W)
ttk.Entry(mainframe, width=7, textvariable=duty_entry).grid(column=2, row=2, sticky=(tk.W, tk.E))

ttk.Button(mainframe, text="Actualizar", command=update_pwm).grid(column=2, row=3, sticky=tk.W)
ttk.Button(mainframe, text="Apagar", command=shutdown).grid(column=2, row=4, sticky=tk.W)

# Estilo de botones
style = ttk.Style()
style.configure("On.TButton", background="green")
style.configure("Off.TButton", background="red")

# Botón para controlar el relé
relay_button = ttk.Button(mainframe, text="Activar/Desactivar Relé", command=toggle_relay)
relay_button.grid(column=2, row=5, sticky=tk.W)
relay_button.configure(style="Off.TButton")  # Estado inicial apagado

# Caja de texto para mostrar información
info_text = tk.Text(mainframe, width=30, height=5, state=tk.DISABLED)
info_text.grid(column=1, row=6, columnspan=2, sticky=(tk.W, tk.E))

# Agregar padding a todos los elementos del frame
for child in mainframe.winfo_children():
    child.grid_configure(padx=5, pady=5)

# Correr la aplicación de Tkinter
root.mainloop()

# Limpiar los pines GPIO al cerrar
for pin in pwm_pins:
    GPIO.output(pin, GPIO.LOW)
GPIO.output(relay_pin, GPIO.LOW)
GPIO.cleanup()
