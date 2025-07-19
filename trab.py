import time
import socket
import sys
import multiprocessing
import math

##PORTAS PARA CONEXÃO DE SOCKETS
HOST = "localhost"
porta_clock = 4000
porta_emissor = 4001
porta_escalonador = 4002


def clock():
    ciclo = 0
    #####ABERTURA DE CONEXÕES############
    skt_clock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    skt_clock.bind((HOST, porta_clock))
    skt_clock.listen(2)
    print("Aguardando conexão...")

    #Conectar ao emissor#
    print("Aguardando conexão do emissor...")
    conn_emissor, addr = skt_clock.accept()
    print(f"Clock conectado por {addr} / Esperado: {porta_emissor}")
    conn_emissor.setblocking(False)

    #Conectar ao escalonador#
    print("Aguardando conexão do escalonador...")
    conn_escalonador, addr = skt_clock.accept()
    print(f"Clock conectado por {addr} / Esperado: {porta_escalonador}")
    conn_escalonador.setblocking(False)
    ###########################################

    while True:
        try:
            msg = conn_escalonador.recv(1024)
            if msg and msg.decode() == 'fim':
                print(f"Recebendo mensagem de fim de {addr}...")
                print("Fim de escalonamento")
                break
        except (BlockingIOError, ConnectionAbortedError):
            pass

        try:
            conn_emissor.sendall(str(ciclo).encode())
        except (BrokenPipeError, ConnectionAbortedError):
            break

        time.sleep(0.005)

        try:
            conn_escalonador.sendall(str(ciclo).encode())
        except (BrokenPipeError, ConnectionAbortedError):
            break

        time.sleep(0.100)
        ciclo += 1

    print("Fechando conexões de sockets...")
    conn_emissor.close()
    conn_escalonador.close()
    skt_clock.close()
    print("Conexões fechadas.")


def emissor(prontas, nome_arq, tipo_escalonamento):
    tarefas = {}
    print("Preparando emissão de tarefas...")
    with open(nome_arq, "r") as arq:
        for linha in arq:
            dict, id = normaliza_tarefa(linha)
            tarefas[id] = dict
    print(tarefas.keys())
    
    
    
    
    qtd_emitidas = 0
    ##Socket para recebimento de clock
    s_em = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    s_em.connect((HOST, porta_clock))

    ##Socket para emissão de tarefas
    print("Conectando ao socket do escalonador...")
    s_tarefas = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s_tarefas.connect((HOST, porta_escalonador))
    print("Conectado ao escalonador!!!")
    

    print("Enviando tipo de escalonamento ao escalonador: "+tipo_escalonamento)
    s_tarefas.sendall(tipo_escalonamento.encode())
    print("Enviado com sucessor!!")
    
    

    
    while True:
        clock = s_em.recv(8).decode()
        if not clock:
            print("Conexão encerrada!")
        print(f"Ciclo de clock: {clock} recebido no emissor!")

        for id_tarefa, valores in tarefas.items():
            if int(valores["ingresso"]) == int(clock):
                prontas[id_tarefa] = valores
                qtd_emitidas += 1


        if qtd_emitidas == len(tarefas):
            print("Todas emitidas. Enviando sinal de fim ao escalonador...")
            try:
                s_tarefas.sendall("fim".encode())
                print("Mensagem de fim enviada")
            except:
                pass
            break

    s_tarefas.setblocking(False)
    while True:
        try:
            msg_fim = s_tarefas.recv(1024)
            if msg_fim:
                break
        except BlockingIOError:
            pass


def escalonador(prontas):
    ##Socket para recebimento de emissão de tarefas
    finalizados = {}
    fim = False
    s_es_em = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    s_es_em.bind((HOST, porta_escalonador))
    s_es_em.listen(1)
    print("Escalonador aguardando conexão do emissor...")
    conn_emissor, _ = s_es_em.accept()
    print("Conectado ao emissor.")
    conn_emissor.setblocking(False)
    
    print("Recebendo tipo de escalonamento...")
    tipo_escalonamento = conn_emissor.recv(1024).decode()
    print("Tipo de esclonamento recebido: "+tipo_escalonamento)
    
    ##socket para recebimento do clock
    s_es_clock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    s_es_clock.connect((HOST, porta_clock))
    print("Conectado ao clock.")

    while True:
        try:
            clock = s_es_clock.recv(12).decode()
            if not clock:
                print("Conexão encerrada!")
            print(f"Ciclo de clock: {clock} recebido no escalonador!")
            try:
                mensagem_emissor = conn_emissor.recv(1024).decode()
            except BlockingIOError:
                mensagem_emissor = ""

            if "fim" in mensagem_emissor and not fim:
                print("Recebimento de mensagem de fim de tarefas do emissor.")
                fim = True
            else:
                print(f"Lista de tarefas: {prontas}")
                match tipo_escalonamento:
                    case "fcfs":
                        prontas, finalizados = fcfs(prontas, clock, finalizados)
                        print(f"finzalidas: {finalizados}")
                    case "rr":
                        prontas, finalizados = rr(prontas, clock, finalizados)
                        print(f"finzalidas: {finalizados}")
                    case "sjf":
                        pass
                    case "srtf":
                        pass
                    case "prioc":
                        pass
                    case "priop":
                        pass
                    case "priod":
                        pass
            if not prontas and fim:
                break

        except (BrokenPipeError, ConnectionAbortedError):
            break

    # Enviar sinal de fim para clock e emissor
    print("Escalonador finalizado. Enviando sinais de fim.")
    try:
        conn_emissor.sendall("fim".encode())
    except:
        pass

    try:
        s_es_clock.sendall("fim".encode())
    except:
        pass

    conn_emissor.close()
    s_es_clock.close()
    s_es_em.close()
    
    escreve_finalizados(finalizados)

##FUNÇÕES DE ESCALONAMENTO
def fcfs(prontas, clock, finalizados):
    if not prontas:
        return prontas, finalizados
    
    list_iter = iter(prontas.items())
    chave_escalonado, valor_escalonado = next(list_iter)
    print(f"Escalonando: {chave_escalonado}")
    print(f"ANTES DO DECRTEMENTO: {chave_escalonado} - "+str(valor_escalonado['duracao']))
    valor_escalonado['duracao'] -= 1
    print(f"DEPOIS DO DECRTEMENTO: {chave_escalonado} - "+str(valor_escalonado['duracao']))
    
    prontas[chave_escalonado] = valor_escalonado
    
    for chave, valor in prontas.items():
        if chave != chave_escalonado:
            # Faz uma cópia, atualiza e reatribui (evita problemas com Manager.dict)
            copia = dict(valor)
            copia['waiting_time'] += 1
            prontas[chave] = copia
    
    
    if valor_escalonado['duracao'] == 0:
        with open('saida.txt', 'a') as arq:
            arq.write(chave_escalonado+";")
        finalizados[chave_escalonado] = valor_escalonado
        finalizados[chave_escalonado]['finalizacao'] = int(clock)
        finalizados[chave_escalonado]['turnaround'] += finalizados[chave_escalonado]['waiting_time']
        del prontas[chave_escalonado]
    else:
        with open('saida.txt', 'a') as arq:
            arq.write(chave_escalonado+";")

    return prontas, finalizados

def rr(prontas, clock, finalizados):
    if not prontas:
        return prontas, finalizados
    
    list_iter = iter(prontas.items())
    chave_escalonado, valor_escalonado = next(list_iter)
    print(f"Escalonando: {chave_escalonado}")
    valor_escalonado['duracao'] -= 1
    valor_escalonado['quantum'] -= 1
    
    prontas[chave_escalonado] = valor_escalonado
    
    for chave, valor in prontas.items():
        if chave != chave_escalonado:
            # Faz uma cópia, atualiza e reatribui (evita problemas com Manager.dict)
            copia = dict(valor)
            copia['waiting_time'] += 1
            prontas[chave] = copia
            
    if valor_escalonado['duracao'] == 0:
        with open('saida.txt', 'a') as arq:
            arq.write(chave_escalonado+";")
        finalizados[chave_escalonado] = valor_escalonado
        finalizados[chave_escalonado]['finalizacao'] = int(clock)
        finalizados[chave_escalonado]['turnaround'] += finalizados[chave_escalonado]['waiting_time']
        del prontas[chave_escalonado]
    elif valor_escalonado['quantum'] == 0:
        with open('saida.txt', 'a') as arq:
            arq.write(chave_escalonado+";")
        valor_escalonado['quantum'] = 3
        del prontas[chave_escalonado]
        prontas[chave_escalonado] = valor_escalonado
        print(f"FILA APOS COLOCADO AO FINAL: {prontas}")
    else:
        with open('saida.txt', 'a') as arq:
            arq.write(chave_escalonado+";")
            
    return prontas, finalizados
    
def sjf(prontas, clock, finalizadas):
    pass
    
    
##Funções auxiliares
def normaliza_tarefa(tarefa_str: str):
    tarefa_dict = {}
    tarefa = tarefa_str.strip("\n").split(";")
    tarefa_dict['ingresso'] = int(tarefa[1]) #Clock de ingresso na fila
    tarefa_dict['duracao'] = int(tarefa[2]) #Duracao é decrementada a cada ciclo em que o processador usa
    tarefa_dict['prioridade'] = int(tarefa[3]) #Seta quem fica ao inicio da fila (depende do escalonamento)
    tarefa_dict['finalizacao'] = None #Clock em que duracao chega em 0
    tarefa_dict['turnaround'] = int(tarefa[2]) #Soma de waiting time com duracao
    tarefa_dict['waiting_time'] = 0 #Tempo não executando, incrementa em todos menos no que está escalonado <- 
    tarefa_dict['quantum'] = 3

    return tarefa_dict, tarefa[0]

def escreve_finalizados(finalizados):
    soma_exec = 0
    soma_espera = 0
    with open('saida.txt', 'a') as arq:
        arq.write('\n')
        for chave, valor in finalizados.items():
            #ingresso na prontas
            #finalizacao
            #turnaround
            arq.write(chave+";"+str(valor['ingresso'])+";"+str(valor['finalizacao'])+";"+str(valor['turnaround'])+";"+str(valor['waiting_time'])+"\n")
            #waiting time
            #calculo after
            soma_exec += valor['turnaround']
            soma_espera += valor['waiting_time']
        qtd_chave = len(finalizados.keys())
        media_exec = math.ceil((soma_exec / qtd_chave) * 10) / 10
        media_espera = math.ceil((soma_espera / qtd_chave) * 10) / 10
        
        arq.write(str(media_exec)+";"+str(media_espera))


##GLOBAIS##
algoritmos = ["fcfs", "rr", "sjf", "srtf", "prioc", "priop", "priod"]

if __name__ == "__main__":
    nome_arq = sys.argv[1]
    algoritmo = sys.argv[2]
    if algoritmo not in algoritmos:
        raise ValueError("Algoritmo " + algoritmo + " invalido.")
    print(algoritmo)
    
    with open('saida.txt', 'w+'):
        pass
        

    with multiprocessing.Manager() as manager: #Compartilhamento de lista entre processos
        dict_prontas = manager.dict()
    
        proc_clock = multiprocessing.Process(target=clock)
        time.sleep(0.500)
        proc_escalonador = multiprocessing.Process(target=escalonador, args=(dict_prontas,))
        time.sleep(0.500)
        proc_emissor = multiprocessing.Process(target=emissor, args=(dict_prontas, nome_arq, algoritmo,))

        proc_clock.start()
        time.sleep(0.500)
        proc_escalonador.start()
        time.sleep(0.500)
        proc_emissor.start()

        proc_clock.join()
        proc_emissor.join()
        proc_escalonador.join()
