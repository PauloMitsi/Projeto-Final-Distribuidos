"""
Uso:
    python sequencial_sir.py <tamanho_matriz> <num_iteracoes>

Descrição:
    Esta versão usa a mesma lógica de cálculo "pull" (Suscetível verifica
    vizinhos) da versão paralela, para garantir uma comparação de
    desempenho justa.
"""

import numpy as np
import time
import argparse

# --- Constantes do Modelo SIR ---
SUSCETIVEL = 0
INFECTADO = 1
RECUPERADO = 2
P_INFECCAO = 0.25 # Probabilidade de infecção
# ------------------------------

def inicializar_grid(N: int, taxa_inicial_infectados: float = 0.05) -> np.ndarray:
    """Cria o grid inicial (idêntico ao paralelo)."""
    np.random.seed(42)
    grid = np.zeros((N, N), dtype=np.int8)
    infectados = np.random.rand(N, N) < taxa_inicial_infectados
    grid[infectados] = INFECTADO
    return grid

def simular_sequencial(N, num_iteracoes):
    """Executa a simulação sequencial com lógica "pull"."""
    
    # Cria os grids de ping-pong
    grid_a = inicializar_grid(N)
    grid_b = grid_a.copy()
    grids = [grid_a, grid_b]
    
    # Gerador de números aleatórios (para ser comparável ao paralelo)
    random_state = np.random.RandomState(seed=42)

    print(f"Iniciando simulação sequencial (Grid: {N}x{N}, Iterações: {num_iteracoes})...")
    start_time = time.time()

    for i in range(num_iteracoes):
        # Estratégia "Ping-Pong"
        read_grid = grids[i % 2]
        write_grid = grids[(i + 1) % 2]
        
        # --- Kernel de Cálculo (lógica "pull", idêntica à SIRThread) ---
        for x in range(N):
            for y in range(N):
                
                estado_atual = read_grid[x, y]
                
                if estado_atual == INFECTADO:
                    write_grid[x, y] = RECUPERADO
                
                elif estado_atual == SUSCETIVEL:
                    infectado_por_vizinho = False
                    # Loop pelos 8 vizinhos
                    for i_v in [-1, 0, 1]:
                        for j_v in [-1, 0, 1]:
                            if i_v == 0 and j_v == 0:
                                continue
            
                            nx, ny = x + i_v, y + j_v
                            # Checa se o vizinho está dentro dos limites
                            if 0 <= nx < N and 0 <= ny < N:
                                if read_grid[nx, ny] == INFECTADO:
                                    if random_state.rand() < P_INFECCAO:
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

    end_time = time.time()
    tempo_execucao = end_time - start_time
    print("Simulação sequencial concluída.")

    # Determina qual grid é o final
    grid_final = grids[num_iteracoes % 2]
    return grid_final, tempo_execucao

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulação Sequencial (Lógica Pull) do Modelo SIR.")
    parser.add_argument("tamanho_matriz", type=int, help="Tamanho N da matriz NxN.")
    parser.add_argument("iteracoes", type=int, help="Número de iterações da simulação.")
    
    args = parser.parse_args()
    
    N = args.tamanho_matriz
    ITERACOES = args.iteracoes

    grid_final, tempo = simular_sequencial(N, ITERACOES)

    print("\n--- Resultados (Sequencial) ---")
    print(f"Tempo total: {tempo:.4f} s")
    
    if N > 10:
        print("\nAmostra do grid final (10x10):")
        print(grid_final[:10, :10])
    else:
        print("\nGrid final:")
        print(grid_final)