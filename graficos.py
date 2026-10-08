import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

OPERACOES = ["alocacao", "escrita", "leitura", "liberacao"]
SISTEMAS = ["Windows", "Linux"]
CORES = {"Windows": "#0078D4", "Linux": "#E95420"}
COLUNAS = ["sistema", "tamanho_mb", "repeticao", "operacao", "tempo_ms", "taxa_mb_s"]


def carregar(entrada):
    partes = []
    for s in SISTEMAS:
        caminho = entrada / f"resultados_{s.lower()}.csv"
        df = pd.read_csv(caminho)
        faltantes = set(COLUNAS) - set(df.columns)
        if faltantes:
            raise ValueError(f"{caminho.name}: colunas ausentes {sorted(faltantes)}")
        partes.append(df[COLUNAS].dropna())
    return pd.concat(partes, ignore_index=True)


def estatisticas(df):
    g = df.groupby(["operacao", "sistema", "tamanho_mb"])
    r = g.agg(media=("tempo_ms", "mean"), mediana=("tempo_ms", "median"),
              sem=("tempo_ms", "sem"), taxa=("taxa_mb_s", "median")).reset_index()
    r["ic95"] = 1.96 * r["sem"]
    return r


def grade(titulo, arquivo, desenhar, saida):
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for ax, op in zip(axes.ravel(), OPERACOES):
        desenhar(ax, op)
        ax.set_title(op)
        ax.set_xlabel("tamanho do bloco (MB)")
        ax.grid(alpha=0.3)
    fig.suptitle(titulo)
    fig.tight_layout()
    fig.savefig(saida / arquivo, dpi=150)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", default="resultados")
    ap.add_argument("--saida", default="graficos")
    args = ap.parse_args()

    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)
    df = carregar(Path(args.entrada))
    est = estatisticas(df)

    def tempo(ax, op):
        for s in SISTEMAS:
            sub = est[(est.operacao == op) & (est.sistema == s)].sort_values("tamanho_mb")
            ax.errorbar(sub["tamanho_mb"], sub["media"], yerr=sub["ic95"],
                        marker="o", capsize=3, label=s, color=CORES[s])
        ax.set_ylabel("tempo médio (ms)")
        ax.legend()

    def vazao(ax, op):
        for s in SISTEMAS:
            sub = est[(est.operacao == op) & (est.sistema == s)].sort_values("tamanho_mb")
            ax.plot(sub["tamanho_mb"], sub["taxa"], marker="o", label=s, color=CORES[s])
        ax.set_ylabel("vazão mediana (MB/s)")
        ax.legend()

    def razao(ax, op):
        piv = est[est.operacao == op].pivot(index="tamanho_mb", columns="sistema", values="mediana")
        r = piv["Windows"] / piv["Linux"]
        cores = [CORES["Linux"] if v > 1 else CORES["Windows"] for v in r]
        ax.bar(r.index, r.values, width=70, color=cores)
        ax.axhline(1, color="black", linestyle="--")
        ax.set_ylabel("tempo Windows / Linux")

    def caixas(ax, op):
        t = df.tamanho_mb.max()
        dados = [df[(df.operacao == op) & (df.sistema == s) & (df.tamanho_mb == t)]["tempo_ms"]
                 for s in SISTEMAS]
        bp = ax.boxplot(dados, patch_artist=True)
        for patch, s in zip(bp["boxes"], SISTEMAS):
            patch.set_facecolor(CORES[s])
            patch.set_alpha(0.6)
        ax.set_xticks([1, 2])
        ax.set_xticklabels(SISTEMAS)
        ax.set_ylabel(f"tempo (ms), bloco de {t} MB")

    grade("Tempo médio por tamanho de bloco (IC 95%)", "tempo_vs_tamanho.png", tempo, saida)
    grade("Vazão mediana por tamanho de bloco", "vazao.png", vazao, saida)
    grade("Razão das medianas (>1: Linux mais rápido; <1: Windows mais rápido)",
          "razao_windows_linux.png", razao, saida)
    grade("Distribuição dos tempos no maior bloco", "boxplot_maior_bloco.png", caixas, saida)

    print(f"Gráficos salvos em {saida}")


if __name__ == "__main__":
    main()
