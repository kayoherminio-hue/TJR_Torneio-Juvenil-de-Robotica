#!/usr/bin/env python3

from ev3dev2.motor import LargeMotor, OUTPUT_B, OUTPUT_C
from ev3dev2.sensor.lego import ColorSensor, UltrasonicSensor
from ev3dev2.sensor import INPUT_1, INPUT_3, INPUT_2
from time import sleep
from moves import desvio

# Configuração dos motores
motor_e = LargeMotor(OUTPUT_B)
motor_d = LargeMotor(OUTPUT_C)

# Configuração dos sensores
ir_e = ColorSensor(INPUT_1)
ir_d = ColorSensor(INPUT_3)
ultrassonico = UltrasonicSensor(INPUT_2)

# --- Constantes do Controle PD ---
kp = 90
kd = 120    # Constante Derivativa (Dica: Comece testando valores entre 50 e 150)
vel = 10
erro_anterior = 0  # Armazena o erro passado para calcular a derivada

while True:
    # 1. Leitura do Ultrassônico para desvio
    distancia = ultrassonico.distance_centimeters_continuous
    if distancia <= 10:
        desvio()

    # 2. Leitura dos Sensores de Cor
    e = ir_e.reflected_light_intensity
    d = ir_d.reflected_light_intensity

    # --- LÓGICA DE CURVAS 90 GRAUS (Sem Sleep) ---
    # Curva de 90 graus para a DIREITA (Sensor direito viu preto, esquerdo viu branco)
    if d < 20 and e >= 20:
        # Gira no próprio eixo enquanto não encontrar a linha
        while True:
            motor_e.on(35)
            motor_d.on(-35)
            
            # Se algum dos sensores encontrar a linha preta (< 20) novamente, sai da curva
            if ir_e.reflected_light_intensity < 20 or ir_d.reflected_light_intensity < 20:
                break 
                
        # Para os motores rápido para não derrapar
        motor_e.off()
        motor_d.off()

    # Curva de 90 graus para a ESQUERDA (Sensor esquerdo viu preto, direito viu branco)
    elif e < 20 and d >= 20:
        while True:
            motor_e.on(-35)
            motor_d.on(35)
            
            if ir_e.reflected_light_intensity < 20 or ir_d.reflected_light_intensity < 20:
                break 
                
        motor_e.off()
        motor_d.off()

    # --- LÓGICA SEGUIDOR DE LINHA (Controle PD) ---
    else:
        # Inverte os valores para que o preto (0-20) seja o maior valor no cálculo
        e_norm = 100 - e
        d_norm = 100 - d

        linha = e_norm + d_norm

        if linha > 0:
            # Calcula o erro atual
            posi = (-1 * e_norm + d_norm) / linha
            erro = posi
            
            # Calcula a derivada (Erro atual - Erro anterior)
            derivada = erro - erro_anterior
            
            # Equação PD final
            correcao = (erro * kp) + (derivada * kd)
            
            # Atualiza o erro anterior para o próximo ciclo do while
            erro_anterior = erro

            # Controle de velocidade baseado na severidade do erro
            if abs(erro) > 0.6:
                vel_atual = 6
            else:
                vel_atual = vel

            # Aplica a correção na velocidade dos motores
            mov_e = vel_atual + correcao
            mov_d = vel_atual - correcao

            # Limita a potência entre -100 e 100 para evitar erros no EV3
            mov_e = max(-100, min(100, mov_e))
            mov_d = max(-100, min(100, mov_d))

            motor_e.on(mov_e)
            motor_d.on(mov_d)

    # Delay mínimo para não sobrecarregar o processador do bloco EV3
    sleep(0.01)