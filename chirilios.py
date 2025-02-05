import socket
import threading
import RPi.GPIO as GPIO
import mysql.connector
from mysql.connector import Error
import tkinter as tk
from tkinter import messagebox, scrolledtext

# Configuración de GPIO
BOMBA1_PIN = 17  # Cambia al pin que estés utilizando para la bomba 1
BOMBA2_PIN = 27  # Cambia al pin que estés utilizando para la bomba 2
BOMBARB3_PIN = 23 #bomba R3
BOMBABC3_PIN = 24
BOMBARB2_PIN = 9  #BOMBA R2
BOMBABC2_PIN = 11
BOMBARB1_PIN = 25 #Bomba R1
BOMBABC1_PIN = 8
Buffer1_PIN = 1
Buffer2_PIN = 7
Buffer3_PIN = 12
BombaFP_PIN = 22 #Filtro Prensa
BombaFD_PIN = 10 #fintro discos


GPIO.setmode(GPIO.BCM)
GPIO.setup(BOMBA1_PIN, GPIO.OUT)
GPIO.setup(BOMBA2_PIN, GPIO.OUT)
GPIO.setup(BOMBARB3_PIN, GPIO.OUT)
GPIO.setup(BOMBABC3_PIN, GPIO.OUT)
GPIO.setup(BOMBARB2_PIN, GPIO.OUT)
GPIO.setup(BOMBABC2_PIN, GPIO.OUT)
GPIO.setup(BOMBARB1_PIN, GPIO.OUT)
GPIO.setup(BOMBABC1_PIN, GPIO.OUT)
GPIO.setup(Buffer1_PIN, GPIO.OUT)
GPIO.setup(Buffer2_PIN, GPIO.OUT)
GPIO.setup(Buffer3_PIN, GPIO.OUT)
GPIO.setup(BombaFP_PIN, GPIO.OUT)
GPIO.setup(BombaFD_PIN, GPIO.OUT)
GPIO.output(BOMBA1_PIN, GPIO.LOW)  # Bomba 1 inicialmente apagada
GPIO.output(BOMBA2_PIN, GPIO.LOW)  # Bomba 2 inicialmente apagada 
GPIO.output(BOMBARB3_PIN, GPIO.LOW)
GPIO.output(BOMBABC3_PIN, GPIO.LOW)
GPIO.output(BOMBARB2_PIN, GPIO.LOW)
GPIO.output(BOMBABC2_PIN, GPIO.LOW)
GPIO.output(BOMBARB1_PIN, GPIO.LOW)
GPIO.output(BOMBABC1_PIN, GPIO.LOW)
GPIO.output(Buffer1_PIN, GPIO.LOW)
GPIO.output(Buffer2_PIN, GPIO.LOW)
GPIO.output(Buffer3_PIN, GPIO.LOW)
GPIO.output(BombaFP_PIN, GPIO.LOW)
GPIO.output(BombaFD_PIN, GPIO.LOW)

# Variable global para el socket del servidor y el log de mensajes
servidor_socket = None
log_widget = None

# Función para redirigir print al widget de texto
class RedirectText:
    def __init__(self, widget):
        self.widget = widget

    def write(self, message):
        self.widget.insert(tk.END, message)
        self.widget.see(tk.END)  # Desplazar automáticamente al final

    def flush(self):  # Dummy flush method
        pass

# Función para conectar a la base de datos
def conectar_db():
    try:
        conn = mysql.connector.connect(
            host='localhost',  # Cambia a la IP del servidor MariaDB
            user='Aurelio',
            password='RG980320',
            database='planta'
        )
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

# Función para guardar el estado de las bombas en la base de datos
def registrar_bomba_en_db(bomba, procedencia):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO estados (bomba, procedencia) VALUES (%s, %s)", (bomba, procedencia))
            print(f"Registrado en DB: bomba={bomba}, procedencia={procedencia}")
            conn.commit()
            cursor.close()
        except Error as e:
            print(f"Error al guardar en la base de datos: {e}")
        finally:
            conn.close()

# Función para manejar la orden de las bombas
def manejar_orden_bomba(orden):
    partes = orden.split(':')
    if len(partes) == 2:
        reactor_id, accion_bomba = partes
        procedencia = f"Reactor {reactor_id}"
        print(f"Procesando: reactor_id={reactor_id}, accion_bomba={accion_bomba}")
        if accion_bomba == "ACTIVAR_BOMBA_1":
            GPIO.output(BOMBA1_PIN, GPIO.HIGH)
            print("Bomba 1 activada")
            bmb='B1'
            registrar_bomba_en_db(bmb, procedencia)
        elif accion_bomba == "DESACTIVAR_BOMBA_1":
            GPIO.output(BOMBA1_PIN, GPIO.LOW)
            print("Bomba 1 desactivada")
            bmb='B10'
            registrar_bomba_en_db(bmb, procedencia)
        elif accion_bomba == "ACTIVAR_BOMBA_2":
            GPIO.output(BOMBA2_PIN, GPIO.HIGH)
            print("Bomba 2 activada")
            bmb='B2'
            registrar_bomba_en_db(bmb, procedencia)
        elif accion_bomba == "DESACTIVAR_BOMBA_2":
            GPIO.output(BOMBA2_PIN, GPIO.LOW)
            print("Bomba 2 desactivada")
            bmb='B20'
            registrar_bomba_en_db(bmb, procedencia)
        elif accion_bomba == "ACTIVAR_BOMBA_RB3":
            GPIO.output(BOMBARB3_PIN, GPIO.HIGH)
            print("Bomba RB3 activada")
            bmb='BRB3'
            registrar_bomba_en_db(bmb, procedencia)
        elif accion_bomba == "DESACTIVAR_BOMBA_RB3":
            GPIO.output(BOMBARB3_PIN, GPIO.LOW)
            print("Bomba RB3 desactivada")
            bmb='BRB30'
            registrar_bomba_en_db(bmb, procedencia)
        elif accion_bomba == "ACTIVAR_BOMBA_BC3":
            GPIO.output(BOMBABC3_PIN, GPIO.HIGH)
            print("Bomba BC3 activada")
            bmb='BBC3'
            registrar_bomba_en_db(bmb, procedencia)
        elif accion_bomba == "DESACTIVAR_BOMBA_BC3":
            GPIO.output(BOMBABC3_PIN, GPIO.LOW)
            print("Bomba BC3 desactivada")
            bmb='BBC30'
            registrar_bomba_en_db(bmb, procedencia)
        elif accion_bomba == "ACTIVAR_BOMBA_RB2":
            GPIO.output(BOMBARB2_PIN, GPIO.HIGH)
            print("Bomba RB2 activada")
            bmb='BRB2'
            registrar_bomba_en_db(bmb, procedencia)
        elif accion_bomba == "DESACTIVAR_BOMBA_RB2":
            GPIO.output(BOMBARB2_PIN, GPIO.LOW)
            print("Bomba RB2 desactivada")
            bmb='BRB20'
            registrar_bomba_en_db(bmb, procedencia)
        elif accion_bomba == "ACTIVAR_BOMBA_BC2":
            GPIO.output(BOMBABC2_PIN, GPIO.HIGH)
            print("Bomba BC2 activada")
            bmb='BBC2'
            registrar_bomba_en_db(bmb, procedencia)
        elif accion_bomba == "DESACTIVAR_BOMBA_BC2":
            GPIO.output(BOMBABC2_PIN, GPIO.LOW)
            print("Bomba BC2 desactivada")
            bmb='BBC20'
            registrar_bomba_en_db(bmb, procedencia)
        elif accion_bomba == "ACTIVAR_BOMBA_RB1":
            GPIO.output(BOMBARB1_PIN, GPIO.HIGH)
            print("Bomba RB1 activada")
            bmb='BRB1'
            registrar_bomba_en_db(bmb, procedencia)
        elif accion_bomba == "DESACTIVAR_BOMBA_RB1":
            GPIO.output(BOMBARB1_PIN, GPIO.LOW)
            print("Bomba RB1 desactivada")
            bmb='BRB10'
            registrar_bomba_en_db(bmb, procedencia)
        elif accion_bomba == "ACTIVAR_BOMBA_BC1":
            GPIO.output(BOMBABC1_PIN, GPIO.HIGH)
            print("Bomba BC1 activada")
            bmb='BBC1'
            registrar_bomba_en_db(bmb, procedencia)
        elif accion_bomba == "DESACTIVAR_BOMBA_BC1":
            GPIO.output(BOMBABC1_PIN, GPIO.LOW)
            print("Bomba BC1 desactivada")
            bmb='BBC10'
            registrar_bomba_en_db(bmb, procedencia)
        elif accion_bomba == "ACTIVAR_Buffer_1":
            GPIO.output(Buffer1_PIN, GPIO.HIGH)
            print("Buffer 1 activada")
            bmb='Buf1'
            registrar_bomba_en_db(bmb, procedencia)
        elif accion_bomba == "DESACTIVAR_Buffer_1":
            GPIO.output(Buffer1_PIN, GPIO.LOW)
            print("Buffer 1 desactivada")
            bmb='Buf10'
            registrar_bomba_en_db(bmb, procedencia)  
        elif accion_bomba == "ACTIVAR_Buffer_2":
            GPIO.output(Buffer2_PIN, GPIO.HIGH)
            print("Buffer 2 activada")
            bmb='Buf2'
            registrar_bomba_en_db(bmb, procedencia)
        elif accion_bomba == "DESACTIVAR_Buffer_2":
            GPIO.output(Buffer2_PIN, GPIO.LOW)
            print("Buffer 2 desactivada")
            bmb='Buf20'
            registrar_bomba_en_db(bmb, procedencia) 
        elif accion_bomba == "ACTIVAR_Buffer_3":
            GPIO.output(Buffer3_PIN, GPIO.HIGH)
            print("Buffer 3 activada")
            bmb='Buf3' #registro de inicio de buffer
            registrar_bomba_en_db(bmb, procedencia)
        elif accion_bomba == "DESACTIVAR_Buffer_3":
            GPIO.output(Buffer3_PIN, GPIO.LOW)
            print("Buffer 3 desactivada")
            bmb='Buf30' #registro de final de buffer
            registrar_bomba_en_db(bmb, procedencia)
         
        else:
            print(f"Acción desconocida: {accion_bomba}")
    else:
        print("Formato de mensaje incorrecto")

# Función para escuchar órdenes desde el esclavo
def escuchar_ordenes():
    global servidor_socket
    servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor_socket.bind(('192.168.247.55', 12345))
    servidor_socket.listen(5)
    print("Esperando conexiones en 192.168.247.55:12345")

    while True:
        conn, addr = servidor_socket.accept()
        print(f"Conexión recibida de {addr}")
        orden = conn.recv(1024).decode()
        print(f"Orden recibida: {orden}")
        if orden:
            manejar_orden_bomba(orden)
        conn.close()

# Función para cerrar el socket y limpiar GPIO
def salir():
    global servidor_socket
    if servidor_socket:
        servidor_socket.close()
        print("Socket cerrado")
    GPIO.cleanup()
    print("GPIO limpio")
    exit(0)
            
# Función para alternar estado de la bomba de filtro discos
def toggle_bombad():
    current_state = GPIO.input(BombaFD_PIN)
    new_state = not current_state
    GPIO.output(BombaFD_PIN, new_state)
    button_fd.config(text="Activar FD" if not new_state else "Desactivar FD")
    print("Filtro Discos", "activado" if new_state else "desactivado")
    registrar_bomba_en_db('FD', "Filtro Discos")

# Función para alternar estado de la bomba de filtro prensa
def toggle_bombafp():
    current_state = GPIO.input(BombaFP_PIN)
    new_state = not current_state
    GPIO.output(BombaFP_PIN, new_state)
    button_fp.config(text="Activar FP" if not new_state else "Desactivar FP")
    print("Filtro Prensa", "activado" if new_state else "desactivado")
    registrar_bomba_en_db('FP', "Filtro Prensa")
            

# Interfaz gráfica con Tkinter
def iniciar_interfaz():
    global log_widget, button_fd, button_fp
    ventana = tk.Tk()
    ventana.title("Control de Bombas y Selenoide")
    
# Crear un marco principal para organizar los widgets
    marco_principal = tk.Frame(ventana)
    marco_principal.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    

# Sección para el log
    log_frame = tk.LabelFrame(marco_principal, text="Log de Eventos")
    log_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
    log_widget = scrolledtext.ScrolledText(log_frame, width=60, height=15, state='normal')
    log_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    

# Redirigir stdout al widget de texto
    import sys
    sys.stdout = RedirectText(log_widget)
    
# Botón para Bomba Filtro Discos
    button_fd = tk.Button(marco_principal, text="Activar FD", command=toggle_bombad, bg="lightblue")
    button_fd.grid(row=1, column=0, padx=10, pady=5)

# Botón para Bomba Filtro Prensa
    button_fp = tk.Button(marco_principal, text="Activar FP", command=toggle_bombafp, bg="lightgreen")
    button_fp.grid(row=1, column=1, padx=10, pady=5)
    
# Botón para salir
    boton_salir = tk.Button(marco_principal, text="Salir", command=salir, bg="red", fg="white")
    boton_salir.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

# Configuración de redimensionamiento
    ventana.columnconfigure(0, weight=1)
    ventana.rowconfigure(0, weight=1)
    marco_principal.columnconfigure([0, 1], weight=1)
    marco_principal.rowconfigure([0, 1], weight=1)

# Manejo de cierre de ventana
    ventana.protocol("WM_DELETE_WINDOW", confirmar_salida)
    ventana.mainloop()

# Función para confirmar la salida
def confirmar_salida():
    if messagebox.askyesno("Salir", "¿Estás seguro de que deseas salir?"):
        salir()

# Iniciar hilo para escuchar órdenes
hilo_escucha = threading.Thread(target=escuchar_ordenes, daemon=True)
hilo_escucha.start()

# Iniciar la interfaz gráfica
iniciar_interfaz()
