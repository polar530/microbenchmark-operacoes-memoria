import argparse
import csv
import gc
import platform
import time
from pathlib import Path

MB = 1024 * 1024
PAGINA = 4096
CHUNK = MB
OPERACOES = ["alocacao", "escrita", "leitura", "liberacao"]


def cronometrar(func, *args):
    inicio = time.perf_counter_ns()
    resultado = func(*args)
    fim = time.perf_counter_ns()
    return resultado, (fim - inicio) / 1e6


def alocar(n):
    buf = bytearray(n)
    buf[::PAGINA] = b"\x01" * len(range(0, n, PAGINA))
    return buf


def escrever(buf, padrao):
    mv = memoryview(buf)
    for i in range(0, len(buf), CHUNK):
        mv[i:i + CHUNK] = padrao
    mv.release()


def ler(buf, destino):
    mv = memoryview(buf)
    for i in range(0, len(buf), CHUNK):
        destino[:] = mv[i:i + CHUNK]
    mv.release()


def ciclo(n, padrao, destino):
    gc.collect()
    gc.disable()
    try:
        buf, t_alocacao = cronometrar(alocar, n)
        _, t_escrita = cronometrar(escrever, buf, padrao)
        _, t_leitura = cronometrar(ler, buf, destino)
        ref = [buf]
        del buf
        _, t_liberacao = cronometrar(ref.clear)
    finally:
        gc.enable()
    return {"alocacao": t_alocacao, "escrita": t_escrita,
            "leitura": t_leitura, "liberacao": t_liberacao}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-mb", type=int, default=100)
    ap.add_argument("--max-mb", type=int, default=1000)
    ap.add_argument("--passo-mb", type=int, default=100)
    ap.add_argument("--repeticoes", type=int, default=100)
    ap.add_argument("--aquecimento", type=int, default=2)
    ap.add_argument("--saida", default="resultados")
    args = ap.parse_args()

    sistema = platform.system()
    versao = platform.platform()
    python = platform.python_version()
    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)
    arquivo = saida / f"resultados_{sistema.lower()}.csv"

    padrao = bytes(range(256)) * (CHUNK // 256)
    destino = memoryview(bytearray(CHUNK))
    tamanhos = range(args.min_mb, args.max_mb + 1, args.passo_mb)

    for _ in range(args.aquecimento):
        ciclo(args.min_mb * MB, padrao, destino)

    with open(arquivo, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sistema", "versao_so", "python", "tamanho_mb", "repeticao",
                    "operacao", "tempo_ms", "taxa_mb_s"])
        for tamanho in tamanhos:
            for rep in range(1, args.repeticoes + 1):
                tempos = ciclo(tamanho * MB, padrao, destino)
                for op in OPERACOES:
                    t = tempos[op]
                    w.writerow([sistema, versao, python, tamanho, rep, op,
                                round(t, 6), round(tamanho / (t / 1000), 6)])
            f.flush()
            print(f"{tamanho} MB concluído")

    print(f"CSV salvo em {arquivo}")


if __name__ == "__main__":
    main()
