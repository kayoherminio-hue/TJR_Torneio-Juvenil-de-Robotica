# Robô seguidor de linha EV3 (TJR 2026) Horus IFPB

Robô LEGO EV3 que segue linha, desvia de obstáculos, pega uma lata, solta no ponto de entrega e, em uma segunda modalidade, volta a seguir a linha até ver verde.

**Resultado:** 1º lugar Resgate de Alto Risco (27/10/2026) Etapa Regional.

2º lugar Resgate no Plano (27/10/2026) Etapa Regional.

## O que o robô faz

- **Modalidade normal (botão CIMA):** segue a linha, desvia de obstáculos, pega a lata e, ao ver preto nos dois sensores por 0,4 s, solta o objeto e para.
- **Botão BAIXO:** pausa e continua durante a corrida.

## Hardware

| Peça | Porta |
|---|---|
| Motor grande esquerdo | B |
| Motor grande direito | C |
| Garra (motor médio) | D |
| Sensor de cor esquerdo (luz refletida) | 1 |
| Ultrassônico | 2 |
| Sensor de cor direito (luz refletida) | 3 |
| Sensor IR (proximidade) | 4 |



## Software

- `main.py`: laço principal (seguidor de linha, curvas de 90°, decisões).
- `moves.py`: manobras (`desvio`, `pegar`, `soltar`, `frente`, `tras`, `direita`, `esquerda`, `pick`).
- Linguagem: Python (MicroPython do ev3dev, biblioteca `ev3dev2`). TODO: versão do ev3dev.
- Como rodar: enviar a pasta para o robô (extensão do VS Code para EV3) e executar `main.py`. A primeira linha é `#!/usr/bin/env micropython`.

## Como funciona

1. **Seguidor de linha (PD + I):** o erro vem da diferença entre as leituras dos dois sensores. A correção soma P (`kp`), D (`kd`) e I (`ki`). A velocidade base é `vel`.
2. **Compensação do sensor direito:** o `K_D` (1,2) multiplica a leitura do sensor direito, porque no branco ele lê menos que o esquerdo (30 contra 36 na cerâmica).
3. **Curva de 90°:** um sensor lê preto (`< 7`) e o outro lê branco (`>= 23`). O robô avança 120° de motor, gira até o sensor de fora achar a linha e volta devagar até ele sair dela.
4. **Obstáculo e lata:** distância do ultrassônico `<= 4` cm. Pelo código, se o IR também vê o objeto é obstáculo (`desvio()`), senão é lata (`pegar()`). TODO: confirmar.
5. **Entrega:** preto nos dois sensores por 0,4 s chama `soltar()`, recua até a linha, avança e abre a garra.
6. **Linha perdida:** com os dois sensores acima de 50 ele gira para o lado da última curva.

## Parâmetros atuais

| Parâmetro | Valor | O que faz |
|---|---|---|
| `kp` / `kd` / `ki` | 675 / 875 / 20 | ganhos do controle |
| `vel` | 70 | velocidade base |
| `K_D` | 1,2 | compensa o sensor direito |
| limite de preto (chegada) | 20 | `e` e `d` abaixo = preto |
| curva de 90° | `< 7` e `>= 23` | detecção |
| saída da linha no 90° | 28 | fim do giro de volta |
| avanço do 90° | 120° a 40% | leva o eixo até a curva |

## Antes de cada rodada

- Bateria carregada (a velocidade dos motores muda com a carga).
- Na tela inicial, com os dois sensores no branco, `Esq` e `Dir` devem aparecer quase iguais. Senão, ajustar o `K_D`.
- Lentes dos sensores limpas e cabos presos.

## Lições aprendidas

- Com `kp` menor que algumas centenas o robô quase não corrige: o erro calculado só chega a cerca de ±0,2, porque o branco lê 30 a 36 e não 100.
- Tempo fixo (`sleep`) depende da bateria. Distância por encoder (`on_for_degrees`) é mais repetível.
- Ler `.color` troca o modo do sensor e atrapalha a leitura de luz logo depois.
- Rodar com MicroPython deixou o laço mais rápido e o movimento mais suave.

## Problemas conhecidos e melhorias

- O robo tende a um lado nas retas.
- Falta aperfeiçoar o resgate.
- Entra muito na condição do 90 graus

## Equipe Horus 

Alunos:
- Kayo Herminio Cabral de Lima
- Rafael Adelino
- Ícaro Emanuel
- Vinicius Gomes
Instituição Federal da Paraíba
