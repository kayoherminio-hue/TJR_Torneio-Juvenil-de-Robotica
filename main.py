#!/usr/bin/env python3

from ev3dev2.motor import LargeMotor, MediumMotor, OUTPUT_B, OUTPUT_C, OUTPUT_D
from ev3dev2.sensor.lego import ColorSensor, UltrasonicSensor, InfraredSensor
from ev3dev2.sensor import INPUT_1, INPUT_3, INPUT_2, INPUT_4
from time import sleep
from moves import desvio, pegar, pick, soltar 
from time import sleep, time

motor_e = LargeMotor(OUTPUT_B)
motor_d = LargeMotor(OUTPUT_C)
garra = MediumMotor(OUTPUT_D)

ir_e = ColorSensor(INPUT_1)
ir_d = ColorSensor(INPUT_3)
red = InfraredSensor(INPUT_4)

ultrassonico = UltrasonicSensor(INPUT_2)
tempo_correcao = time()

kp = 90
vel = 40
ultima_curva = "direita"
count = 0
#pick(-1,0.8)
while True:
    '''count += 1 
    if count >= 150:
        pick(-1,0.2)
        count = 0'''
    distancia2 = red.proximity
    distancia = ultrassonico.distance_centimeters_continuous

    e = ir_e.reflected_light_intensity
    d = ir_d.reflected_light_intensity

    
    if time() - tempo_correcao >= 3:
        garra.on_for_seconds(
            speed=-35,
            seconds=0.4,
            brake=True,
            block=False
        )
    tempo_correcao = time()
    if e < 20 and d < 20:
        if tempo_preto is None:
            tempo_preto = time()

        elif time() - tempo_preto >= 0.5:
            soltar()
            motor_e.off()
            motor_d.off()
            #garra.stop_action = 'hold'
            garra.off()
            break
    else:
        tempo_preto = None
    '''if ir_e.color == 3 and ir_d.color == 3:
        motor_e.off()
        motor_d.off()
        break'''

    if distancia <= 4 and distancia2 <= 4:
        desvio()

    elif distancia <= 4 and distancia2 >= 4:
        pegar()

    if d < 30:
        ultima_curva = "direita"
    elif e < 30:
        ultima_curva = "esquerda"

    if e > 50 and d > 50:
        if ultima_curva == "direita":
            motor_e.on(35)
            motor_d.on(-35)
        elif ultima_curva == "esquerda":
            motor_e.on(-35)
            motor_d.on(35)

    elif d < 20 and e >= 20:
        motor_e.on(20)
        motor_d.on(20)
        sleep(0.25)
        while ir_e.reflected_light_intensity >= 20:
            motor_e.on(35)
            motor_d.on(-35)

        motor_e.on(-20)
        motor_d.on(20)
        sleep(0.3)

        motor_e.on(20)
        motor_d.on(20)
        sleep(0.15)

    elif e < 20 and d >= 20:
        motor_e.on(20)
        motor_d.on(20)
        sleep(0.25)
        while ir_d.reflected_light_intensity >= 20:
            motor_e.on(-35)
            motor_d.on(35)

        motor_e.on(20)
        motor_d.on(-20)
        sleep(0.3)

        motor_e.on(20)
        motor_d.on(20)
        sleep(0.15)

    else:
        e_calc = 100 - e
        d_calc = 100 - d

        linha = e_calc + d_calc

        if linha > 0:
            posi = (-1 * e_calc + d_calc) / linha
            erro = posi
            correcao = erro * kp

            if abs(erro) > 0.6:
                vel_atual = 33
            else:
                vel_atual = vel

            mov_e = vel_atual + correcao
            mov_d = vel_atual - correcao

            mov_e = max(-100, min(100, mov_e))
            mov_d = max(-100, min(100, mov_d))

            motor_e.on(mov_e)
            motor_d.on(mov_d)

    sleep(0.01)