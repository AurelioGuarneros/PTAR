import tkinter as tk
from tkinter import ttk
import RPi.GPIO as GPIO
import threading
import time
import socket
from adafruit_ads1x15.analog_in import AnalogIn
import adafruit_ads1x15.ads1115 as ADS
import board
import busio
from conexion_db import actualizar_db_en_hilo
global bandera 



# Configuración de GPIO (Evitar repetir)
GPIO.setmode(GPIO.BCM)
RELE_ELECTROVALVULA_PIN = 18
SENSOR_PIN = 12  

# Configuración de pines de salida
for pin in [ RELE_ELECTROVALVULA_PIN]:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW if pin  else GPIO.HIGH)

# Configuración del sensor
GPIO.setup(SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Configuración de I2C y ADS1115
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
ads.gain = 1  # Rango de ±4.096V
canal = AnalogIn(ads, ADS.P0)

# Variables globales
running = False
nivel_agua = 0
placas_activadas = False
reactor_id = 'R1'
MAESTRO_IP = '192.168.1.78'
MAESTRO_PORT = 12345
relay_timer_running = False
sensor_estado = "Nivel Bajo (Vacío)"  # Estado inicial
running = True
lock = threading.Lock() 
barra = None
bandera = 0

    
# Función para calcular la presión a partir del voltaje
def calcular_presion(voltaje):
    V_offset = 0.04  # Voltaje a 0 kPa
    sensibilidad = 0.045  # Sensibilidad en V/kPa
    return (voltaje - V_offset) / sensibilidad

# Función para actualizar la barra de nivel
def actualizar_barra():
    global barra, bandera,root

    voltaje = canal.voltage
    presion = calcular_presion(voltaje)
    print('el valor de la presion calculada es:', presion)

    # Rango de presión ajustado
    presion = max(3.5, min(presion, 13))

    # Actualizar barra de nivel
    if barra is None:
        barra = canvas.create_rectangle(50, 200, 150, 200, fill="blue")

    altura = int(((presion - 3.5) / (9.26 - 3.5)) * 200)
    canvas.coords(barra, 50, 200 - altura, 150, 200)
    etiqueta_presion.config(text=f"Presión: {presion:.2f} kPa")

    # Apagar bomba si se alcanza presión máxima
    if presion >= 13 and bandera == 0:
        desactivar_bomba1()
        desactivar_valvula()
        bomba1_button.config(bg="red", text="Bomba 1: Apagada")
        bandera = 1
        print("Bomba desactivada por presión máxima")

    root.after(1000, actualizar_barra)  # Actualización cada segundo

# Funciones para el reactor
def enviar_orden_bomba(mensaje):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((MAESTRO_IP, MAESTRO_PORT))
            mensaje_completo = f"{reactor_id}:{mensaje}"
            s.sendall(mensaje_completo.encode())
    except Exception as e:
        print(f"Error al enviar la orden: {e}")


def activar_bomba1(): enviar_orden_bomba('ACTIVAR_BOMBA_1')
def desactivar_bomba1(): enviar_orden_bomba('DESACTIVAR_BOMBA_1')
def activar_bomba2(): enviar_orden_bomba('ACTIVAR_BOMBA_2')
def desactivar_bomba2(): enviar_orden_bomba('DESACTIVAR_BOMBA_2')
def activar_bombaRB1(): enviar_orden_bomba('ACTIVAR_BOMBA_RB1')
def desactivar_bombaRB1(): enviar_orden_bomba('DESACTIVAR_BOMBA_RB1')
def activar_bombaBC1(): enviar_orden_bomba('ACTIVAR_BOMBA_BC1')
def desactivar_bombaBC1(): enviar_orden_bomba('DESACTIVAR_BOMBA_BC1')
def activar_buffer1(): enviar_orden_bomba('ACTIVAR_Buffer_1')
def desactivar_buffer1(): enviar_orden_bomba('DESACTIVAR_Buffer_1')



# Función que maneja el cambio de estado del botón
def toggle_bomba_button(button, activar_func, desactivar_func, on_color, off_color, on_text, off_text):
    if button.cget("bg") == on_color:  # Si está activada
        desactivar_func()  # Desactiva la bomba
        button.config(bg=off_color, text=off_text)  # Cambia el texto y color del botón
    else:
        activar_func()  # Activa la bomba
        button.config(bg=on_color, text=on_text)


def activar_valvula():
    global bandera 
    GPIO.output(RELE_ELECTROVALVULA_PIN, GPIO.LOW)
    valvula_label.config(text="Estado Válvula: Abierta")
    actualizar_db_en_hilo('valvula', 1)
    bandera = 0
    print('bandera',bandera)
    
def desactivar_valvula():
    GPIO.output(RELE_ELECTROVALVULA_PIN, GPIO.HIGH)
    valvula_label.config(text="Estado Válvula: Cerrada")
    actualizar_db_en_hilo('valvula', 0)
    

# Función de interrupción
def detectar_cambio(channel):
    global sensor_estado
    nuevo_estado = "Nivel Alto (Llenado)" if GPIO.input(SENSOR_PIN) == GPIO.HIGH else "Nivel Bajo (Vacío)"
    nivel = 100 if nuevo_estado == "Nivel Alto (Llenado)" else 0

    with lock:
        if nuevo_estado != sensor_estado:
            sensor_estado = nuevo_estado
            # Actualizar base de datos en un hilo separado
            threading.Thread(target=actualizar_db_en_hilo, args=('nivel', nivel), daemon=True).start()

# Enviar comandos al maestro según el nivel
        if nivel == 100:  # Nivel alto
                desactivar_bomba1()
                bomba1_button.config(bg="red", text="Bomba 1: Apagada")  # Cambia el color y el texto del botón
        #elif nivel == 0:  # Nivel bajo
                #activar_bomba1()

    
def salir():
    global running
    running = False
    time.sleep(0.1)
    GPIO.cleanup()
    root.destroy()

def programa_PWM():
    root = tk.Tk()
    root.title("REACTOR 1")

# Función para actualizar la interfaz gráfica
def actualizar_interfaz():
    estado_label.config(text=f"Estado del sensor: {sensor_estado}")
    root.after(1000, actualizar_interfaz)



# Estilo de botones
style = ttk.Style()
style.configure("On.TButton", background="green")
style.configure("Off.TButton", background="red")
style.configure("TButton", font=("Helvetica", 16))  # Cambiar fuente y tamaño para botones
style.configure("TLabel", font=("Helvetica", 16))  # Cambiar fuente y tamaño para etiquetas


# Widgets para el Reactor
valvula_label = ttk.Label(mainframe, text="Estado Válvula: Cerrada")
valvula_label.grid(row=0, column=0, columnspan=2, padx=5, pady=5)
estado_label = ttk.Label(mainframe, text=f"Estado del sensor: {sensor_estado}")
estado_label.grid(row=1, column=0, columnspan=2, padx=5, pady=5)
placas_label = ttk.Label(mainframe, text="Placas: Desactivadas")
placas_label.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

ttk.Button(mainframe, text="Activar Válvula", command=activar_valvula).grid(row=3, column=0, pady=5)
ttk.Button(mainframe, text="Desactivar Válvula", command=desactivar_valvula).grid(row=3, column=1, pady=5)

#Botones de Bombas
bomba1_button = tk.Button(mainframe, text="Bomba 1: Apagada", bg="red", command=lambda: toggle_bomba_button(bomba1_button, activar_bomba1, desactivar_bomba1, "green", "red", "Bomba 1: Encendida", "Bomba 1: Apagada"))
bomba1_button.grid(row=6, column=0, pady=5)

bomba2_button = tk.Button(mainframe, text="Bomba 2: Apagada", bg="red", command=lambda: toggle_bomba_button(bomba2_button, activar_bomba2, desactivar_bomba2, "green", "red", "Bomba 2: Encendida", "Bomba 2: Apagada"))
bomba2_button.grid(row=7, column=0, pady=5)

bombaRB1_button = tk.Button(mainframe, text="Bomba RB1: Apagada", bg="red", command=lambda: toggle_bomba_button(bombaRB1_button, activar_bombaRB1, desactivar_bombaRB1, "green", "red", "Bomba RB1: Encendida", "Bomba RB1: Apagada"))
bombaRB1_button.grid(row=8, column=0, pady=5)

bombaBC1_button = tk.Button(mainframe, text="Bomba BC1: Apagada", bg="red", command=lambda: toggle_bomba_button(bombaBC1_button, activar_bombaBC1, desactivar_bombaBC1, "green", "red", "Bomba BC1: Encendida", "Bomba BC1: Apagada"))
bombaBC1_button.grid(row=9, column=0, pady=5)

bombaBF1_button = tk.Button(mainframe, text="Buffer 1: Apagada", bg="red", command=lambda: toggle_bomba_button(bombaBF1_button, activar_buffer1, desactivar_buffer1, "green", "red", "Buffer 1: Encendida", "Buffer 1: Apagada"))
bombaBF1_button.grid(row=10, column=0, pady=5)

# Etiqueta para mostrar el valor de la presión
etiqueta_presion = ttk.Label(mainframe, text="Presión: 0.00 kPa")
etiqueta_presion.grid(row=6, column=1, pady=5)

# Canvas para la barra de nivel
canvas = tk.Canvas(mainframe, width=200, height=200, bg="white")
canvas.grid(row=7, column=1, pady=5)


# Configuración inicial del GPIO y eventos
GPIO.setup(SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(SENSOR_PIN, GPIO.BOTH, callback=detectar_cambio)


# Botón de salida
boton_salida = tk.Button(mainframe, text="Salir", command=salir, bg="red", fg="white", font=("Arial", 12, "bold"))
boton_salida.grid(row=12, column=0, pady=5)  # Ajusta el espaciado

actualizar_barra()
actualizar_interfaz()
root.mainloop()