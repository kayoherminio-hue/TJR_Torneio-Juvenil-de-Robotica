#!/usr/bin/env python3

from pybricks.hubs import EV3Brick

from pybricks.ev3devices import Motor, ColorSensor

from pybricks.parameters import Port, Color

from pybricks.tools import wait


ev3 = EV3Brick()

motor_e = Motor(Port.B)
motor_d = Motor(Port.C)

ir_e = ColorSensor(Port.S1)
ir_d = ColorSensor(Port.S3)


vel = 300
Kp = 200
erro2 = 0


def frente(vel, tempo:int):
    motor_e.run(vel)
    motor_d.run(vel)
    wait(tempo)


def esquerda(vel, tempo:int):
    motor_e.run(-vel)
    motor_d.run(vel)
    wait(tempo)


def direita(vel, tempo:int):
    motor_e.run(vel)
    motor_d.run(-vel)
    wait(tempo)





def pid():

    global erro2

    e = ir_e.reflection()
    d = ir_d.reflection()
    e = 100 - e
    d = 100 - d

    linha = e + d

    if linha > 20:

        posicao = (-1 * e + 1 * d) / linha

        erro = posicao
        erro2 = erro
        correcao = Kp * erro
        motor_e.run(vel + correcao)
        motor_d.run(vel - correcao)

    else:

        if erro2 > 0:
            motor_e.run(300)
            motor_d.run(-300)

        else:
            motor_e.run(-300)
            motor_d.run(300)


while True:

    pid()

    wait(10)