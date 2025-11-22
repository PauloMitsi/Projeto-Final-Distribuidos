"""
Script de Geração de Gráficos
--------------------------------------------------
Lê o 'resultados.csv' (gerado pelo benchmark.py) e cria
os gráficos de análise de desempenho exigidos.

"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sys

def plotar_graficos(arquivo_csv="resultados.csv"):
    
    # --- Configuração de Estilo ---
    sns.set_theme(style="whitegrid")
    
    # --- Carregar Dados ---
    try:
        df = pd.read_csv(arquivo_csv)
    except FileNotFoundError:
        print(f"Erro: Arquivo '{arquivo_csv}' não encontrado.")
        print("Execute o 'benchmark.py' primeiro.")
        sys.exit(1)
        
    # Limpar dados ruins (testes que falharam)
    df = df[df["Tempo_s"] > 0]
    if df.empty:
        print("Não há dados válidos para plotar.")
        return

    # --- 1. Gráfico: Escalabilidade do Problema ---
    # Compara Sequencial, Paralelo (4w) e Distribuído (4w)
    # variando o tamanho da matriz.
    print("Gerando Gráfico 1: Escalabilidade do Problema...")
    
    # Pega o N de workers mais baixo (ex: 2 ou 4) para comparação
    worker_comparacao = df[df["Tipo"] != "Sequencial"]["Num_Workers_Threads"].min()
    
    df_escalab = df[
        (df["Tipo"] == "Sequencial") |
        (df["Num_Workers_Threads"] == worker_comparacao)
    ]
    
    plt.figure(figsize=(10, 6))
    sns.lineplot(
        data=df_escalab,
        x="Tamanho_Matriz",
        y="Tempo_s",
        hue="Tipo",
        marker="o"
    )
    plt.title(f"Tempo vs. Tamanho da Matriz (Workers={worker_comparacao})")
    plt.xlabel("Tamanho da Matriz (N)")
    plt.ylabel("Tempo de Execução (s)")
    plt.legend(title="Tipo de Execução")
    plt.tight_layout()
    plt.savefig("grafico_escalabilidade.png")
    print("Salvo em 'grafico_escalabilidade.png'")

    # --- 2. Gráfico: Speedup ---
    # Compara Paralelo e Distribuído contra o Sequencial,
    # variando o número de workers/threads.
    print("Gerando Gráfico 2: Speedup...")
    
    # Isolar tempos sequenciais para cálculo do speedup
    df_seq = df[df["Tipo"] == "Sequencial"][["Tamanho_Matriz", "Tempo_s"]]
    df_seq = df_seq.rename(columns={"Tempo_s": "Tempo_Seq"})
    
    # Pegar o maior tamanho de matriz para o teste de speedup
    # (onde a paralelização tem mais efeito)
    n_speedup = df["Tamanho_Matriz"].max()
    df_speedup = df[
        (df["Tipo"] != "Sequencial") &
        (df["Tamanho_Matriz"] == n_speedup)
    ]
    
    # Juntar o tempo sequencial correspondente
    tempo_seq_n = df_seq[df_seq["Tamanho_Matriz"] == n_speedup]["Tempo_Seq"].values[0]
    
    # Calcular Speedup = Tempo_Sequencial / Tempo_Paralelo
    df_speedup["Speedup"] = tempo_seq_n / df_speedup["Tempo_s"]
    
    # Linha ideal (Speedup = N)
    ideal = pd.DataFrame({
        "Num_Workers_Threads": df_speedup["Num_Workers_Threads"].unique(),
        "Tipo": "Speedup Ideal"
    })
    ideal["Speedup"] = ideal["Num_Workers_Threads"]
    
    # Juntar dados reais e ideal
    df_speedup = pd.concat([df_speedup, ideal])

    plt.figure(figsize=(10, 6))
    sns.lineplot(
        data=df_speedup,
        x="Num_Workers_Threads",
        y="Speedup",
        hue="Tipo",
        marker="o"
    )
    plt.title(f"Speedup vs. Número de Workers/Threads (Matriz={n_speedup}x{n_speedup})")
    plt.xlabel("Número de Workers / Threads")
    plt.ylabel("Speedup (Tempo_Seq / Tempo_Paralelo)")
    plt.legend(title="Tipo de Execução")
    plt.tight_layout()
    plt.savefig("grafico_speedup.png")
    print("Salvo em 'grafico_speedup.png'")

if __name__ == "__main__":
    plotar_graficos()