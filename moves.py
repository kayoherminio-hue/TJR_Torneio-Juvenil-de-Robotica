from ev3dev2.motor import LargeMotor, MediumMotor, OUTPUT_B, OUTPUT_C, OUTPUT_D
from time import sleep
from ev3dev2.sensor.lego import ColorSensor, UltrasonicSensor, InfraredSensor
from ev3dev2.sensor import INPUT_1, INPUT_3, INPUT_2, INPUT_4


ir_e = ColorSensor(INPUT_1)
ir_d = ColorSensor(INPUT_3)
red = InfraredSensor(INPUT_4)
ultrassonico = UltrasonicSensor(INPUT_2)

motor_e = LargeMotor(OUTPUT_B)
motor_d = LargeMotor(OUTPUT_C)
garra = MediumMotor(OUTPUT_D)

area = False
tempo = 0

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

def desvio_por_grau():
    motor_e.on_for_degrees(-50, 360, block = False)
    motor_d.on_for_degrees(-50, 360, block = True)

    motor_e.on_for_degrees(50, 480, block = False)
    motor_d.on_for_degrees(-50, 480, block = True)

    motor_e.on_for_degrees(50, 700, block = False)
    motor_d.on_for_degrees(50, 700, block = True)

    motor_e.on_for_degrees(-50, 480, block = False)
    motor_d.on_for_degrees(50, 480, block = True)

    motor_e.on_for_degrees(50, 1150, block = False)
    motor_d.on_for_degrees(50, 1150, block = True)

    motor_e.on_for_degrees(-50, 480, block = False)
    motor_d.on_for_degrees(50, 480, block = True)

    motor_e.on_for_degrees(50, 300, block = False)
    motor_d.on_for_degrees(50, 300, block = True)

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
   # pick(1,0.8)
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

def reto(distancia: int):
    motor_e.position = 0
    motor_d.position = 0
    while motor_e.position < distancia:
        dis = ultrassonico.distance_centimeters_continuous
        if dis <= 4:
            motor_e.off()
            motor_d.off()
            if red.proximity <=4:
                desvio_por_grau()
            else:
                pegar()
        dif = motor_e.position - motor_d.position 
        motor_e.on(max(20,min(80,40 - dif*2)))
        motor_d.on(max(20,min(80,40 + dif*2)))
    motor_e.off()
    motor_d.off()

def resgate(e,d,t):
    global tempo, area
    if e < 20 and d < 20 and not area:
        area = True
        tempo = t

    if area:
        if (t - tempo > 0.3) and (e < 20 or d < 20):
            area = False
        elif t - tempo >= 3:
            motor_e.off()
            motor_d.off()
            while ir_e.reflected_light_intensity > 10 and ir_d.reflected_light_intensity > 10:
                dif = motor_e.position - motor_d.position 
                motor_e.on(max(-100, min(100, 50 - dif * 2)))
                motor_d.on(max(-100, min(100, 50 + dif * 2)))
            motor_e.on_for_degrees(-50, 180, block = False)
            motor_d.on_for_degrees(-50, 180, block = True)           
            motor_e.on_for_degrees(-50, 480, block = False)
            motor_d.on_for_degrees(50, 480, block = True)
            while ir_e.reflected_light_intensity > 10 and ir_d.reflected_light_intensity > 10:
                motor_e.on(-50)
                motor_d.on(-50)
            area = False
            return True
    return False
                
