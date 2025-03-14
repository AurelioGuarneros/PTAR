import tkinter as tk
from tkinter import ttk
import threading
import p2
import color
import turbio

def programa_PWM(frame):
    p2.root = frame  # Redirigir la interfaz de alu.py al frame
    p2.freq_label = ttk.Label(frame, text="Frecuencia (Hz):")
    p2.freq_label.grid(column=1, row=1, sticky=tk.W)
    p2.freq_entry = ttk.Entry(frame, width=10)
    p2.freq_entry.grid(column=2, row=1, sticky=(tk.W, tk.E))
    p2.freq_entry.insert(0, "100")

    p2.duty_label = ttk.Label(frame, text="Ciclo de trabajo (%):")
    p2.duty_label.grid(column=1, row=2, sticky=tk.W)
    p2.duty_entry = ttk.Entry(frame, width=10)
    p2.duty_entry.grid(column=2, row=2, sticky=(tk.W, tk.E))
    p2.duty_entry.insert(0, "0")

    p2.time_label = ttk.Label(frame, text="Tiempo (min)")
    p2.time_label.grid(column=1, row=3, sticky=tk.W)
    p2.time_entry = ttk.Entry(frame, width=10)
    p2.time_entry.grid(column=2, row=3, sticky=(tk.W, tk.E))
    p2.time_entry.insert(0, "0")

    p2.dead_time_label = ttk.Label(frame, text="Tiempo Muerto (s):")
    p2.dead_time_label.grid(column=1, row=4, sticky=tk.W)
    p2.dead_time_entry = ttk.Entry(frame, width=10)
    p2.dead_time_entry.grid(column=2, row=4, sticky=(tk.W, tk.E))
    p2.dead_time_entry.insert(0, "0.0005")

def iniciar_color(frame):
    color.root = frame  # Redirigir la interfaz de color.py al frame
    color.label_color = tk.Label(frame, text="R: 0  V: 0  A: 0", font=("Arial", 14))
    color.label_color.pack()
    
    color.result_label = tk.Label(frame, text="No identificado", font=("Arial", 16, "bold"))
    color.result_label.pack()
    
    frame.after(900, color.update_display)  # Iniciar actualización dentro del frame

def iniciar_turbio(frame):
    turbio.root = frame
    turbio.label_sensor = tk.Label(frame, text="Sensor Value: --", font=("Arial", 14))
    turbio.label_sensor.pack()

    turbio.label_porcentaje = tk.Label(frame, text="Valor: --%", font=("Arial", 14))
    turbio.label_porcentaje.pack()

    turbio.label_voltage1 = tk.Label(frame, text="Voltage1: -- V", font=("Arial", 14))
    turbio.label_voltage1.pack()

    turbio.label_voltage = tk.Label(frame, text="Voltage: -- V", font=("Arial", 14))
    turbio.label_voltage.pack()

# Configurar la ventana principal
root = tk.Tk()
root.title("Aplicación con Pestañas")

notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both")

frame_p2 = ttk.Frame(notebook)
frame_color = ttk.Frame(notebook)
frame_turbio = ttk.Frame(notebook)
notebook.add(frame_p2, text="programa_PWM")
notebook.add(frame_color, text="Sensor de Color")
notebook.add(frame_turbio, text="Sensor de turbio")

# Iniciar las interfaces en sus respectivas pestañas
programa_PWM(frame_p2)
iniciar_color(frame_color)
iniciar_turbio(frame_turbio)

root.mainloop()
