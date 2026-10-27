from ev3dev2.motor import LargeMotor, MediumMotor, OUTPUT_B, OUTPUT_C, OUTPUT_D
from time import sleep
from ev3dev2.sensor.lego import ColorSensor
from ev3dev2.sensor import INPUT_1, INPUT_3


ir_e = ColorSensor(INPUT_1)
ir_d = ColorSensor(INPUT_3)

motor_e = LargeMotor(OUTPUT_B)
motor_d = LargeMotor(OUTPUT_C)
garra = MediumMotor(OUTPUT_D)

def frente(tempo:float):
    motor_e.on(40)
    motor_d.on(40)
    sleep(tempo)
    motor_e.off()
    motor_d.off()
def tras(tempo:float):
    motor_e.on(-40)
    motor_d.on(-40)
    sleep(tempo)
    motor_e.off()
    motor_d.off()
def esquerda(tempo:float):
    motor_e.on(-40)
    motor_d.on(40)
    sleep(tempo)
def direita(tempo:float):
    motor_e.on(40)
    motor_d.on(-40)
    sleep(tempo)


def desvio():
    tras(0.6)
    direita(0.9)
    frente(1.7)
    esquerda(0.9)
    frente (2)
    esquerda(1.1)
    frente(1)
    while ir_e.reflected_light_intensity >= 20:
        motor_e.on(35)
        motor_d.on(35)
    frente(0.4)
    while ir_d.reflected_light_intensity >= 20:
        motor_e.on(35)
        motor_d.on(-35)
    direita(0.3)

def pick(direcao: int, tempo: int):
    garra.on(direcao*80)
    sleep(tempo)
    garra.stop_action = 'hold'
    garra.off()

def pegar():
    tras(1.1)
    garra.on_for_seconds(80,0.8,block=False)
    direita(2.4)    
    tras(1.2)
    pick(-1,1.2)
    #garra.hold()
    frente(0.8)
    direita(1)
    motor_e.on(40)
    motor_d.on(-40)
    sleep(0.7)
    motor_e.on(-40)
    motor_d.on(40)
    sleep(0.5)
    while ir_d.reflected_light_intensity >= 20:
        motor_e.on(40)
        motor_d.on(-40)
    direita(0.3)

def soltar():
    tras(1.1)
    direita(3)    
   # tras(0.85)
   # motor_e.off()
   # motor_d.off()
   # pick(1,0.8)'''
    #frente(1.5)
    #pick(-1,1)

def soltar2():
    tras(1.1)
    direita(2.8)    
    tras(0.85)
    motor_e.off()
    motor_d.off()
    pick(1,0.8)
    frente(1.5)
    pick(-1, 1.2)
    #frente(1.5)
    #pick(-1,1)

