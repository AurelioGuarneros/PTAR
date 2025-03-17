import tkinter as tk
import RPi.GPIO as GPIO

# Configuración de pines
PIN_PWM1 = 36  # GPIO físico 36
PIN_PWM2 = 38  # GPIO físico 38
FREQ = 1000    # Frecuencia inicial del PWM en Hz

# Configurar GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setup(PIN_PWM1, GPIO.OUT)
GPIO.setup(PIN_PWM2, GPIO.OUT)

# Iniciar PWM
pwm1 = GPIO.PWM(PIN_PWM1, FREQ)
pwm2 = GPIO.PWM(PIN_PWM2, FREQ)
pwm1.start(0)
pwm2.start(0)

# Función para actualizar el ciclo de trabajo de pwm1
def update_pwm1(value):
    pwm1.ChangeDutyCycle(int(value))
    label1.config(text=f"PWM1: {value}%")

# Función para actualizar el ciclo de trabajo de pwm2
def update_pwm2(value):
    pwm2.ChangeDutyCycle(int(value))
    label2.config(text=f"PWM2: {value}%")

# Función para actualizar la frecuencia de pwm1
def update_freq1(value):
    new_freq = int(value)
    pwm1.ChangeFrequency(new_freq)
    label_freq1.config(text=f"Frecuencia PWM1: {new_freq} Hz")

# Crear ventana Tkinter
root = tk.Tk()
root.title("Control de PWM")
root.geometry("300x300")

# Control para PWM1
label1 = tk.Label(root, text="PWM1: 0%", font=("Arial", 12))
label1.pack()
scale1 = tk.Scale(root, from_=0, to=100, orient=tk.HORIZONTAL, command=update_pwm1)
scale1.pack()

# Control para Frecuencia de PWM1
label_freq1 = tk.Label(root, text=f"Frecuencia PWM1: {FREQ} Hz", font=("Arial", 12))
label_freq1.pack()
scale_freq1 = tk.Scale(root, from_=100, to=1500, orient=tk.HORIZONTAL, command=update_freq1)
scale_freq1.set(FREQ)
scale_freq1.pack()

# Control para PWM2
label2 = tk.Label(root, text="PWM2: 0%", font=("Arial", 12))
label2.pack()
scale2 = tk.Scale(root, from_=0, to=100, orient=tk.HORIZONTAL, command=update_pwm2)
scale2.pack()

# Botón para salir
def close_app():
    pwm1.stop()
    pwm2.stop()
    GPIO.cleanup()
    root.destroy()

btn_exit = tk.Button(root, text="Salir", command=close_app)
btn_exit.pack()

root.mainloop()

