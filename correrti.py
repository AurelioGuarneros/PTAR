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

# Configuración de GPIO
GPIO.setmode(GPIO.BCM)

# Configuración para PWM
pwm_pins = [21, 20, 16]
relay_pin = 26
for pin in pwm_pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)
GPIO.setup(relay_pin, GPIO.OUT)
GPIO.output(relay_pin, GPIO.HIGH)

# Configuración para el reactor
RELE_ELECTROVALVULA_PIN = 18
GPIO.setup(RELE_ELECTROVALVULA_PIN, GPIO.OUT)
GPIO.output(RELE_ELECTROVALVULA_PIN, GPIO.HIGH)

# Configuración de GPIO
GPIO.setmode(GPIO.BCM)
SENSOR_PIN = 12  # Pin GPIO 12 para el sensor
GPIO.setup(SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Configuración de entrada con pull-up interno

# Configuración de I2C y ADS1115
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
ads.gain = 1  # Rango de ±4.096V
canal = AnalogIn(ads, ADS.P0)

# Variables globales
freq = 100
duty1 = 50
running = False
nivel_agua = 0
placas_activadas = False
reactor_id = 'R1'
MAESTRO_IP = '192.168.247.55'
MAESTRO_PORT = 12345
relay_timer_running = False
sensor_estado = "Nivel Bajo (Vacío)"  # Estado inicial
running = True
lock = threading.Lock() 
barra = None
bandera = 0


# Funciones para PWM
def pwm_thread():
    global running, freq, duty1
    period = 1.0 / freq
    dead_time = 0.0001
    while running:
        on_time = (duty1 / 100.0) * period
        off_time = period - on_time
        GPIO.output(pwm_pins[0], GPIO.HIGH)
        GPIO.output(pwm_pins[2], GPIO.HIGH)
        GPIO.output(pwm_pins[1], GPIO.LOW)
        time.sleep(on_time)
        GPIO.output(pwm_pins[0], GPIO.LOW)
        GPIO.output(pwm_pins[2], GPIO.LOW)
        time.sleep(dead_time)
        GPIO.output(pwm_pins[1], GPIO.HIGH)
        time.sleep(off_time)
        GPIO.output(pwm_pins[1], GPIO.LOW)
        time.sleep(dead_time)

def update_pwm():
    global freq, duty1, running
    try:
        freq = float(freq_entry.get())
        duty1 = float(duty_entry.get())
        running = False
        time.sleep(0.1)
        running = True
        threading.Thread(target=pwm_thread).start()
        period_ms = (1 / freq) * 1000
        on_time_ms = (duty1 / 100) * period_ms
        info_text.config(state=tk.NORMAL)
        info_text.delete("1.0", tk.END)
        info_text.insert(tk.END, f"Frecuencia: {freq} Hz\n")
        info_text.insert(tk.END, f"Período: {period_ms:.2f} ms\n")
        info_text.insert(tk.END, f"Ancho de pulso: {on_time_ms:.2f} ms\n")
        info_text.config(state=tk.DISABLED)
    except ValueError:
        pass

def toggle_relay_with_timer():
    global relay_timer_running
    if relay_timer_running:
        return  # Ignora si ya hay un temporizador en ejecución
    try:
        time_minutes = float(time_entry.get())
        time_seconds = time_minutes * 60

        GPIO.output(relay_pin, GPIO.LOW)
        relay_button.config(text="Relé Encendido", state=tk.DISABLED)
        relay_timer_running = True
        placas_label.config(text="Placas: Activadas")
        actualizar_db_en_hilo('placas', 1)

        threading.Thread(target=relay_timer, args=(time_seconds,)).start()
    except ValueError:
        pass


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
    
# Función para calcular la presión a partir del voltaje
def calcular_presion(voltaje):
    V_offset = 0.04  # Voltaje a 0 kPa
    sensibilidad = 0.045  # Sensibilidad en V/kPa
    return (voltaje - V_offset) / sensibilidad

# Función para actualizar la barra de nivel
def actualizar_barra():
    
    voltaje = canal.voltage  # Leer voltaje del ADS1115
    print('el valor del voltaje calculada es:', voltaje)
    presion = calcular_presion(voltaje)  # Convertir voltaje a presión
    print('el valor de la presion calculada es:', presion)
    #print("presion",presion)
    
# Definir el nuevo rango de presión
    global barra, bandera
    presion_min = 3.5  # Presión mínima en kPa
    presion_max = 9.26  # Presión máxima en kPa
    
# Limitar la presión al rango definido
    presion = max(presion_min, min(presion, presion_max))

# Crear la barra de nivel (un rectángulo que subirá)
    if barra is None:
        barra = canvas.create_rectangle(50, 200, 150, 200, fill="blue")
    
# Calcular altura proporcional de la barra (de 0 a 200 píxeles)
    altura = int(((presion - presion_min) / (presion_max - presion_min)) * 200)
    canvas.coords(barra, 50, 200 - altura, 150, 200)  # Ajustar el rectángulo
    etiqueta_presion.config(text=f"Presión: {presion:.2f} kPa")
    
# Verificar si la presión alcanza el máximo para apagar la bomba
   

    if presion >= 9.25 and presion <= 9.30:  
         if bandera == 0:
            desactivar_bomba1()# Ordenar al maestro apagar la bomba
            desactivar_valvula()
            bomba1_button.config(bg="red", text="Bomba 1: Apagada")  # Cambia el color y el texto del botón
            print("Bomba desactivada: presión máxima alcanzada") 
            bandera = 1
            
    root.after(1000, actualizar_barra)  # Actualiza cada segundo

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

# Crear la ventana principal
root = tk.Tk()
root.title("REACTOR 1")
root.geometry("1024x500")  # Ancho x Alto en píxeles

# Función para actualizar la interfaz gráfica
def actualizar_interfaz():
    estado_label.config(text=f"Estado del sensor: {sensor_estado}")
    root.after(100, actualizar_interfaz)

# Dividir la ventana en dos secciones
left_frame = ttk.LabelFrame(root, text="PWM y Relé", padding="10")
left_frame.grid(row=0, column=0, padx=10, pady=10, sticky=(tk.N, tk.S, tk.W, tk.E))
right_frame = ttk.LabelFrame(root, text="Control del Reactor", padding="10")
right_frame.grid(row=0, column=1, padx=10, pady=10, sticky=(tk.N, tk.S, tk.W, tk.E))
# Crear un frame para el sensor de presión dentro de la ventana principal
sensor_frame = ttk.LabelFrame(right_frame, text="Sensor de Presión", padding="10")
sensor_frame.grid(row=6, column=1,rowspan=11, sticky=(tk.N, tk.S, tk.W, tk.E))

# Widgets para PWM y Relé
freq_entry = tk.StringVar(value="100")
duty_entry = tk.StringVar(value="50")
time_entry = tk.StringVar(value="1")

ttk.Label(left_frame, text="Frecuencia (Hz)").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
ttk.Entry(left_frame, textvariable=freq_entry, width=10).grid(row=0, column=1, padx=5, pady=5)
ttk.Label(left_frame, text="Ciclo de trabajo (%)").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
ttk.Entry(left_frame, textvariable=duty_entry, width=10).grid(row=1, column=1, padx=5, pady=5)
ttk.Label(left_frame, text="Tiempo (min)").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
ttk.Entry(left_frame, textvariable=time_entry, width=10).grid(row=2, column=1, padx=5, pady=5)
info_text = tk.Text(left_frame, width=40, height=10, font=("Helvetica", 16))
info_text.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

ttk.Button(left_frame, text="Actualizar PWM", command=update_pwm).grid(row=3, column=0, columnspan=2, pady=10)

# Estilo de botones
style = ttk.Style()
style.configure("On.TButton", background="green")
style.configure("Off.TButton", background="red")
style.configure("TButton", font=("Helvetica", 16))  # Cambiar fuente y tamaño para botones
style.configure("TLabel", font=("Helvetica", 16))  # Cambiar fuente y tamaño para etiquetas


# Botón para activar el relé con temporizador
relay_button = ttk.Button(left_frame, text="Relé Apagado", command=toggle_relay_with_timer)
relay_button.grid(row=5, column=0, columnspan=2, pady=10)

# Widgets para el Reactor
valvula_label = ttk.Label(right_frame, text="Estado Válvula: Cerrada")
valvula_label.grid(row=0, column=0, columnspan=2, padx=5, pady=5)
estado_label = ttk.Label(right_frame, text=f"Estado del sensor: {sensor_estado}")
estado_label.grid(row=1, column=0, columnspan=2, padx=5, pady=5)
placas_label = ttk.Label(right_frame, text="Placas: Desactivadas")
placas_label.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

ttk.Button(right_frame, text="Activar Válvula", command=activar_valvula).grid(row=3, column=0, pady=5)
ttk.Button(right_frame, text="Desactivar Válvula", command=desactivar_valvula).grid(row=3, column=1, pady=5)

#Botones de Bombas
bomba1_button = tk.Button(right_frame, text="Bomba 1: Apagada", bg="red", command=lambda: toggle_bomba_button(bomba1_button, activar_bomba1, desactivar_bomba1, "green", "red", "Bomba 1: Encendida", "Bomba 1: Apagada"))
bomba1_button.grid(row=6, column=0, pady=5)

bomba2_button = tk.Button(right_frame, text="Bomba 2: Apagada", bg="red", command=lambda: toggle_bomba_button(bomba2_button, activar_bomba2, desactivar_bomba2, "green", "red", "Bomba 2: Encendida", "Bomba 2: Apagada"))
bomba2_button.grid(row=7, column=0, pady=5)

bombaRB1_button = tk.Button(right_frame, text="Bomba RB1: Apagada", bg="red", command=lambda: toggle_bomba_button(bombaRB1_button, activar_bombaRB1, desactivar_bombaRB1, "green", "red", "Bomba RB1: Encendida", "Bomba RB1: Apagada"))
bombaRB1_button.grid(row=8, column=0, pady=5)

bombaBC1_button = tk.Button(right_frame, text="Bomba BC1: Apagada", bg="red", command=lambda: toggle_bomba_button(bombaBC1_button, activar_bombaBC1, desactivar_bombaBC1, "green", "red", "Bomba BC1: Encendida", "Bomba BC1: Apagada"))
bombaBC1_button.grid(row=9, column=0, pady=5)

bombaBF1_button = tk.Button(right_frame, text="Buffer 1: Apagada", bg="red", command=lambda: toggle_bomba_button(bombaBF1_button, activar_buffer1, desactivar_buffer1, "green", "red", "Buffer 1: Encendida", "Buffer 1: Apagada"))
bombaBF1_button.grid(row=10, column=0, pady=5)

# Etiqueta para mostrar el valor de la presión
etiqueta_presion = ttk.Label(sensor_frame, text="Presión: 0.00 kPa")
etiqueta_presion.grid(row=6, column=1, pady=5)

# Canvas para la barra de nivel
canvas = tk.Canvas(sensor_frame, width=200, height=200, bg="white")
canvas.grid(row=7, column=1, pady=5)


# Configuración inicial del GPIO y eventos
GPIO.setup(SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(SENSOR_PIN, GPIO.BOTH, callback=detectar_cambio)


# Botón de salida
boton_salida = tk.Button(right_frame, text="Salir", command=salir, bg="red", fg="white", font=("Arial", 12, "bold"))
boton_salida.grid(row=12, column=0, pady=5)  # Ajusta el espaciado

actualizar_barra()
# Actualizar la interfaz gráfica
actualizar_interfaz()

# Ejecutar la aplicación
root.mainloop()
