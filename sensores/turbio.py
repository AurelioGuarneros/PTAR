import time
import tkinter as tk
from tkinter import Label
import board
import busio
from adafruit_ads1x15.ads1115 import ADS1115

i2c = busio.I2C(board.SCL, board.SDA)
adc = ADS1115(i2c)
GAIN = 1  # Ganancia del ADS1115 (1 = ±4.096V)

# Función para leer el sensor y actualizar la interfaz
def leer_sensor():
    global label_sensor, label_porcentaje, label_voltage1, label_voltage, root
    sensor_value = adc.read(0, gain=GAIN) # Leer canal 0 del ADS1115
    voltage1 = sensor_value * (4.096 / 32767)  # Convertir a voltaje
    valor = sensor_value / 10  # Conversión similar a la del código de Arduino
    voltaje = voltage1 - 4.00  # Ajuste de voltaje

    # Actualizar etiquetas en la interfaz
    label_sensor.config(text=f"Sensor Value: {sensor_value}")
    label_porcentaje.config(text=f"Valor: {valor}%")
    label_voltage1.config(text=f"Voltage1: {voltage1:.3f} V")
    label_voltage.config(text=f"Voltage: {voltaje:.3f} V")

    # Repetir la lectura cada 500 ms
    root.after(500, leer_sensor)

def sensor_corriente():
# Configurar la ventana de Tkinter
    root = tk.Tk()
    root.title("Lectura de Sensor")

    # Crear etiquetas para mostrar los valores
    label_sensor = Label(root, text="Sensor Value: --", font=("Arial", 14))
    label_sensor.pack()

    label_porcentaje = Label(root, text="Valor: --%", font=("Arial", 14))
    label_porcentaje.pack()

    label_voltage1 = Label(root, text="Voltage1: -- V", font=("Arial", 14))
    label_voltage1.pack()

    label_voltage = Label(root, text="Voltage: -- V", font=("Arial", 14))
    label_voltage.pack()

    # Iniciar la lectura del sensor
    leer_sensor()

    # Ejecutar la interfaz gráfica
    root.mainloop()
