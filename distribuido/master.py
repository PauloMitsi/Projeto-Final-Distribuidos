"""
O Mestre (Servidor) (master_simplificado.py)
--------------------------------------------
Versão simplificada que contém todo o código necessário em um
único arquivo (comunicação, lógica de inicialização, etc.).
"""

import socket
import time
import argparse
import numpy as np
import pickle
import struct
from typing import List

# --- Constantes do Modelo e Rede ---
SUSCETIVEL = 0
INFECTADO = 1
RECUPERADO = 2
P_INFECCAO = 0.25
HOST = '127.0.0.1' # Roda localmente. Mude para '0.0.0.0' para rede externa.
PORT = 65432
HEADER_SIZE = 8 # 8 bytes para o cabeçalho de tamanho

# --- Módulo de Comunicação (Embutido) ---

def send_msg(sock: socket.socket, obj: object):
    """Serializa e envia um objeto com um cabeçalho de tamanho."""
    try:
        data = pickle.dumps(obj)
        header = struct.pack('Q', len(data)) # 'Q' = unsigned long long (8 bytes)
        sock.sendall(header)
        sock.sendall(data)
    except (socket.error, pickle.PickleError) as e:
        print(f"[ERRO COMUNICACAO] Erro ao enviar dados: {e}")
        raise

def recv_all(sock: socket.socket, n: int) -> bytearray:
    """Garante que 'n' bytes sejam lidos do socket."""
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None # Conexão fechada
        data.extend(packet)
    return data

def recv_msg(sock: socket.socket) -> object:
    """Recebe um objeto com cabeçalho de tamanho e o desserializa."""
    try:
        header_data = recv_all(sock, HEADER_SIZE)
        if not header_data:
            return None # Conexão fechada
        
        msg_len = struct.unpack('Q', header_data)[0]
        data = recv_all(sock, msg_len)
        
        if not data:
            return None # Conexão fechada
            
        return pickle.loads(data)
    except (socket.error, pickle.PickleError, struct.error) as e:
        print(f"[ERRO COMUNICACAO] Erro ao receber dados: {e}")
        raise

# --- Lógica de Simulação (Embutida) ---

def inicializar_grid(N: int, taxa_inicial_infectados: float = 0.05) -> np.ndarray:
    """Cria o grid inicial (com semente fixa para reprodutibilidade)."""
    np.random.seed(42)
    grid = np.zeros((N, N), dtype=np.int8)
    infectados = np.random.rand(N, N) < taxa_inicial_infectados
    grid[infectados] = INFECTADO
    return grid

# --- Lógica Principal do Mestre ---

def run_master(N: int, iteracoes: int, num_workers: int):
    """Função principal do Mestre."""
    
    print(f"[MESTRE] Iniciando Mestre em {HOST}:{PORT}")
    print(f"[MESTRE] Configuração: Grid={N}x{N}, Iterações={iteracoes}, Workers={num_workers}")

    # 1. Inicializar Grids (Ping-Pong)
    grid_a = inicializar_grid(N)
    grid_b = np.zeros_like(grid_a)
    grids = [grid_a, grid_b]

    # 2. Configurar Rede e Aceitar Conexões
    worker_conns: List[socket.socket] = []
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        server_sock.bind((HOST, PORT))
        server_sock.listen(num_workers)
        
        print(f"[MESTRE] Aguardando {num_workers} workers se conectarem...")
        for i in range(num_workers):
            conn, addr = server_sock.accept()
            worker_conns.append(conn)
            print(f"[MESTRE] Worker {i} conectado de {addr}")
            
            # Envia informações de inicialização para o worker
            send_msg(conn, {
                'id': i,
                'p_infeccao': P_INFECCAO
            })

    # 3. Calcular Fatias
    fatias = []
    chunk_size = N // num_workers
    start_row = 0
    for i in range(num_workers):
        end_row = start_row + chunk_size
        if i == num_workers - 1:
            end_row = N # Último worker pega o resto
        fatias.append((start_row, end_row))
        start_row = end_row

    print(f"[MESTRE] Fatias calculadas: {fatias}")
    print("[MESTRE] Iniciando simulação...")
    start_time = time.time()

    # 4. Loop de Simulação Principal
    for i in range(iteracoes):
        if (i+1) % 50 == 0 or i == 0:
             print(f"[MESTRE] Iniciando iteração {i+1}/{iteracoes}...")
             
        read_grid = grids[i % 2]
        write_grid = grids[(i + 1) % 2]
        
        # a. Enviar trabalho (Broadcast)
        for worker_id, conn in enumerate(worker_conns):
            start, end = fatias[worker_id]
            
            # Determinar as "linhas fantasma" (halos)
            top_halo = np.zeros(N, dtype=np.int8) if start == 0 else read_grid[start - 1, :]
            bottom_halo = np.zeros(N, dtype=np.int8) if end == N else read_grid[end, :]
            data_slice = read_grid[start:end, :]
            
            # Monta o "pacote" de trabalho
            payload = {
                'slice': data_slice,
                'top_halo': top_halo,
                'bottom_halo': bottom_halo
            }
            send_msg(conn, payload)
            
        # b. Receber resultados (Gather)
        for worker_id, conn in enumerate(worker_conns):
            result_slice = recv_msg(conn)
            
            # (Verificação de erro que causou o NoneType)
            if result_slice is None:
                print(f"[ERRO MESTRE] Worker {worker_id} desconectou inesperadamente.")
                raise ConnectionError(f"Worker {worker_id} falhou.")

            # c. Remontar o grid
            start, end = fatias[worker_id]
            write_grid[start:end, :] = result_slice

    # 5. Finalização
    end_time = time.time()
    print("[MESTRE] Simulação concluída.")
    
    for conn in worker_conns:
        try:
            send_msg(conn, {'action': 'shutdown'})
            conn.close()
        except Exception:
            pass # Ignora erros ao fechar

    grid_final = grids[iteracoes % 2]
    tempo_total = end_time - start_time
    
    print(f"\n--- Resultados (Distribuído) ---")
    print(f"Tempo total: {tempo_total:.4f} s")
    
    if N > 10:
        print("\nAmostra do grid final (10x10):")
        print(grid_final[:10, :10])
    else:
        print("\nGrid final:")
        print(grid_final)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulação Distribuída (Mestre) do Modelo SIR.")
    parser.add_argument("tamanho_matriz", type=int, help="Tamanho N da matriz NxN.")
    parser.add_argument("iteracoes", type=int, help="Número de iterações.")
    parser.add_argument("num_workers", type=int, help="Número de workers (escravos).")
    
    args = parser.parse_args()
    run_master(args.tamanho_matriz, args.iteracoes, args.num_workers)