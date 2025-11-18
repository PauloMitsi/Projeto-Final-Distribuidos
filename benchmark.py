"""
Script de Benchmark (benchmark.py)
----------------------------------
Automatiza a execução dos 3 scripts (sequencial, paralelo, distribuído)
com diferentes parâmetros e salva os resultados em um CSV.

NOTA: Este script pressupõe que o 'master.py' e 'worker.py'
conseguem rodar na mesma máquina (localhost).
"""

import subprocess
import re
import csv
import time

# --- PARÂMETROS DE TESTE ---
# (Ajuste conforme necessário. Cuidado, testes grandes demoram!)
ITERACOES = 100
TAMANHOS_MATRIZ = [50, 100, 200] # Ex: 50, 100, 200
CONTAGEM_WORKERS = [2, 4, 8]      # Ex: 2, 4, 8, 16
# ---------------------------

# Regex para capturar o tempo de execução (ex: "Tempo total: 12.3456 s")
TIME_REGEX = re.compile(r"Tempo total:\s*([\d\.]+)\s*s")

def extrair_tempo(output: str) -> float:
    """Extrai o tempo da saída do console usando regex."""
    match = TIME_REGEX.search(output)
    if match:
        return float(match.group(1))
    return -1.0

def rodar_teste(comando: list) -> float:
    """Roda um comando e retorna o tempo de execução."""
    try:
        print(f"  Rodando: {' '.join(comando)}")
        # Adicionamos text=True, capture_output=True, check=True
        # timeout=600 (10 minutos) para evitar que testes travem
        result = subprocess.run(
            comando, 
            capture_output=True, 
            text=True, 
            check=True, 
            timeout=600
        )
        tempo = extrair_tempo(result.stdout)
        print(f"  Tempo: {tempo:.4f} s")
        return tempo
    except subprocess.TimeoutExpired:
        print("  ERRO: Teste demorou mais de 10 minutos (Timeout).")
        return -999.0
    except subprocess.CalledProcessError as e:
        print(f"  ERRO: Falha ao executar o script.")
        print(e.stderr)
        return -1.0

def main():
    print("Iniciando script de benchmark...")
    resultados = []

    # Cabeçalho do CSV
    resultados.append([
        "Tipo", 
        "Tamanho_Matriz", 
        "Iteracoes", 
        "Num_Workers_Threads", 
        "Tempo_s"
    ])

    # --- Testes Sequenciais ---
    for n in TAMANHOS_MATRIZ:
        print(f"\nTestando Sequencial (Matriz: {n}x{n})...")
        cmd = ["python", "./sequencial/sequencial_sir.py", str(n), str(ITERACOES)]
        tempo = rodar_teste(cmd)
        resultados.append(["Sequencial", n, ITERACOES, 1, tempo])

    # --- Testes Paralelos ---
    for n in TAMANHOS_MATRIZ:
        for w in CONTAGEM_WORKERS:
            print(f"\nTestando Paralelo (Matriz: {n}x{n}, Threads: {w})...")
            cmd = ["python", "./paralelo/paralelo_sir.py", str(n), str(ITERACOES), str(w)]
            tempo = rodar_teste(cmd)
            resultados.append(["Paralelo", n, ITERACOES, w, tempo])

    # --- Testes Distribuídos ---
    # (Estes são mais complexos de orquestrar)
    for n in TAMANHOS_MATRIZ:
        for w in CONTAGEM_WORKERS:
            print(f"\nTestando Distribuído (Matriz: {n}x{n}, Workers: {w})...")
            
            # Iniciar o Mestre
            cmd_master = ["python", "./distribuido/master.py", str(n), str(ITERACOES), str(w)]
            master_proc = subprocess.Popen(
                cmd_master, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )
            
            # Dar 2 segundos para o mestre iniciar
            time.sleep(2) 
            
            # Iniciar os Workers
            worker_procs = []
            for _ in range(w):
                proc = subprocess.Popen(
                    ["python", "worker.py"],
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE, 
                    text=True
                )
                worker_procs.append(proc)
            
            # Esperar o Mestre terminar (ele controla o tempo)
            try:
                master_stdout, master_stderr = master_proc.communicate(timeout=600)
                tempo = extrair_tempo(master_stdout)
                print(f"  Tempo: {tempo:.4f} s")
                
                if master_proc.returncode != 0:
                    print("  ERRO: Mestre falhou.")
                    print(master_stderr)
                    tempo = -1.0
                
                resultados.append(["Distribuido", n, ITERACOES, w, tempo])

            except subprocess.TimeoutExpired:
                print("  ERRO: Teste distribuído demorou mais de 10 minutos (Timeout).")
                master_proc.kill()
                resultados.append(["Distribuido", n, ITERACOES, w, -999.0])
            
            # Garantir que todos os workers foram mortos
            for proc in worker_procs:
                proc.kill()

    # --- Salvar Resultados ---
    nome_arquivo = "resultados.csv"
    with open(nome_arquivo, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(resultados)
        
    print(f"\nBenchmark concluído! Resultados salvos em '{nome_arquivo}'.")

if __name__ == "__main__":
    main()