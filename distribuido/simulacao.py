"""
Script Lançador de DEMONSTRAÇÃO COMPLETA
------------------------------------------------------------
Este script demonstra TODAS AS TRÊS implementações em sequência
para uso em sua apresentação de vídeo.

Ele usa a flag '/K' do CMD para forçar as novas janelas
a permanecerem abertas, permitindo que você leia os resultados.

VOCÊ DEVE FECHAR CADA JANELA DE TESTE MANUALMENTE PARA CONTINUAR.
"""

import subprocess
import time
import argparse
import os

def launch_in_new_console(command_list: list):
    """
    Inicia um comando em uma nova janela de console (CMD) no Windows
    e MANTÉM A JANELA ABERTA após a execução.
    """
    if os.name != 'nt':
        print("Aviso: Este lançador automático só funciona no Windows.")
        print(f"Por favor, execute manually: {' '.join(command_list)}")
        return None
        
    try:
        # Usa 'python' em vez do caminho completo para evitar
        # problemas com espaços em "Program Files".
        py_command = f'python {" ".join(command_list)}'
        
        # /K = "Execute e mantenha a janela aberta"
        final_command = ['cmd.exe', '/K', py_command]

        proc = subprocess.Popen(
            final_command,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        return proc
        
    except Exception as e:
        print(f"Falha ao iniciar {' '.join(command_list)}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Lançador da Simulação Distribuída SIR.")
    parser.add_argument("tamanho_matriz", type=int, help="Tamanho N da matriz NxN.")
    parser.add_argument("iteracoes", type=int, help="Número de iterações.")
    parser.add_argument("num_workers", type=int, help="Número de workers/threads para os testes paralelo e distribuído.")
    
    args = parser.parse_args()
    
    N = str(args.tamanho_matriz)
    ITERACOES = str(args.iteracoes)
    NUM_WORKERS_STR = str(args.num_workers)
    NUM_WORKERS_INT = args.num_workers

    master_proc = None
    worker_procs = []

    try:
        # --- ETAPA 1: TESTE SEQUENCIAL ---
        seq_command = [".\sequencial\sequencial_sir.py", N, ITERACOES]
        print(f"\n--- INICIANDO TESTE SEQUENCIAL (Matriz {N}x{N}) ---")
        print("Uma nova janela será aberta.")
        print(">>> QUANDO O TESTE TERMINAR, FECHE A JANELA PARA CONTINUAR. <<<")
        seq_proc = launch_in_new_console(seq_command)
        if seq_proc is None:
            raise RuntimeError("Falha ao iniciar o script sequencial.")
        
        # .wait() pausa este script até que o processo (e a janela) seja fechado
        seq_proc.wait() 
        print("--- Teste Sequencial Concluído ---")
        time.sleep(2)

        # --- ETAPA 2: TESTE PARALELO ---
        par_command = [".\paralelo\paralelo_sir.py", N, ITERACOES, NUM_WORKERS_STR]
        print(f"\n--- INICIANDO TESTE PARALELO (Matriz {N}x{N}, Threads: {NUM_WORKERS_STR}) ---")
        print("Uma nova janela será aberta.")
        print(">>> QUANDO O TESTE TERMINAR, FECHE A JANELA PARA CONTINUAR. <<<")
        par_proc = launch_in_new_console(par_command)
        if par_proc is None:
            raise RuntimeError("Falha ao iniciar o script paralelo.")
            
        par_proc.wait()
        print("--- Teste Paralelo Concluído ---")
        time.sleep(2)

        # --- ETAPA 3: TESTE DISTRIBUÍDO ---
        print(f"\n--- INICIANDO TESTE DISTRIBUÍDO (Matriz {N}x{N}, Workers: {NUM_WORKERS_STR}) ---")
        master_command = [".\distribuido\master.py", N, ITERACOES, NUM_WORKERS_STR]
        print(f"Iniciando Mestre em uma nova janela...")
        master_proc = launch_in_new_console(master_command)
        if master_proc is None:
            raise RuntimeError("Falha ao iniciar o mestre.")
            
        print("Aguardando 5 segundos para o mestre iniciar...")
        time.sleep(5)

        worker_command = [".\distribuido\worker.py"]
        print(f"Iniciando {NUM_WORKERS_INT} workers em novas janelas...")
        for i in range(NUM_WORKERS_INT):
            proc = launch_in_new_console(worker_command)
            if proc:
                worker_procs.append(proc)
            time.sleep(0.5)

        print("\nSimulação distribuída em andamento.")
        print("Aguardando o Mestre terminar... (Não feche esta janela)")
        master_proc.wait()
        print("--- Teste Distribuído Concluído ---")

    except KeyboardInterrupt:
        print("\nInterrupção detectada. Encerrando todos os processos...")
    except Exception as e:
        print(f"\nOcorreu um erro: {e}")
    finally:
        print("\nEncerrando todos os processos worker...")
        for proc in worker_procs:
            if proc.poll() is None:
                proc.terminate()
        
        if master_proc and master_proc.poll() is None:
            master_proc.terminate()
            
        print("Demonstração concluída.")
        print("As janelas do CMD podem agora ser fechadas manualmente.")

if __name__ == "__main__":
    main()