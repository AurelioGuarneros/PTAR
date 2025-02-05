from adafruit_ads1x15.analog_in import AnalogIn
import adafruit_ads1x15.ads1115 as ADS
import board
import busio
import tkinter as tk
from tkinter import ttk
import mysql.connector
import RPi.GPIO as GPIO
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import time
import threading


# Configuración de I2C y ADS1115
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
ads.gain = 1  # Rango de ±4.096V
canal = AnalogIn(ads, ADS.P0)

# Configuración del GPIO del relevador
GPIO.setmode(GPIO.BCM)
RELAY_PIN = 16  # Cambia este pin según tu conexión
RELAY_PIN2 = 12
GPIO.setup(RELAY_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(RELAY_PIN2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Configuración del pin GPIO
SENSOR_B6_PIN = 17  # Pin del sensor YF-B6
GPIO.setup(SENSOR_B6_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Constantes
FACTOR_B6 = 6.6  # YF-B6: Frecuencia = 6.6 * L/min
RELACION_TUBERIA_2 = 2.5  # Relación estimada para la tubería de 2"

# Variables globales
barra = None  # Inicializa la barra para usarla en la función
presion_min = 3.60 #2.88 #3.40  # Presión mínima en kPa
presion_max = 5.80 #6.77 #6.74  # Presión máxima en kPa
capacidad_cisterna = 2154 #3819  # Capacidad total en litros
estado_bomba = "Apagada"  # Estado inicial de la bomba
registro_hecho = {"Encendida": False, "Apagada": False}  # Controla si ya se registró el cambio de estado
estado_bomba2 = "Apagada"  # Estado inicial de la bomba
registro_hecho2 = {"Encendida": False, "Apagada": False} 
hora_encendido = None
hora_encendido2 = None
pulse_count_b6 = 0
flow_rate_b6 = 0.0
total_liters_2 = 0.0  # Litros totales estimados en la tubería de 2"
total_liters_b6 = 0.0
total_pulses_b6 = 0  # Nueva variable para la suma total de pulsos
pulses_per_second = 0  # Pulsos por segundo


# Conexión a la base de datos
def conectar_base_datos():
    try:
        conexion = mysql.connector.connect(
            host="localhost",
            user="Aurelio",
            password="RG980320",
            database="plantas"
        )
        return conexion
    except mysql.connector.Error as e:
        print(f"Error de conexión a MySQL: {e}")
        return None

# Funciones auxiliares
def calcular_presion(voltaje):
    V_offset = 0.04  # Voltaje a 0 kPa
    sensibilidad = 0.045  # Sensibilidad en V/kPa
    return (voltaje - V_offset) / sensibilidad

def guardar_en_base_datos(presion, estado_bomba1, estado_bomba2):
    conexion = conectar_base_datos()
    if conexion is None:
        print("No se pudo conectar a la base de datos.")
        return

    try:
        cursor = conexion.cursor()
        cursor.execute('''
            INSERT INTO niveles (nivel, estado_bomba, estado_bomba2)
            VALUES (%s, %s, %s)
        ''', (presion, estado_bomba1, estado_bomba2))
        conexion.commit()
    except mysql.connector.Error as e:
        print(f"Error al insertar datos en MySQL: {e}")
    finally:
        conexion.close()

def enviar_correo(bomba_numero, mensaje):
    remitente = "direcciongeneralatlcaltli@gmail.com" 
    destinatario = "luce.marahi.lopez.perez@gmail.com"
    asunto = f"Reporte PTAR Satelite - Bomba {bomba_numero}"

    msg = MIMEMultipart()
    msg["From"] = remitente
    msg["To"] = destinatario
    msg["Subject"] = asunto 
    msg.attach(MIMEText(mensaje, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(remitente, "keva tupn hgac qfay")  # Contraseña de aplicación
        server.sendmail(remitente, destinatario, msg.as_string())
        server.quit()
        print(f"Correo enviado correctamente para la Bomba {bomba_numero}")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")

    
# Función para convertir presión a litros
def presion_a_litros(presion):
    # Escalar la presión al rango de la capacidad de la cisterna
    return (presion - presion_min) / (presion_max - presion_min) * capacidad_cisterna


# Actualización de la interfaz y datos
def actualizar_barra():
    global barra, estado_bomba, estado_bomba2, registro_hecho, registro_hecho2, porcentaje_llenado, hora_encendido, hora_encendido2, total_liters_combined

    voltaje = canal.voltage  # Leer voltaje del ADS1115
    print("valor de voltaje", voltaje)
    presion = calcular_presion(voltaje)  # Convertir voltaje a presión
    print("presion", presion)
    
    # Limitar la presión al rango establecido
    presion = max(presion_min, min(presion, presion_max))  

    # Convertir presión a litros
    nivel_litros = presion_a_litros(presion)
    
    # Calcular el porcentaje de llenado
    porcentaje_llenado = ((presion - presion_min) / (presion_max - presion_min)) * 100
    porcentaje_llenado = max(0, min(porcentaje_llenado, 100))  # Asegurar que esté en el rango 0-100%

    # Actualizar etiquetas con nivel y porcentaje
    etiqueta_nivel.config(text=f"Nivel: {nivel_litros:.0f} litros ({porcentaje_llenado:.1f}%)")

    # Crear la barra de nivel si no existe
    if barra is None:
        barra = canvas.create_rectangle(50, 200, 150, 200, fill="blue")

    # Calcular altura proporcional de la barra
    altura = int(((presion - presion_min) / (presion_max - presion_min)) * 200)
    canvas.coords(barra, 50, 200 - altura, 150, 200)
    etiqueta_presion.config(text=f"Presión: {presion:.2f} kPa")


    # Leer el estado del primer relevador
    bomba_activa = GPIO.input(RELAY_PIN)
    nuevo_estado = "Encendida" if bomba_activa else "Apagada"

    # Actualizar el estado de la primera bomba y registrar en la base de datos si cambia
    if nuevo_estado != estado_bomba:
        estado_bomba = nuevo_estado
        etiqueta_estado.config(text=f"Bomba 1: {estado_bomba}", foreground="green" if estado_bomba == "Encendida" else "red")

        if nuevo_estado == "Encendida":
            hora_encendido = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Guardamos la hora de encendido
            registro_hecho["Encendida"] = True
            registro_hecho["Apagada"] = False  # Reiniciamos el estado de apagado

        elif nuevo_estado == "Apagada" and not registro_hecho["Apagada"]:
                hora_apagado = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Guardamos la hora de apagado
                mensaje = (f"Hola, buen día. La Bomba 1 se ha Apagado.\n"
                        f"🕒 Encendida: {hora_encendido}\n"
                        f"🕒 Apagada: {hora_apagado}\n"
                        f"💧 Nivel actual: {porcentaje_llenado:.0f} %.\n"
                        f"💧 litros enviados: {total_liters_combined:.0f} litros.")
                enviar_correo(1, mensaje)  # Enviamos el mensaje con las horas
                registro_hecho["Apagada"] = True
                registro_hecho["Encendida"] = False  # Reiniciar el estado de encendido


    # Leer el estado del segundo relevador
    bomba_activa2 = GPIO.input(RELAY_PIN2)
    nuevo_estado2 = "Encendida" if bomba_activa2 else "Apagada"

    # Actualizar el estado de la segunda bomba y registrar en la base de datos si cambia
    if nuevo_estado2 != estado_bomba2:
        estado_bomba2 = nuevo_estado2
        etiqueta_estado2.config(text=f"Bomba 2: {estado_bomba2}", foreground="green" if estado_bomba2 == "Encendida" else "red")

        if nuevo_estado2 == "Encendida": 
            hora_encendido2 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Guardamos la hora de encendido
            registro_hecho2["Encendida"] = True
            registro_hecho2["Apagada"] = False  # Reiniciamos el estado de apagado

        elif nuevo_estado2 == "Apagada" and not registro_hecho2["Apagada"]:
            hora_apagado2 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Guardamos la hora de apagado
            mensaje = (f"Hola, buen día. La Bomba 2 se ha Apagado.\n"
                    f"🕒 Encendida: {hora_encendido2}\n"
                    f"🕒 Apagada: {hora_apagado2}\n"
                    f"💧 Nivel actual: {porcentaje_llenado:.0f} %\n"
                    f"💧 litros enviados: {total_liters_combined:.0f} litros.")
            enviar_correo(2, mensaje)  # Enviamos el mensaje con las horas
            registro_hecho2["Apagada"] = True
            registro_hecho2["Encendida"] = False  # Reiniciar el estado de encendido
            
    total_liters_combined = total_liters_b6 + total_liters_2
            
    # Repetir la actualización cada 500 ms
    root.after(500, actualizar_barra)

#Funciones del cuenta litros
def count_pulse_b6(channel):
    global pulse_count_b6, total_pulses_b6
    pulse_count_b6 += 1
    total_pulses_b6 += 1  # Acumulador total de pulsos
    
GPIO.add_event_detect(SENSOR_B6_PIN, GPIO.RISING, callback=count_pulse_b6)

# Función para calcular el flujo y actualizar las variables
def calculate_flow_b6():
    global pulse_count_b6, flow_rate_b6, flow_rate_2, total_liters_b6, total_liters_2, pulses_per_second
    
    while True:
        time.sleep(1)  # Calcular cada segundo
        pulses_per_second = pulse_count_b6
        pulse_count_b6 = 0  # Reiniciar contador
        
        # Calcular caudal (L/min) y litros acumulados
        if pulses_per_second > 0:
            flow_rate_b6 = pulses_per_second / FACTOR_B6
            total_liters_b6 += flow_rate_b6 / 60  # Convertir a litros por segundo
            
            # Aplicar la relación para la tubería de 2"
            flow_rate_2 = flow_rate_b6 * RELACION_TUBERIA_2
            total_liters_2 += flow_rate_2 / 60
        else:
            flow_rate_b6 = 0.0
            flow_rate_2 = 0.0
            
# Función para actualizar la interfaz
def update_ui_b6():
    total_liters_combined = total_liters_b6 + total_liters_2
    
    #flow_label.config(text=f"Caudal: {flow_rate_b6:.2f} L/min")
    #flow_label_2.config(text=f"Caudal en tubería 2: {flow_rate_2:.2f} L/min")
    total_label.config(text=f"Total: {total_liters_b6:.2f} L")
    total_label_2.config(text=f"Total en tubería 2: {total_liters_2:.2f} L")
    total_combined_label.config(text=f"Total combinado: {total_liters_combined:.2f} L")
    pulses_label.config(text=f"Pulsos por segundo: {pulses_per_second}")
    total_pulses_label.config(text=f"Total de pulsos: {total_pulses_b6}")
    root.after(1000, update_ui_b6)

# Configuración de la interfaz Tkinter
root = tk.Tk()
root.title("Sensor de Presión y Bomba")
root.geometry("600x400")  # Ajustamos el tamaño para mejor visualización

# Dividir la ventana en dos secciones
left_frame = ttk.LabelFrame(root, text="Nivel Sensor", padding="10")
left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

right_frame = ttk.LabelFrame(root, text="Litros Enviados", padding="10")
right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

# Ajustar el tamaño de las columnas
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)

# --------------------- Sección Izquierda (Nivel Sensor) ---------------------
sensor_frame = ttk.Frame(left_frame, padding="10")
sensor_frame.pack(fill="both", expand=True)

etiqueta_nivel = ttk.Label(sensor_frame, text="Nivel: 0 litros")
etiqueta_nivel.pack(pady=5)

etiqueta_presion = ttk.Label(sensor_frame, text="Presión: 0.00 kPa")
etiqueta_presion.pack(pady=5)

canvas = tk.Canvas(sensor_frame, width=200, height=200, bg="white")
canvas.pack(pady=5)

etiqueta_estado = ttk.Label(sensor_frame, text="Bomba 1: Apagada", foreground="red")
etiqueta_estado.pack(pady=5)

etiqueta_estado2 = ttk.Label(sensor_frame, text="Bomba 2: Apagada", foreground="red")
etiqueta_estado2.pack(pady=5)

# --------------------- Sección Derecha (Cuenta Litros) ---------------------
frame = ttk.Frame(right_frame, padding="10")
frame.pack(fill="both", expand=True)

total_combined_label = ttk.Label(frame, text="Total combinado: 0.00 L", font=("Arial", 12))
#flow_label = ttk.Label(frame, text="Caudal: 0.00 L/min", font=("Arial", 12))
total_combined_label.pack(pady=5)


total_label_2 = ttk.Label(frame, text="Total en tubería 2: 0.00 L", font=("Arial", 12))
total_label_2.pack(pady=5)

total_label = ttk.Label(frame, text="Total: 0.00 L", font=("Arial", 12))
total_label.pack(pady=5)

pulses_label = ttk.Label(frame, text="Pulsos por segundo: 0", font=("Arial", 12))
pulses_label.pack(pady=5)

total_pulses_label = ttk.Label(frame, text="Total de pulsos: 0", font=("Arial", 12))
total_pulses_label.pack(pady=5)

# Botones de salida 
boton_salir2 = ttk.Button(frame, text="Salir", command=root.quit)
boton_salir2.pack(pady=10)


# Hilo para calcular el flujo
thread = threading.Thread(target=calculate_flow_b6, daemon=True)
thread.start()

def salir_programa():
    GPIO.cleanup()  # Apagar GPIO al salir
    root.quit()

update_ui_b6()
actualizar_barra()
root.mainloop()


