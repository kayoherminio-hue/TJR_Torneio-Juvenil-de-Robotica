import time as t

log = [0] * 3600

if hasattr(t, "ticks_ms"):
    _ms = t.ticks_ms
else:
    def _ms():
        return int(t.time() * 1000)

arquivo = "/home/robot/TJR_2026/log.csv"
dados = [0] * 2400
_tam = len(dados)
k_atual = 0
total = 0
_motores = ()

def registrar(e, d, ramo):
    global k_atual, total
    dados[k_atual] = _ms()
    dados[k_atual + 1] = int(e)
    dados[k_atual + 2] = int(d)
    dados[k_atual + 3] = ramo
    k_atual += 4
    if k_atual >= _tam:
        k_atual = 0
    total += 1


def salvar():
    f = open(arquivo, "w")
    f.write("ms,e,d,ramo\n")
    n = min(total, _tam // 4)
    ini = k_atual if total > _tam // 4 else 0
    for j in range(n):
        k = (ini + j * 4) % _tam
        f.write(str(dados[k]) + "," + str(dados[k + 1]) + "," + str(dados[k + 2]) + "," + str(dados[k + 3]) + "\n")
    f.close()


def ao_sinal(sig, frame):
    for m in _motores:
        m.off()
    salvar()
    raise SystemExit


def armar_sinal(*motores):
    global _motores
    _motores = motores
    try:
        import signal
        signal.signal(signal.SIGTERM, ao_sinal)
        return True
    except ImportError:
        return False