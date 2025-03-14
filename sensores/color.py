import tkinter as tk
import RPi.GPIO as GPIO
import time

# Definir pines
S0, S1, S2, S3, OUT = 14, 15, 18, 23, 24
LED_R, LED_A, LED_V = 17, 27, 22

# Configurar GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup([S0, S1, S2, S3], GPIO.OUT)
GPIO.setup(OUT, GPIO.IN)
GPIO.setup([LED_R, LED_A, LED_V], GPIO.OUT)

GPIO.output(S0, GPIO.HIGH)
GPIO.output(S1, GPIO.HIGH)
GPIO.output(LED_R, GPIO.LOW)
GPIO.output(LED_A, GPIO.LOW)
GPIO.output(LED_V, GPIO.LOW)

def read_color():
    GPIO.output(S2, GPIO.LOW)
    GPIO.output(S3, GPIO.LOW)
    rojo = pulse_in(OUT)
    
    GPIO.output(S3, GPIO.HIGH)
    azul = pulse_in(OUT)
    
    GPIO.output(S2, GPIO.HIGH)
    verde = pulse_in(OUT)
    
    return rojo, verde, azul

def pulse_in(pin):
    start_time = time.time()
    while GPIO.input(pin) == GPIO.LOW:
        if time.time() - start_time > 0.1:
            return 0
    start = time.time()
    while GPIO.input(pin) == GPIO.HIGH:
        if time.time() - start_time > 0.1:
            return 0
    return (time.time() - start) * 1000000

def update_display():
    global label_color, result_label, root
    rojo, verde, azul = read_color()
    color_str = f"R: {rojo}  V: {verde}  A: {azul}"
    label_color.config(text=color_str)
    
    GPIO.output([LED_R, LED_A, LED_V], GPIO.LOW)
    if (rojo > 5 and verde > azul and verde > 7 and rojo < 20):
        result_label.config(text="Rojo")
    elif (azul < rojo and azul > verde and verde < azul):
        result_label.config(text="Verde")
    elif (azul < rojo and azul < verde and verde < rojo):
        result_label.config(text="Azul")
    elif (verde > 5 and verde < 20 and azul < 18 and rojo < 20):
        result_label.config(text="Amarillo")
    elif (verde > 52 and verde < 63 and azul < 50 and rojo < 47):
        result_label.config(text="Negro")
        GPIO.output(LED_R, GPIO.HIGH)
    elif (verde > 26 and verde < 30 and azul < 26 and rojo < 24):
        result_label.config(text="Transparente")
        GPIO.output(LED_V, GPIO.HIGH)
    elif (verde > 23 and verde < 38 and azul < 34 and rojo < 27):
        result_label.config(text="Transparente Amarilla")
        GPIO.output(LED_A, GPIO.HIGH)
    else:
        result_label.config(text="No identificado")
    
    root.after(900, update_display)

def sensor_color():
    # Configurar interfaz gráfica
    root = tk.Tk()
    root.title("Sensor de Color")

    label_color = tk.Label(root, text="R: 0  V: 0  A: 0", font=("Arial", 14))
    label_color.pack()

    result_label = tk.Label(root, text="No identificado", font=("Arial", 16, "bold"))
    result_label.pack()

    root.after(900, update_display)
    root.mainloop()

GPIO.cleanup()
