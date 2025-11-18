
"""
Parte Algoritmo de Paralelização por: Victor Ribeiro Calado


Testes realizados
python paralelo_sir.py 500 100 4   4 Threads
python paralelo_sir.py 500 100 2   2 Threads
python paralelo_sir.py 500 100 8   8 Threads
"""


import numpy as np
import time
import threading
import argparse


# --- Constantes do Modelo SIR ---
SUSCETIVEL = 0
INFECTADO = 1
RECUPERADO = 2
# ------------------------------

def inicializar_grid(N: int, taxa_inicial_infectados: float = 0.05) -> np.ndarray:
    """Cria o grid inicial (idêntico ao sequencial)."""
    # Define a semente do gerador aleatório para reprodutibilidade
    np.random.seed(42)
    grid = np.zeros((N, N), dtype=np.int8)
    infectados = np.random.rand(N, N) < taxa_inicial_infectados
    grid[infectados] = INFECTADO
    return grid

class SIRThread(threading.Thread):
    """
    Uma thread trabalhadora que calcula uma "fatia" horizontal do modelo SIR.
    """
    def __init__(self, grid_a, grid_b, start_row, end_row, N, num_iteracoes, barrier, p_infeccao):
        super().__init__()
        self.grid_a = grid_a  # Grid de leitura
        self.grid_b = grid_b  # Grid de escrita
        
        self.start_row = start_row
        self.end_row = end_row
        self.N = N
        self.num_iteracoes = num_iteracoes
        self.barrier = barrier
        self.p_infeccao = p_infeccao
        
        # Cada thread precisa de seu próprio estado de gerador aleatório
        # para ser verdadeiramente paralela e segura.
        # Usamos o ID da thread como semente.
        thread_id = threading.current_thread().ident
        if thread_id is None:
             thread_id = int(time.time() * 1000) % 1000
             
        self.random_state = np.random.RandomState(seed=thread_id)

    def run(self):
        """O código que a thread executa."""
        
        for i in range(self.num_iteracoes):
            # Estratégia "Ping-Pong": Alterna os grids de leitura e escrita
            if i % 2 == 0:
                read_grid = self.grid_a
                write_grid = self.grid_b
            else:
                read_grid = self.grid_b
                write_grid = self.grid_a
            
            # --- Kernel de Cálculo (lógica SIR "paralelizada") ---
            # Esta lógica é "read-neighbors, write-self" (ler vizinhos, escrever em si)
            for x in range(self.start_row, self.end_row):
                for y in range(0, self.N): # Calculamos todas as colunas da nossa linha
                    
                    estado_atual = read_grid[x, y]
                    
                    if estado_atual == INFECTADO:
                        # Infectados se tornam recuperados
                        write_grid[x, y] = RECUPERADO
                    
                    elif estado_atual == SUSCETIVEL:
                        # Suscetíveis checam se vizinhos os infectam
                        infectado_por_vizinho = False
                        # Loop pelos 8 vizinhos
                        for i_v in [-1, 0, 1]:
                            for j_v in [-1, 0, 1]:
                                if i_v == 0 and j_v == 0:
                                    continue
                                
                                nx, ny = x + i_v, y + j_v
                                # Checa se o vizinho está dentro dos limites
                                if 0 <= nx < self.N and 0 <= ny < self.N:
                                    # Se o vizinho ESTAVA infectado...
                                    if read_grid[nx, ny] == INFECTADO:
                                        # ...rola o dado para ver se infecta
                                        # (Usando o gerador aleatório seguro da thread)
                                        if self.random_state.rand() < self.p_infeccao:
                                            infectado_por_vizinho = True
                                            break # Um já infectou, não precisa checar os outros
                            if infectado_por_vizinho:
                                break
                        
                        if infectado_por_vizinho:
                            write_grid[x, y] = INFECTADO
                        else:
                            write_grid[x, y] = SUSCETIVEL
                    
                    elif estado_atual == RECUPERADO:
                        # Recuperados continuam recuperados (Modelo SIR)
                        # (Para um modelo SIS, eles voltariam a ser SUSCETIVEL)
                        write_grid[x, y] = RECUPERADO
            
            # Tarefa de Sincronização: Ponto de encontro
            # Ninguém começa a próxima iteração (i+1) antes que TODAS
            # as threads terminem a iteração (i).
            self.barrier.wait()


def run_parallel(N, num_iteracoes, num_threads, p_infeccao=0.25):
    """
    Executa a simulação SIR em paralelo com threads.
    """
    # Cria os dois grids que serão compartilhados
    grid_a = inicializar_grid(N) # Já define a semente aqui
    grid_b = grid_a.copy() # Copia o estado inicial

    # A barreira deve esperar por TODAS as threads
    barrier = threading.Barrier(num_threads)
    
    threads = []
    
    # Tarefa de Divisão: Fatiar a matriz horizontalmente
    # (Dividimos todas as linhas, de 0 até N)
    chunk_size = N // num_threads
    start_row = 0
    
    for i in range(num_threads):
        end_row = start_row + chunk_size
        # Para a última thread, garanta que ela pegue o resto
        if i == num_threads - 1:
            end_row = N
            
        thread = SIRThread(grid_a, grid_b, start_row, end_row, N, num_iteracoes, barrier, p_infeccao)
        threads.append(thread)
        
        start_row = end_row

    print(f"Iniciando simulação paralela (Grid: {N}x{N}, Iterações: {num_iteracoes}, Threads: {num_threads})...")
    start_time = time.time()

    # Inicia todas as threads
    for t in threads:
        t.start()

    # Espera todas as threads terminarem
    for t in threads:
        t.join()

    end_time = time.time()
    tempo_execucao = end_time - start_time
    
    print(f"Simulação paralela concluída.")

    # Determina qual grid é o final, baseado no Ping-Pong
    if num_iteracoes % 2 == 0:
        grid_final = grid_a
    else:
        grid_final = grid_b

    return grid_final, tempo_execucao


        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulação Paralela (Threads) do Modelo SIR.")
    parser.add_argument("tamanho_matriz", type=int, help="Tamanho N da matriz NxN.")
    parser.add_argument("iteracoes", type=int, help="Número de iterações da simulação.")
    parser.add_argument("num_threads", type=int, help="Número de threads para usar.")
    
    # Adiciona o argumento de benchmark
    parser.add_argument("--benchmark", action="store_true", help="Modo silencioso, imprime apenas o tempo de execução.")
    
    args = parser.parse_args()
    
    N = args.tamanho_matriz
    ITERACOES = args.iteracoes
    NUM_THREADS = args.num_threads

    if not args.benchmark:
        print(f"Iniciando simulação paralela (Grid: {N}x{N}, Iterações: {ITERACOES}, Threads: {NUM_THREADS})...")

    # Executa a simulação
    grid_final, tempo = run_parallel(N, ITERACOES, NUM_THREADS)

    if args.benchmark:
        # Modo benchmark: imprime APENAS o tempo em segundos
        print(f"{tempo:.4f}")
    else:
        # Modo interativo normal
        print(f"Simulação paralela concluída.")
        print("\n--- Resultados ---")
        print(f"Tempo total: {tempo:.4f} s")
        
        if N > 10:
            print("\nAmostra do grid final (10x10):")
            print(grid_final[:10, :10])
        else:
            print("\nGrid final:")
            print(grid_final)