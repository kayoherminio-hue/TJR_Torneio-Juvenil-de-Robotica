#!/usr/bin/env micropython

from ev3dev2.motor import LargeMotor, MediumMotor, OUTPUT_B, OUTPUT_C, OUTPUT_D
from ev3dev2.sensor.lego import ColorSensor, UltrasonicSensor, InfraredSensor
from ev3dev2.sensor import INPUT_1, INPUT_3, INPUT_2, INPUT_4
from ev3dev2.button import Button
from ev3dev2.console import Console    
import time as _t                      
from time import sleep                 
from moves import desvio, pegar, pick, soltar, tras, frente


if hasattr(_t, "ticks_ms"):
    def agora():
        return _t.ticks_ms() / 1000
else:
    def agora():
        return _t.time()

motor_e = LargeMotor(OUTPUT_B)
motor_d = LargeMotor(OUTPUT_C)
garra = MediumMotor(OUTPUT_D)

ir_e = ColorSensor(INPUT_1)
ir_d = ColorSensor(INPUT_3)
red = InfraredSensor(INPUT_4)

ultrassonico = UltrasonicSensor(INPUT_2)
btn = Button()
tela = Console(font="Lat15-Terminus12x6")   


def linha(n, texto):                        
    tela.text_at("{:<28}".format(texto), column=1, row=n)


kp = 675
kd = 875                
erro_anterior = 0       
vel = 90
ultima_curva = "direita"
count = 0
tempo_preto = None

VERDE = 3
ATRASO_VERDE = 1.0
soltou = False
tempo_soltou = 0
n_verde = 0


VEL_GIRO = 30           
KP_ALINHA = 50          
TEMPO_MAX_GIRO = 4.0    
TEMPO_MAX_ALINHA = 1.5  

def realinhar():
    motor_e.on(40)
    motor_d.on(40)
    sleep(1)
    motor_e.on(-35)
    motor_d.on(35)
    sleep(1)
    while ir_e.reflected_light_intensity >= 20:
        motor_e.on(35)
        motor_d.on(-35)
    motor_e.on(20)
    motor_d.on(-20)
    sleep(0.3)
    motor_e.on(20)
    motor_d.on(20)
    sleep(0.15)


tela.reset_console()
linha(1, "SENSORES")
linha(6, "CIMA = normal")
linha(7, "ESQ = modalidade 2")

while not (btn.up or btn.left):
    linha(2, "Esq (luz): " + str(ir_e.reflected_light_intensity))
    linha(3, "Dir (luz): " + str(ir_d.reflected_light_intensity))
    linha(4, "Ultra cm: " + str(int(ultrassonico.distance_centimeters)))
    linha(5, "IR prox: " + str(red.proximity))
    sleep(0.1)

modo2 = btn.left
tela.reset_console()                                                     
tela.text_at("MODALIDADE 2" if modo2 else "NORMAL", column=1, row=1)    
sleep(0.3)   

tempo_correcao = agora()                
pick(-1, 0.5)
while True:
    if btn.down:
        motor_e.off()
        motor_d.off()
        garra.off()
        sleep(0.5)
        
        btn.wait_for_bump('down')
        
        tempo_correcao = agora()        
        erro_anterior = 0   
        if tempo_preto is not None:
            tempo_preto = agora()       

    distancia2 = red.proximity
    distancia = ultrassonico.distance_centimeters_continuous

    '''if ir_e.color == 7 and ir_d.color == 7:
        pass'''

    e = ir_e.reflected_light_intensity
    d = ir_d.reflected_light_intensity
    

    if not soltou and e < 20 and d < 20: 
        if tempo_preto is None:
            tempo_preto = agora()                   
        elif agora() - tempo_preto >= 0.3:          
            soltar()
            tras(2)
            e = ir_e.reflected_light_intensity
            d = ir_d.reflected_light_intensity
            while e > 20 and d > 20:
                e = ir_e.reflected_light_intensity
                d = ir_d.reflected_light_intensity
                motor_e.on(-70)
                motor_d.on(-70)
            frente(1.4)
            pick(1,0.8)

            if modo2:
                realinhar()                 
                soltou = True
                tempo_soltou = agora()      
                tempo_preto = None
                erro_anterior = 0
                continue                    
            else:
                motor_e.off()
                motor_d.off()
                garra.off()
                break
    else:
        tempo_preto = None

    if not soltou: 
        if distancia <= 4 and distancia2 <= 4:
            desvio()
            erro_anterior = 0   
        elif distancia <= 4 and distancia2 >= 4:
            pegar()
            erro_anterior = 0   

    if d < 30:
        ultima_curva = "direita"
    elif e < 30:
        ultima_curva = "esquerda"

    if e > 50 and d > 50:
        erro_anterior = 0   
        if ultima_curva == "direita":
            motor_e.on(35)
            motor_d.on(-35)
        elif ultima_curva == "esquerda":
            motor_e.on(-35)
            motor_d.on(35)
        #valor normal é 10 e 20
    elif d < 7 and e >= 23:
        erro_anterior = 0   
        motor_e.on(40)
        motor_d.on(40)
        sleep(0.25)
        while ir_e.reflected_light_intensity >= 20:
            motor_e.on(35)
            motor_d.on(-35)
        motor_e.on(-25)
        motor_d.on(25)
        sleep(0.24)
        motor_e.on(20)
        motor_d.on(20)
        sleep(0.15)

    elif e < 7 and d >= 23:
        erro_anterior = 0   
        motor_e.on(40)
        motor_d.on(40)
        sleep(0.25)
        while ir_d.reflected_light_intensity >= 20:
            motor_e.on(-35)
            motor_d.on(35)
        motor_e.on(25)
        motor_d.on(-25)
        sleep(0.24)
        motor_e.on(20)
        motor_d.on(20)
        sleep(0.15)

    else:
        e_calc = 100 - e
        d_calc = 100 - d
        linha_soma = e_calc + d_calc        

        if linha_soma > 0:
            posi = (-1 * e_calc + d_calc) / linha_soma
            erro = posi

            derivada = erro - erro_anterior            
            erro_anterior = erro                       
            correcao = erro * kp + derivada * kd       

            if abs(erro) > 0.6:
                vel_atual = 82
            else:
                vel_atual = vel

            mov_e = vel_atual + correcao
            mov_d = vel_atual - correcao

            mov_e = max(-100, min(100, mov_e))
            mov_d = max(-100, min(100, mov_d))

            motor_e.on(mov_e)
            motor_d.on(mov_d)

    if soltou and agora() - tempo_soltou > ATRASO_VERDE:    
        n_verde += 1
        if n_verde % 3 == 0:
            if ir_e.color == VERDE or ir_d.color == VERDE:
                motor_e.off()
                motor_d.off()
                garra.off()
                tela.reset_console()                                      
                tela.text_at("VERDE - FIM", column=1, row=1)              
                break