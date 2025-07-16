import time
import socket
import sys
import multiprocessing

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


def emissor(nome_arq):
    tarefas = {}
    with open(nome_arq, "r") as arq:
        for linha in arq:
            entradas = linha.strip("\n").split(";")
            tarefas[entradas[0]] = [int(x) for x in entradas[1:]]

    qtd_emitidas = 0
    ##Socket para recebimento de clock
    s_em = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    s_em.connect((HOST, porta_clock))

    ##Socket para emissão de tarefas
    s_tarefas = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s_tarefas.connect((HOST, porta_escalonador))

    while True:
        clock = s_em.recv(8).decode()
        if not clock:
            print("Conexão encerrada!")
        print(f"Ciclo de clock: {clock} recebido no emissor!")

        for id_tarefa, (tempo_ingresso, duracao, prioridade) in tarefas.items():
            if tempo_ingresso == int(clock):
                emitida = f"{id_tarefa};{tempo_ingresso};{duracao};{prioridade}"
                try:
                    s_tarefas.sendall(emitida.encode())
                    print(f"Tarefa {id_tarefa} emitida")
                    qtd_emitidas += 1
                except (BrokenPipeError, ConnectionAbortedError):
                    print("Erro ao enviar tarefa, conexão encerrada.")
                    return

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


def escalonador(tipo_escalonamento):
    ##Socket para recebimento de emissão de tarefas
    escalonada = ""
    fim = False
    fila_prontos = {}
    s_es_em = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    s_es_em.bind((HOST, porta_escalonador))
    s_es_em.listen(1)
    print("Escalonador aguardando conexão do emissor...")
    conn_emissor, _ = s_es_em.accept()
    print("Conectado ao emissor.")
    conn_emissor.setblocking(False)

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
                break
            elif mensagem_emissor:
                print(f"Tarefa recebida do emissor: {mensagem_emissor}")
                tarefa_info, id = normaliza_tarefa(mensagem_emissor)
                fila_prontos[id] = tarefa_info
                print(f"Processando tarefa {id}")

                match tipo_escalonamento:
                    case "fcfs":
                        pass
                    case "rr":
                        pass
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


##Funções auxiliares
def normaliza_tarefa(tarefa_str: str):
    tarefa_dict = {}
    tarefa = tarefa_str.strip("\n").split(";")
    tarefa_dict['ingresso'] = int(tarefa[1])
    tarefa_dict['duracao'] = int(tarefa[2])
    tarefa_dict['prioridade'] = int(tarefa[3])
    tarefa_dict['finalizacao'] = None
    tarefa_dict['turnaround'] = None
    tarefa_dict['waiting_time'] = None

    return tarefa_dict, tarefa[0]


##FUNÇÕES DE ESCALONAMENTO
def fcfs(clock, fila):
    #REDUZ A DURACAO POR CICLO DE CLOCK, QUANDO CHEGA EM ZERO, A TAREFA TERMINOU, ENTÃO CALCULA TEMPOS DE TERMINO E ETC.
    pass


##GLOBAIS##
algoritmos = ["fcfs", "rr", "sjf", "srtf", "prioc", "priop", "priod"]

if __name__ == "__main__":
    nome_arq = sys.argv[1]
    algoritmo = sys.argv[2]
    if algoritmo not in algoritmos:
        raise ValueError("Algoritmo " + algoritmo + " invalido.")
    print(algoritmo)

    proc_clock = multiprocessing.Process(target=clock)
    time.sleep(0.500)
    proc_escalonador = multiprocessing.Process(target=escalonador, args=(algoritmo,))
    time.sleep(0.500)
    proc_emissor = multiprocessing.Process(target=emissor, args=(nome_arq,))

    proc_clock.start()
    time.sleep(0.500)
    proc_escalonador.start()
    time.sleep(0.500)
    proc_emissor.start()

    proc_clock.join()
    proc_emissor.join()
    proc_escalonador.join()
