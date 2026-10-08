# Microbenchmark de operações em memória: Windows 11 x Debian 13

Compara o tempo de alocação, escrita, leitura e liberação de blocos de memória em duas máquinas virtuais com o mesmo hardware virtual, uma com Windows 11 e outra com Debian 13.

## Estrutura

```
.
├── benchmark.py          coleta os tempos e grava um CSV por sistema
├── plotar.py             lê os dois CSVs e gera os gráficos
├── requirements.txt      dependências do plotar.py
├── resultados/
│   ├── resultados_windows.csv
│   └── resultados_linux.csv
└── graficos/             PNGs gerados pelo plotar.py
```

## Requisitos

- Duas VMs com a mesma configuração de hardware virtual (vCPUs, RAM, disco) e o mesmo hipervisor.
- Windows 11 em uma e Debian 13 na outra.
- Pelo menos 4 GB de RAM em cada VM (o maior bloco tem 1.000 MB).
- A mesma versão do Python nas duas VMs. No experimento original as versões foram diferentes (3.14.8 no Windows e 3.13.5 no Debian), o que é uma limitação. Para reproduzir com rigor, instale a mesma versão nos dois sistemas, por exemplo Python 3.13.
- `benchmark.py` usa só a biblioteca padrão. `pandas` e `matplotlib` são necessários apenas para `plotar.py`.

## 1. Preparar o ambiente

### Debian 13

```bash
sudo apt install python3 python3-venv
python3 -m venv .venv
source .venv/bin/activate
python --version
```

### Windows 11 (PowerShell)

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python --version
```

Se o PowerShell bloquear a ativação:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

Anote a saída de `python --version` nas duas VMs e confirme que são iguais.

## 2. Executar o benchmark em cada VM

Com o ambiente ativo, na pasta do projeto:

```
python benchmark.py
```

Os valores padrão são os do experimento: blocos de 100 a 1.000 MB em passos de 100 MB e 100 repetições por tamanho. O script gera:

- `resultados/resultados_windows.csv` no Windows;
- `resultados/resultados_linux.csv` no Debian.

O arquivo é nomeado pelo sistema detectado, então não é preciso informar o SO. A execução leva de dezenas de minutos a cerca de 1 hora por VM.

### Parâmetros

| Parâmetro | Padrão | Descrição |
|---|---|---|
| `--min-mb` | 100 | menor tamanho de bloco (MB) |
| `--max-mb` | 1000 | maior tamanho de bloco (MB) |
| `--passo-mb` | 100 | intervalo entre tamanhos (MB) |
| `--repeticoes` | 100 | repetições por tamanho |
| `--aquecimento` | 2 | ciclos descartados antes da coleta |
| `--saida` | `resultados` | pasta de saída dos CSVs |

Nesta documentação, 1 MB corresponde a 1024² bytes.

### Boas práticas durante a coleta

- Feche outros programas e evite atualizações ou antivírus em varredura durante a execução.
- Execute as duas VMs sob condições semelhantes (mesmo hospedeiro, mesma carga, mesmo plano de energia).
- Não mexa na VM enquanto o teste roda.
- Não use as duas VMs ao mesmo tempo, para que uma não disute recursos com a outra.

## 3. Reunir os CSVs

Copie os dois arquivos para a mesma pasta `resultados/` na máquina onde os gráficos serão gerados:

```
resultados/resultados_windows.csv
resultados/resultados_linux.csv
```

### Formato dos CSVs

| Coluna | Descrição |
|---|---|
| `sistema` | `Windows` ou `Linux` |
| `versao_so` | versão detalhada do sistema |
| `python` | versão do Python |
| `tamanho_mb` | tamanho do bloco em MB |
| `repeticao` | número da repetição (1 a 100) |
| `operacao` | `alocacao`, `escrita`, `leitura` ou `liberacao` |
| `tempo_ms` | tempo da operação em milissegundos |
| `taxa_mb_s` | tamanho do bloco dividido pelo tempo, em MB/s |

Cada arquivo deve ter 4.000 linhas (10 tamanhos × 100 repetições × 4 operações).

## 4. Gerar os gráficos

```
pip install -r requirements.txt
python plotar.py
```

Para outras pastas, use `--entrada` e `--saida`. Os gráficos ficam em `graficos/`:

| Arquivo | Conteúdo |
|---|---|
| `tempo_vs_tamanho.png` | tempo médio por tamanho de bloco, com intervalo de confiança de 95% |
| `vazao.png` | vazão mediana por tamanho de bloco |
| `razao_windows_linux.png` | razão entre as medianas dos tempos (acima de 1, o Linux é mais rápido) |
| `boxplot_maior_bloco.png` | distribuição dos tempos no maior bloco |

## O que o benchmark mede

- **Alocação:** cria o bloco com `bytearray` e acessa todas as páginas, para que a escrita não inclua o custo da primeira ocupação.
- **Escrita:** preenche o bloco inteiro em segmentos de 1 MB.
- **Leitura:** copia o bloco inteiro, em segmentos de 1 MB, para um buffer pequeno.
- **Liberação:** mede o tempo de devolver o bloco ao sistema.

Cada repetição executa o ciclo alocação, escrita, leitura e liberação. O relógio usado é `time.perf_counter_ns`, o coletor de lixo fica desligado durante cada medição e dois ciclos de aquecimento são descartados.

## Observações para interpretar

- A vazão da liberação (`taxa_mb_s`) não representa uma taxa real de memória, porque o bloco só é devolvido ao sistema. Compare a liberação pelo tempo em milissegundos.
- O código roda em Python, então parte do tempo reflete o interpretador e o alocador da plataforma, e não só o sistema operacional.
- Os resultados valem para máquinas virtuais, para blocos de 100 a 1.000 MB e para o hardware virtual testado.
- Registre a configuração das VMs (vCPUs, RAM, disco, hipervisor), pois os CSVs guardam apenas o sistema e a versão do Python.
