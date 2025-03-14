import time
import math
import board
import busio
from adafruit_ads1x15.ads1115 import ADS1115

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS1115(i2c)
GAIN = 2  # Equivalente a GAIN_TWO en Arduino
FACTOR = 50  # 30A/1V
MULTIPLIER = 0.0625  # mV por bit

def get_corriente():
    sumatoria = 0
    contador = 0
    tiempo_inicial = time.time()
    
    while time.time() - tiempo_inicial < 1:  # Muestreo durante 1 segundo
        volt_diferencial = ads.read_adc_difference(0, gain=GAIN) * MULTIPLIER / 1000  # Convertir a V
        corriente = volt_diferencial * FACTOR
        sumatoria += corriente ** 2
        contador += 1
    
    corriente_rms = math.sqrt(sumatoria / contador)
    return corriente_rms

def imprimir_medidas(prefijo, valor, sufijo):
    print(f"{prefijo}{valor:.3f} {sufijo}")

import tkinter as tk
from tkinter import ttk

def actualizar_gui():
    global root, etiqueta_corriente, etiqueta_potencia
    corriente_rms = get_corriente()
    potencia = 110.0 * corriente_rms
    etiqueta_corriente.config(text=f"Irms: {corriente_rms:.3f} A")
    etiqueta_potencia.config(text=f"Potencia: {potencia:.3f} W")
    root.after(1000, actualizar_gui)

def sensor_corriente():
# Configurar la interfaz gráfica
    root = tk.Tk()
    root.title("Medición de Corriente SCT-013")

    frame = ttk.Frame(root, padding=20)
    frame.grid(row=0, column=0)

    etiqueta_corriente = ttk.Label(frame, text="Irms: 0.000 A", font=("Arial", 14))
    etiqueta_corriente.grid(row=0, column=0)

    etiqueta_potencia = ttk.Label(frame, text="Potencia: 0.000 W", font=("Arial", 14))
    etiqueta_potencia.grid(row=1, column=0)

    boton_salir = ttk.Button(frame, text="Salir", command=root.quit)
    boton_salir.grid(row=2, column=0, pady=10)

    # Iniciar actualización
    root.after(1000, actualizar_gui)
    root.mainloop()

if __name__ == "__main__":
    while True:
        corriente_rms = get_corriente()
        potencia = 110.0 * corriente_rms  # Asumiendo 110V de tensión
        
        imprimir_medidas("Irms: ", corriente_rms, "A ,")
        imprimir_medidas("Potencia: ", potencia, "W")
        
        time.sleep(1)  # Esperar antes de la siguiente medición

