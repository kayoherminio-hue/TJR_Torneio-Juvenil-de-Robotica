#!/usr/bin/env python3

from ev3dev2.motor import LargeMotor, OUTPUT_B, OUTPUT_C
from ev3dev2.sensor.lego import ColorSensor, UltrasonicSensor
from ev3dev2.sensor import INPUT_1, INPUT_3, INPUT_2
from time import sleep, time
from moves import desvio

# ---------------- Hardware ----------------
motor_e = LargeMotor(OUTPUT_B)
motor_d = LargeMotor(OUTPUT_C)

ir_e = ColorSensor(INPUT_1)
ir_d = ColorSensor(INPUT_3)

ultrassonico = UltrasonicSensor(INPUT_2)

# ---------------- Parâmetros (ajuste aqui) ----------------
LIMIAR = 20          # abaixo disso = preto. Ideal: ponto médio entre preto e branco do seu piso
VEL = 25             # velocidade base (comece em 20 se estiver instável)
KP = 25              # ganho proporcional (antes era 90)
KD = 15              # ganho derivativo (por ciclo)
VEL_GIRO = 22        # velocidade de giro nas curvas de 90°
TIMEOUT_GIRO = 2.0   # segundos; evita girar para sempre se não achar a linha
DIST_OBSTACULO = 10  # cm
LER_ULTRA_A_CADA = 10  # lê o ultrassônico a cada N ciclos para não atrasar o loop
DEBUG = False        # True imprime os sensores nas curvas (deixa o loop mais lento)


def limitar(valor, minimo=-100, maximo=100):
    return max(minimo, min(maximo, valor))


def girar(sentido, condicao_parada):
    """
    Gira no próprio eixo até condicao_parada() ser verdadeira (ou timeout).
    sentido = +1 gira para a direita, -1 para a esquerda.
    """
    inicio = time()
    motor_e.on(sentido * VEL_GIRO)
    motor_d.on(-sentido * VEL_GIRO)

    while not condicao_parada():
        if time() - inicio > TIMEOUT_GIRO:
            break

    motor_e.off()
    motor_d.off()


erro_anterior = 0
ultimo_erro = 0   # lembra de que lado a linha estava (para recuperar se sair dela)
ciclo = 0

while True:

    # ---- Obstáculo (lido só de vez em quando) ----
    ciclo += 1
    if ciclo % LER_ULTRA_A_CADA == 0:
        if ultrassonico.distance_centimeters_continuous <= DIST_OBSTACULO:
            motor_e.off()
            motor_d.off()
            desvio()
            erro_anterior = 0
            continue

    e = ir_e.reflected_light_intensity
    d = ir_d.reflected_light_intensity

    # ---- Curva de 90°: direita (só o sensor direito vê preto) ----
    if d < LIMIAR and e >= LIMIAR:
        if DEBUG:
            print("90 dir", e, d)
        # gira à direita até o sensor esquerdo também encontrar a linha
        girar(+1, lambda: ir_e.reflected_light_intensity < LIMIAR)
        erro_anterior = 0
        continue

    # ---- Curva de 90°: esquerda (só o sensor esquerdo vê preto) ----
    elif e < LIMIAR and d >= LIMIAR:
        if DEBUG:
            print("90 esq", e, d)
        # gira à esquerda até o sensor direito também encontrar a linha
        girar(-1, lambda: ir_d.reflected_light_intensity < LIMIAR)
        erro_anterior = 0
        continue

    # ---- Perdeu a linha (os dois veem branco) ----
    elif e >= LIMIAR and d >= LIMIAR:
        if DEBUG:
            print("perdido", e, d)
        # gira para o lado em que a linha estava até algum sensor achá-la
        sentido = 1 if ultimo_erro >= 0 else -1
        girar(sentido, lambda: ir_e.reflected_light_intensity < LIMIAR
              or ir_d.reflected_light_intensity < LIMIAR)
        erro_anterior = 0
        continue

    # ---- Seguimento normal com PD ----
    e_escuro = 100 - e
    d_escuro = 100 - d
    linha = e_escuro + d_escuro

    if linha > 0:
        erro = (-e_escuro + d_escuro) / linha   # entre -1 e 1
        derivada = erro - erro_anterior
        correcao = erro * KP + derivada * KD

        erro_anterior = erro
        ultimo_erro = erro

        # reduz a velocidade de forma contínua conforme o erro cresce
        vel_atual = VEL * (1 - 0.5 * abs(erro))

        mov_e = limitar(vel_atual + correcao)
        mov_d = limitar(vel_atual - correcao)

        motor_e.on(mov_e)
        motor_d.on(mov_d)

    sleep(0.005)