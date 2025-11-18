"""
O Worker (Escravo) (worker_simplificado.py)
-------------------------------------------
Versão simplificada que contém todo o código necessário em um
único arquivo (comunicação, lógica de simulação, etc.).

NOVA MUDANÇA: Adicionado loop de "retry" para a conexão.
"""

import socket
import argparse
import numpy as np
import pickle
import struct
import time

# --- Constantes do Modelo e Rede ---
SUSCETIVEL = 0
INFECTADO = 1
RECUPERADO = 2
HOST = '127.0.0.1' # Endereço do Mestre
PORT = 65432
HEADER_SIZE = 8 # 8 bytes para o cabeçalho de tamanho

# --- Módulo de Comunicação (Embutido) ---
# ... (funções send_msg, recv_all, recv_msg - sem alterações) ...
def send_msg(sock: socket.socket, obj: object):
    """Serializa e envia um objeto com um cabeçalho de tamanho."""
    try:
        data = pickle.dumps(obj)
        header = struct.pack('Q', len(data))
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

# --- Lógica de Simulação (Embutida e CORRIGIDA) ---
# ... (função processar_fatia - sem alterações) ...
def processar_fatia(read_grid: np.ndarray,
                      write_grid: np.ndarray,
                      N: int,
                      p_infeccao: float,
                      random_state: np.random.RandomState):
    """
    Processa uma fatia horizontal da matriz (Lógica "Pull" CORRIGIDA).
    Lê de `read_grid` (que contém halos) e escreve em `write_grid`.
    """
    
    local_height = write_grid.shape[0]

    for x in range(local_height):
        read_x = x + 1 # +1 por causa do halo superior em read_grid[0]
        
        for y in range(N):
            estado_atual = read_grid[read_x, y]
            
            if estado_atual == INFECTADO:
                write_grid[x, y] = RECUPERADO
            
            elif estado_atual == SUSCETIVEL:
                infectado_por_vizinho = False
                for i_v in [-1, 0, 1]:
                    for j_v in [-1, 0, 1]:
                        if i_v == 0 and j_v == 0:
                            continue
                        
                        nx, ny = read_x + i_v, y + j_v
                        
                        # --- CORREÇÃO DO BUG ESTÁ AQUI ---
                        # Checa os limites da coluna (ny)
                        if 0 <= ny < N:
                            if read_grid[nx, ny] == INFECTADO:
                                if random_state.rand() < p_infeccao:
                                    infectado_por_vizinho = True
                                    break
                    if infectado_por_vizinho:
                        break
                
                if infectado_por_vizinho:
                    write_grid[x, y] = INFECTADO
                else:
                    write_grid[x, y] = SUSCETIVEL
            
            elif estado_atual == RECUPERADO:
                write_grid[x, y] = RECUPERADO

    return write_grid

# --- Lógica Principal do Worker ---

def run_worker(master_host: str, master_port: int):
    """Função principal do Worker."""
    worker_id = -1 # ID será recebido do mestre
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            
            # --- MUDANÇA AQUI: Loop de Tentativa de Conexão ---
            max_tentativas = 5
            for tentativa in range(max_tentativas):
                try:
                    print(f"[WORKER] Tentando conectar ao Mestre em {master_host}:{master_port} (Tentativa {tentativa+1}/{max_tentativas})...")
                    sock.connect((master_host, master_port))
                    # Se conectar, saia do loop
                    print("[WORKER] Conexão bem-sucedida.")
                    break
                except ConnectionRefusedError:
                    if tentativa == max_tentativas - 1:
                        # Se for a última tentativa, desista
                        print("[WORKER] ERRO FATAL: Não foi possível conectar ao Mestre. Desistindo.")
                        raise
                    # Se não for a última, espere e tente de novo
                    time.sleep(1)
            # --- FIM DA MUDANÇA ---
            
            
            # 1. Receber Info de Inicialização
            init_data = recv_msg(sock)
            worker_id = init_data['id']
            p_infeccao = init_data['p_infeccao']
            
            # Gerador aleatório único por worker
            random_state = np.random.RandomState(seed=42 + worker_id)
            print(f"[WORKER {worker_id}] Conectado e registrado.")

            # 2. Loop de Trabalho
            while True:
                # a. Esperar trabalho
                payload = recv_msg(sock)
                
                if payload is None or payload.get('action') == 'shutdown':
                    print(f"[WORKER {worker_id}] Recebido sinal de desligamento.")
                    break
                
                # b. Desempacotar trabalho
                data_slice = payload['slice']
                top_halo = payload['top_halo']
                bottom_halo = payload['bottom_halo']
                
                N = data_slice.shape[1]
                slice_height = data_slice.shape[0]
                
                # Montar o grid de LEITURA local (com halos)
                read_grid_local = np.zeros((slice_height + 2, N), dtype=np.int8)
                read_grid_local[1:-1, :] = data_slice
                read_grid_local[0, :] = top_halo
                read_grid_local[-1, :] = bottom_halo
                
                # Grid de ESCRITA local
                write_grid_local = np.zeros_like(data_slice)

                # c. Processar a fatia
                result_slice = processar_fatia(
                    read_grid=read_grid_local,
                    write_grid=write_grid_local,
                    N=N,
                    p_infeccao=p_infeccao,
                    random_state=random_state
                )
                
                # d. Enviar resultado de volta
                send_msg(sock, result_slice)

    except socket.error as e:
        print(f"[WORKER {worker_id}] Erro de Socket: {e}")
    except Exception as e:
        print(f"[WORKER {worker_id}] Erro inesperado: {e}")
    finally:
        print(f"[WORKER {worker_id}] Desconectado.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulação Distribuída (Worker) do Modelo SIR.")
    parser.add_argument("--host", type=str, default=HOST, help="Endereço IP do Mestre.")
    parser.add_argument("--port", type=int, default=PORT, help="Porta do Mestre.")
    
    args = parser.parse_args()
    run_worker(args.host, args.port)