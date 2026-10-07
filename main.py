#!/usr/bin/env python3

from ev3dev2.motor import LargeMotor, OUTPUT_B, OUTPUT_C
from ev3dev2.sensor.lego import ColorSensor
from ev3dev2.sensor import INPUT_1, INPUT_3
from time import sleep

motor_e = LargeMotor(OUTPUT_B)
motor_d = LargeMotor(OUTPUT_C)

ir_e = ColorSensor(INPUT_1)
ir_d = ColorSensor(INPUT_3)

kp = 100
vel = 15

while True:

    e = ir_e.reflected_light_intensity
    d = ir_d.reflected_light_intensity

    if d < 20 and e >= 20:

        while ir_e.reflected_light_intensity >= 20:
            motor_e.on(40)
            motor_d.on(-40)

        motor_e.on(-25)
        motor_d.on(25)
        sleep(0.25)

    elif e < 20 and d >= 20:

        while ir_d.reflected_light_intensity >= 20:
            motor_e.on(-40)
            motor_d.on(40)

        motor_e.on(25)
        motor_d.on(-25)
        sleep(0.25)

    else:

        e = 100 - e
        d = 100 - d

        linha = e + d

        if linha > 0:
            posi = (-1 * e + d) / linha
            erro = posi

            correcao = erro * kp

            mov_e = vel + correcao
            mov_d = vel - correcao

            mov_e = max(-100, min(100, mov_e))
            mov_d = max(-100, min(100, mov_d))

            motor_e.on(mov_e)
            motor_d.on(mov_d)