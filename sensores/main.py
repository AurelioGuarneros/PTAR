import tkinter as tk
from tkinter import ttk
import threading
import alu
import color
import turbio

def iniciar_alu(frame):
    alu.root = frame  # Redirigir la interfaz de alu.py al frame
    alu.etiqueta_corriente = ttk.Label(frame, text="Irms: 0.000 A", font=("Arial", 14))
    alu.etiqueta_corriente.grid(row=0, column=0)
    
    alu.etiqueta_potencia = ttk.Label(frame, text="Potencia: 0.000 W", font=("Arial", 14))
    alu.etiqueta_potencia.grid(row=1, column=0)
    
    boton_salir = ttk.Button(frame, text="Salir", command=root.quit)
    boton_salir.grid(row=2, column=0, pady=10)
    
    frame.after(1000, alu.actualizar_gui)  # Iniciar actualización dentro del frame

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

frame_alu = ttk.Frame(notebook)
frame_color = ttk.Frame(notebook)
frame_turbio = ttk.Frame(notebook)
notebook.add(frame_alu, text="Medición de Corriente")
notebook.add(frame_color, text="Sensor de Color")
notebook.add(frame_turbio, text="Sensor de turbio")

# Iniciar las interfaces en sus respectivas pestañas
iniciar_alu(frame_alu)
iniciar_color(frame_color)
iniciar_turbio(frame_turbio)

root.mainloop()
