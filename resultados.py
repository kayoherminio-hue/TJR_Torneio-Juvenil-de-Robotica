#!/usr/bin/env python3
"""
analisar_log.py - analisa o log.csv do robô seguidor de linha.

O log tem as colunas: ms, e, d, ramo
    ramo 0 = PID, 1 = branco nos dois sensores, 2 = curva de 90 à direita, 3 = curva de 90 à esquerda

Uso (no computador, não no robô):
    pip install pandas matplotlib          (só na primeira vez)

    python analisar_log.py                          usa o log*.csv mais recente da pasta
    python analisar_log.py log.csv                  analisa um arquivo
    python analisar_log.py antes.csv depois.csv     analisa os dois e compara
    python analisar_log.py log.csv --curvas 16      número de curvas de 90 da pista (padrão 16)

No Windows também dá para arrastar o arquivo .csv em cima do .py.

Gera a pasta relatorio_<nome>/ com relatorio.html (abre sozinho), resumo.csv e os gráficos em PNG.
"""

import argparse
import base64
import glob
import html
import io
import os
import sys
import webbrowser

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

PERIODO_TICKS = 1 << 30  # o contador ticks_ms do MicroPython dá a volta nesse valor


# ---------------------------------------------------------------- leitura ----

def carregar(caminho):
    df = pd.read_csv(caminho)
    df.columns = [str(c).strip().lower() for c in df.columns]
    if not {"ms", "e", "d", "ramo"}.issubset(df.columns):
        df = pd.read_csv(caminho, header=None, names=["ms", "e", "d", "ramo"])
    for c in ["ms", "e", "d", "ramo"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["ms", "e", "d", "ramo"]).reset_index(drop=True)
    df["ramo"] = df["ramo"].astype(int)

    # tempo em segundos desde o primeiro registro (corrige a volta do contador)
    dif = df["ms"].diff().fillna(0)
    dif = dif.where(dif >= 0, dif + PERIODO_TICKS)
    df["t"] = dif.cumsum() / 1000.0

    # mesmo cálculo do erro do robô: (-e_calc + d_calc) / (e_calc + d_calc)
    e_calc = 100 - df["e"]
    d_calc = 100 - df["d"]
    soma = (e_calc + d_calc).replace(0, np.nan)
    df["erro"] = (-e_calc + d_calc) / soma
    return df


def episodios(df, ramo):
    """Sequências de linhas seguidas com o mesmo ramo."""
    colunas = ["inicio", "duracao", "linhas", "e_medio", "d_medio"]
    mascara = (df["ramo"] == ramo).values
    n = len(df)
    saida = []
    i = 0
    while i < n:
        if mascara[i]:
            j = i
            while j + 1 < n and mascara[j + 1]:
                j += 1
            ini = df["t"].iloc[i]
            fim = df["t"].iloc[j + 1] if j + 1 < n else df["t"].iloc[j]
            saida.append({
                "inicio": ini,
                "duracao": fim - ini,
                "linhas": j - i + 1,
                "e_medio": df["e"].iloc[i:j + 1].mean(),
                "d_medio": df["d"].iloc[i:j + 1].mean(),
            })
            i = j + 1
        else:
            i += 1
    return pd.DataFrame(saida, columns=colunas)


# ---------------------------------------------------------------- análise ----

def analisar(df, passo, curvas_esperadas, tam_buffer):
    r = {}
    alertas = []
    pid = df[df["ramo"] == 0]

    r["Registros"] = len(df)
    r["Duração coberta (s)"] = round(df["t"].iloc[-1], 1) if len(df) else 0

    c_dir = int((df["ramo"] == 2).sum())
    c_esq = int((df["ramo"] == 3).sum())
    r["Curvas de 90° detectadas"] = c_dir + c_esq
    r["   à direita"] = c_dir
    r["   à esquerda"] = c_esq

    br = episodios(df, 1)
    r["Episódios de branco"] = len(br)
    r["Maior episódio de branco (s)"] = round(br["duracao"].max(), 2) if len(br) else 0
    r["Tempo total em branco (s)"] = round(br["duracao"].sum(), 2) if len(br) else 0

    for nome, rotulo in (("e", "esquerdo"), ("d", "direito")):
        s = pid[nome]
        if len(s):
            r[f"Sensor {rotulo} no PID: mín / mediana / máx"] = f"{s.min():.0f} / {s.median():.0f} / {s.max():.0f}"
            r[f"Sensor {rotulo} no PID: p5 / p95"] = f"{s.quantile(0.05):.0f} / {s.quantile(0.95):.0f}"
        else:
            r[f"Sensor {rotulo} no PID: mín / mediana / máx"] = "-"
            r[f"Sensor {rotulo} no PID: p5 / p95"] = "-"

    erro = pid["erro"].dropna()
    if len(erro):
        r["Erro: maior |erro|"] = round(erro.abs().max(), 3)
        r["Erro: p95 de |erro|"] = round(erro.abs().quantile(0.95), 3)
        r["Erro: média (viés)"] = round(erro.mean(), 3)
        r["Voltas PID com |erro| > 0.4 (%)"] = round(100 * (erro.abs() > 0.4).mean(), 1)
    else:
        r["Erro: maior |erro|"] = "-"
        r["Erro: p95 de |erro|"] = "-"
        r["Erro: média (viés)"] = "-"
        r["Voltas PID com |erro| > 0.4 (%)"] = "-"

    # voltas por segundo (assume um registro a cada `passo` voltas entre linhas PID seguidas)
    idx = pid.index.to_series()
    seguidas = idx.diff() == 1
    dt = pid["t"].diff()[seguidas]
    dt = dt[dt > 0]
    if len(dt):
        r["Voltas por segundo (estimado)"] = round(passo / dt.median(), 1)
    else:
        r["Voltas por segundo (estimado)"] = "-"

    # ----- alertas -----
    if len(df) >= tam_buffer:
        alertas.append(f"O log está cheio ({len(df)} registros): o início da corrida pode ter sido sobrescrito. "
                       f"O que você vê são os últimos {r['Duração coberta (s)']} s.")

    nunca_branco = ((df["e"] > 50) & (df["d"] > 50)).sum() == 0
    if nunca_branco and len(pid):
        alertas.append(f"Os dois sensores nunca passaram de 50 ao mesmo tempo (p95: e={pid['e'].quantile(0.95):.0f}, "
                       f"d={pid['d'].quantile(0.95):.0f}). O teste 'e > 50 and d > 50' do código nunca dispara "
                       "nessa pista, então a busca por linha perdida não roda.")

    if len(erro) and erro.abs().max() < 0.4:
        alertas.append(f"O maior |erro| foi {erro.abs().max():.2f}, abaixo de 0.4. A redução de velocidade "
                       "'abs(erro) > 0.4' nunca acontece nessa pista.")

    if len(erro) and abs(erro.mean()) > 0.03:
        lado = "direita" if erro.mean() > 0 else "esquerda"
        alertas.append(f"O erro médio é {erro.mean():+.3f}: as leituras sugerem a linha sempre um pouco à {lado}. "
                       "Pode ser diferença entre os sensores (confira o k_d) ou desvio do robô.")

    if curvas_esperadas:
        total = c_dir + c_esq
        if total != curvas_esperadas:
            alertas.append(f"Foram detectadas {total} curvas de 90°, e a pista tem {curvas_esperadas}. "
                           "Se você não rodou a pista inteira (ou o log encheu), ignore. Senão, pode ter faltado "
                           "uma detecção ou ter havido uma falsa.")

    if len(br) and br["duracao"].max() > 1.0:
        alertas.append(f"Houve um episódio de branco de {br['duracao'].max():.1f} s. Se não era um gap desse tamanho, "
                       "o robô provavelmente estava perdido.")

    # curvas de 90 seguidas de branco
    seguidas_branco = 0
    for i in df.index[df["ramo"].isin([2, 3])]:
        if i + 1 < len(df) and df["ramo"].iloc[i + 1] == 1:
            seguidas_branco += 1
    r["Curvas de 90° seguidas de branco"] = seguidas_branco
    if seguidas_branco:
        alertas.append(f"{seguidas_branco} curva(s) de 90° terminaram em branco logo depois. Pode ser o gap perto da "
                       "curva ou o robô terminando a curva torto.")

    if len(df) and df["ramo"].iloc[-1] == 1:
        alertas.append("O log termina em branco: o robô provavelmente estava perdido quando foi pausado.")

    return r, alertas, br


# --------------------------------------------------------------- gráficos ----

def para_base64(fig, caminho_png):
    fig.savefig(caminho_png, format="png", dpi=110, bbox_inches="tight")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def grafico_tempo(df, titulo):
    br = episodios(df, 1)
    fig, ax = plt.subplots(3, 1, sharex=True, figsize=(11, 7.5), gridspec_kw={"height_ratios": [3, 2, 1]})

    ax[0].plot(df["t"], df["e"], label="e (esquerdo)", lw=1.2)
    ax[0].plot(df["t"], df["d"], label="d (direito)", lw=1.2)
    ax[0].axhline(20, color="gray", ls="--", lw=0.8)
    ax[0].axhline(50, color="gray", ls=":", lw=0.8)
    ax[0].set_ylabel("leitura do sensor")
    ax[0].set_title(titulo)

    for _, b in br.iterrows():
        for a in ax:
            a.axvspan(b["inicio"], b["inicio"] + max(b["duracao"], 0.03), color="red", alpha=0.15)
    for t in df.loc[df["ramo"] == 2, "t"]:
        ax[0].axvline(t, color="tab:green", alpha=0.7, lw=1)
    for t in df.loc[df["ramo"] == 3, "t"]:
        ax[0].axvline(t, color="tab:purple", alpha=0.7, lw=1)

    legenda = [
        Line2D([0], [0], color="tab:blue", lw=1.5, label="e (esquerdo)"),
        Line2D([0], [0], color="tab:orange", lw=1.5, label="d (direito)"),
        Line2D([0], [0], color="tab:green", lw=1.5, label="curva 90° à direita"),
        Line2D([0], [0], color="tab:purple", lw=1.5, label="curva 90° à esquerda"),
        matplotlib.patches.Patch(color="red", alpha=0.25, label="branco nos dois"),
    ]
    ax[0].legend(handles=legenda, loc="upper right", fontsize=8, ncol=3)

    pid = df[df["ramo"] == 0]
    ax[1].plot(pid["t"], pid["erro"], color="tab:red", lw=1)
    ax[1].axhline(0, color="gray", lw=0.8)
    ax[1].axhline(0.4, color="gray", ls="--", lw=0.8)
    ax[1].axhline(-0.4, color="gray", ls="--", lw=0.8)
    ax[1].set_ylabel("erro do PID")

    ax[2].step(df["t"], df["ramo"], where="post", color="black", lw=1)
    ax[2].set_yticks([0, 1, 2, 3])
    ax[2].set_yticklabels(["PID", "branco", "90 dir", "90 esq"], fontsize=8)
    ax[2].set_xlabel("segundos")
    fig.tight_layout()
    return fig


def grafico_distribuicao(df):
    pid = df[df["ramo"] == 0]
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.5))
    if len(pid):
        ax[0].hist(pid["e"], bins=30, alpha=0.6, label="e")
        ax[0].hist(pid["d"], bins=30, alpha=0.6, label="d")
        ax[0].legend()
        ax[1].hist(pid["erro"].dropna(), bins=40, color="tab:red", alpha=0.7)
    ax[0].set_title("Leituras dos sensores (PID)")
    ax[0].set_xlabel("valor")
    ax[1].set_title("Erro do PID")
    ax[1].set_xlabel("erro")
    fig.tight_layout()
    return fig


# ------------------------------------------------------------------- HTML ----

CSS = """
body{font-family:Segoe UI,Arial,sans-serif;margin:24px auto;max-width:1100px;color:#222}
h1{font-size:24px}h2{font-size:19px;margin-top:34px;border-bottom:2px solid #ddd;padding-bottom:4px}
h3{font-size:16px;margin-top:24px}
table{border-collapse:collapse;margin:8px 0;font-size:14px}
td,th{border:1px solid #ccc;padding:4px 10px;text-align:left}th{background:#f0f0f0}
.alerta{background:#fff3cd;border-left:4px solid #e0a800;padding:6px 12px;margin:6px 0}
.ok{background:#e6f4ea;border-left:4px solid #34a853;padding:6px 12px;margin:6px 0}
img{max-width:100%}
"""


def tabela_html(df, **kw):
    return df.to_html(index=False, border=0, justify="left", **kw)


def secao_arquivo(caminho, df, resumo, alertas, br, janela, pasta):
    nome = os.path.basename(caminho)
    base = os.path.splitext(nome)[0]
    h = [f"<h2>{html.escape(nome)}</h2>"]

    if alertas:
        h.append("<h3>O que chamou atenção</h3>")
        for a in alertas:
            h.append(f'<div class="alerta">{html.escape(a)}</div>')
    else:
        h.append('<div class="ok">Nenhum alerta automático para esse log.</div>')

    h.append("<h3>Resumo</h3>")
    h.append(tabela_html(pd.DataFrame({"Medida": list(resumo.keys()), "Valor": [str(v) for v in resumo.values()]})))

    img = para_base64(grafico_tempo(df, f"{nome}: corrida inteira"), os.path.join(pasta, f"{base}_geral.png"))
    h.append("<h3>Corrida inteira</h3>")
    h.append(f'<img src="data:image/png;base64,{img}">')

    if len(df):
        fim = df[df["t"] >= df["t"].max() - janela].reset_index(drop=True)
        img2 = para_base64(grafico_tempo(fim, f"{nome}: últimos {janela:.0f} s (onde ele pode ter se perdido)"),
                           os.path.join(pasta, f"{base}_final.png"))
        h.append(f"<h3>Últimos {janela:.0f} segundos</h3>")
        h.append(f'<img src="data:image/png;base64,{img2}">')

    img3 = para_base64(grafico_distribuicao(df), os.path.join(pasta, f"{base}_distribuicao.png"))
    h.append("<h3>Distribuição dos valores</h3>")
    h.append(f'<img src="data:image/png;base64,{img3}">')

    if len(br):
        t = br.copy()
        t.columns = ["início (s)", "duração (s)", "registros", "e médio", "d médio"]
        h.append("<h3>Episódios de branco</h3>")
        h.append(tabela_html(t.round(2)))

    curvas = df[df["ramo"].isin([2, 3])].copy()
    if len(curvas):
        curvas["lado"] = curvas["ramo"].map({2: "direita", 3: "esquerda"})
        curvas["seguida de branco"] = ["sim" if (i + 1 < len(df) and df["ramo"].iloc[i + 1] == 1) else "não"
                                       for i in curvas.index]
        t = curvas[["t", "lado", "e", "d", "seguida de branco"]]
        t.columns = ["tempo (s)", "lado", "e", "d", "seguida de branco"]
        h.append("<h3>Curvas de 90° detectadas</h3>")
        h.append(tabela_html(t.round(2)))

    ultimas = df.tail(25)[["t", "e", "d", "ramo", "erro"]].copy()
    ultimas["ramo"] = ultimas["ramo"].map({0: "PID", 1: "branco", 2: "90 dir", 3: "90 esq"})
    ultimas.columns = ["tempo (s)", "e", "d", "ramo", "erro"]
    h.append("<h3>Últimas 25 linhas do log</h3>")
    h.append(tabela_html(ultimas.round(3)))
    return "\n".join(h)


# ------------------------------------------------------------------- main ----

def main():
    ap = argparse.ArgumentParser(description="Analisa o log.csv do robô e gera um relatório HTML.")
    ap.add_argument("arquivos", nargs="*", help="um ou mais arquivos .csv (se mais de um, compara)")
    ap.add_argument("--curvas", type=int, default=16, help="curvas de 90 da pista (0 = não conferir)")
    ap.add_argument("--passo", type=int, default=4, help="o robô registra 1 a cada N voltas (padrão 4)")
    ap.add_argument("--buffer", type=int, default=600, help="tamanho do buffer do log (padrão 600)")
    ap.add_argument("--janela", type=float, default=8.0, help="segundos finais no zoom (padrão 8)")
    ap.add_argument("--nao-abrir", action="store_true", help="não abrir o relatório no navegador")
    args = ap.parse_args()

    arquivos = args.arquivos
    if not arquivos:
        achados = sorted(glob.glob("log*.csv"), key=os.path.getmtime, reverse=True)
        if not achados:
            print("Não achei nenhum log*.csv nessa pasta. Passe o arquivo: python analisar_log.py log.csv")
            sys.exit(1)
        arquivos = [achados[0]]
        print(f"Usando o mais recente: {arquivos[0]}")

    primeiro = os.path.splitext(os.path.basename(arquivos[0]))[0]
    pasta = os.path.join(os.path.dirname(os.path.abspath(arquivos[0])), f"relatorio_{primeiro}")
    os.makedirs(pasta, exist_ok=True)

    secoes = []
    resumos = {}
    for caminho in arquivos:
        try:
            df = carregar(caminho)
        except Exception as erro:
            print(f"Não consegui ler {caminho}: {erro}")
            continue
        if len(df) == 0:
            print(f"{caminho} está vazio ou sem linhas válidas.")
            continue
        resumo, alertas, br = analisar(df, args.passo, args.curvas, args.buffer)
        resumos[os.path.basename(caminho)] = resumo
        secoes.append(secao_arquivo(caminho, df, resumo, alertas, br, args.janela, pasta))

    if not secoes:
        print("Nada para analisar.")
        sys.exit(1)

    tabela = pd.DataFrame({nome: {k: str(v) for k, v in r.items()} for nome, r in resumos.items()})
    tabela.index.name = "Medida"
    tabela.to_csv(os.path.join(pasta, "resumo.csv"), encoding="utf-8-sig")

    corpo = ["<h1>Relatório do log do robô</h1>"]
    if len(resumos) > 1:
        corpo.append("<h2>Comparação</h2>")
        corpo.append(tabela.reset_index().to_html(index=False, border=0, justify="left"))
    corpo.extend(secoes)

    pagina = (f"<!doctype html><html><head><meta charset='utf-8'><title>Relatório do log</title>"
              f"<style>{CSS}</style></head><body>{''.join(corpo)}</body></html>")
    saida = os.path.join(pasta, "relatorio.html")
    with open(saida, "w", encoding="utf-8") as f:
        f.write(pagina)

    print(f"Relatório gerado em: {saida}")
    if not args.nao_abrir:
        webbrowser.open("file://" + os.path.abspath(saida))


if __name__ == "__main__":
    main()