# Simulação de Epidemia SIR - Análise de Desempenho
Trabalho Prático da disciplina de Sistemas Distribuídos.

Este projeto implementa e compara o desempenho de um modelo de simulação de epidemia (SIR - Suscetível, Infectado, Recuperado) em três arquiteturas distintas:
1.  **Sequencial**: Execução em um único processo e thread.
2.  **Paralela**: Execução com múltiplas threads na mesma máquina.
3.  **Distribuída**: Execução com múltiplos processos (em uma ou mais máquinas) coordenados por Sockets.

## Estrutura do Repositório

O projeto está organizado nas seguintes pastas e arquivos:

* `/sequencial/sequencial_sir.py`: A implementação base (baseline) que roda em uma única thread. Esta versão utiliza a lógica "pull" para garantir uma comparação justa com as demais.
* `/paralelo/paralelo_sir.py`: A implementação paralela usando a biblioteca `threading` e `Barrier` para sincronização de threads.
* `/distribuido/master.py`: O servidor (Mestre) da implementação distribuída. Ele coordena os workers, distribui as fatias da matriz e agrega os resultados.
* `/distribuido/worker.py`: O cliente (Escravo) da implementação distribuída. Ele se conecta ao mestre, recebe uma fatia do trabalho, processa-a e a envia de volta.
* `/distribuido/simulacao.py`: **Lançador de demonstração** (para Windows). Este script abre automaticamente as janelas do CMD para os testes Sequencial, Paralelo e Distribuído (Mestre + Workers) em sequência. Ideal para a apresentação em vídeo.

### Scripts de Análise

* `benchmark.py`: Script de automação que executa os três modos com diferentes parâmetros e salva os tempos de execução no arquivo `resultados.csv`.
* `plotar_graficos.py`: Lê o `resultados.csv` e gera os gráficos de análise de desempenho (`grafico_escalabilidade.png` e `grafico_speedup.png`).

## Requisitos

O projeto foi desenvolvido em Python 3. As seguintes bibliotecas são necessárias:

* `numpy`: Para cálculos de matriz eficientes.
* `pandas`: Para análise dos resultados do benchmark.
* `matplotlib` e `seaborn`: Para a geração dos gráficos.

Você pode instalar todas as dependências com:
```bash
pip install numpy pandas matplotlib seaborn
````

## Como Executar

Existem três formas principais de executar o código:

### 1\. Execução de Demonstração (Para Apresentação)

Este script executa as três versões em sequência para fácil visualização.

1.  Abra um terminal na pasta raiz do projeto.
2.  Execute o `simulacao.py` (dentro da pasta `distribuido`) passando os parâmetros:


````bash
# Formato: python ./distribuido/simulacao.py <tamanho> <iteracoes> <workers/threads>
python ./distribuido/simulacao.py 500 100 4
````

**Observação:** Você deve fechar a janela do CMD de cada teste (Sequencial, Paralelo) para que o próximo se inicie.

### 2\. Geração de Gráficos (Para Análise)

Para gerar os dados de desempenho e os gráficos:

1.  **Rodar o Benchmark:**

    ````bash
    python benchmark.py
    ````

    (Isso pode demorar vários minutos. Ele criará o arquivo `resultados.csv`.)

2.  **Gerar os Gráficos:**

    ````bash
    python plotar_graficos.py
    ````

    (Isso criará `grafico_escalabilidade.png` e `grafico_speedup.png`.)

### 3\. Execução Manual (Para Depuração)

Você também pode executar cada script individualmente.

**Sequencial:**

````bash
python ./sequencial/sequencial_sir.py <tamanho> <iteracoes>
# Ex: python ./sequencial/sequencial_sir.py 500 100
````

**Paralelo (Threads):**

````bash
python ./paralelo/paralelo_sir.py <tamanho> <iteracoes> <num_threads>
# Ex: python ./paralelo/paralelo_sir.py 500 100 4
````

**Distribuído (Sockets/Processos):**

1.  Abra um terminal para o Mestre:
    ````bash
    python ./distribuido/master.py <tamanho> <iteracoes> <num_workers>
    # Ex: python ./distribuido/master.py 500 100 2
    ````
2.  Abra um terminal para CADA worker:
    ````bash
    python ./distribuido/worker.py
    ````


## Autores

  * **Claudiney Júnior Givisiez** - Implementação da lógica Distribuída (Multi-Process)
  * **Victor Ribeiro Calado** - Implementação da lógica Paralela (Multi-Thread).
  * **Paulo Cesar de Oliveira Mitsi** - Implementação da lógica de benchmark (simulação, benchmark e plotar_graficos)
  * **Pedro Enzo Laurynovi** - Implementação Sequencial.
