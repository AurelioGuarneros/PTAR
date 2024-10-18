import socket
import threading
import RPi.GPIO as GPIO

# Configuración de GPIO
BOMBA1_PIN = 17  # Cambia al pin que estés utilizando para la bomba 1
BOMBA2_PIN = 27  # Cambia al pin que estés utilizando para la bomba 2

GPIO.setmode(GPIO.BCM)
GPIO.setup(BOMBA1_PIN, GPIO.OUT)
GPIO.setup(BOMBA2_PIN, GPIO.OUT)
GPIO.output(BOMBA1_PIN, GPIO.HIGH)  # Bomba 1 inicialmente apagada
GPIO.output(BOMBA2_PIN, GPIO.HIGH)  # Bomba 2 inicialmente apagada

# Función para manejar las órdenes de las bombas
def manejar_orden_bomba(orden):
    if orden == 'ACTIVAR_BOMBA_1':
        GPIO.output(BOMBA1_PIN, GPIO.LOW)
        print("Bomba 1 activada")
    elif orden == 'DESACTIVAR_BOMBA_1':
        GPIO.output(BOMBA1_PIN, GPIO.HIGH)
        print("Bomba 1 desactivada")
    elif orden == 'ACTIVAR_BOMBA_2':
        GPIO.output(BOMBA2_PIN, GPIO.LOW)
        print("Bomba 2 activada")
    elif orden == 'DESACTIVAR_BOMBA_2':
        GPIO.output(BOMBA2_PIN, GPIO.HIGH)
        print("Bomba 2 desactivada")

# Función para escuchar órdenes desde el esclavo
def escuchar_ordenes():
    servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor_socket.bind(('192.168.0.101', 12345))  # IP del maestro
    servidor_socket.listen(5)
    print("Esperando conexiones en 192.168.0.100:12345")

    while True:
        conn, addr = servidor_socket.accept()
        print(f"Conexión recibida de {addr}")
        orden = conn.recv(1024).decode()
        if orden:
            manejar_orden_bomba(orden)
        conn.close()

# Iniciar hilo para escuchar órdenes
hilo_escucha = threading.Thread(target=escuchar_ordenes)
hilo_escucha.start()

# Mantener el hilo principal activo
try:
    while True:
        pass
except KeyboardInterrupt:
    GPIO.cleanup()
