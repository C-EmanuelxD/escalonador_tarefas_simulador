import time
import socket
import sys
import multiprocessing
import threading

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
    conn_emissor.setblocking(False) #Não deixa esperar mensagens e apenas checa se existem mensagens e se existem ele passa
    
    #Conectar ao escalonador#
    print("Aguardando conexão do escalonador...")
    conn_escalonador, addr = skt_clock.accept()
    print(f"Clock conectado por {addr} / Esperado: {porta_escalonador}")
    conn_escalonador.setblocking(False) #Não deixa esperar mensagens e apenas checa se existem mensagens e se existem ele passa
    ###########################################
    
    while True:
        try:
            msg = conn_escalonador.recv(1024)
            print(f"Recebendo mensagem de fim de {addr}...")
            if msg and msg.decode() == 'fim':
                print("Fim de escalonamento")
                break
        except BlockingIOError: #Se não há dados na msg de fim só continua o processo
            pass
        
        conn_emissor.sendall(str(ciclo).encode())
            
        time.sleep(0.005)

        conn_escalonador.sendall(str(ciclo).encode())
        
            
        time.sleep(0.100)
        ciclo += 1
        
    print("Fechando conexões de sockets...")
    conn_emissor.close()
    conn_escalonador.close()
    skt_clock.close()
    print("Conexões fechadas.")
    

def emissor(tarefas):
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
            print("Coneão encerrada!")
        print(f"Ciclo de clock: {clock} recebido no emissor!")
        
        for id_tarefa, (tempo_ingresso, duracao, prioridade) in tarefas.items():
            if tempo_ingresso == int(clock):
                emitida = f"{id_tarefa};{tempo_ingresso};{duracao};{prioridade}"
                s_tarefas.sendall(emitida.encode())
                print(f"Tarefa {id_tarefa} emitida")
                qtd_emitidas += 1
                
        if qtd_emitidas == len(tarefas):
            print(tarefas)
            print("Todas emitidas. Enviando sinal de fim ao escalonador...")
            s_tarefas.sendall("fim".encode())
            print("Mensagem enviada")
            break
    
def escalonador():
    ##Socket para recebimento de emissão de tarefas
    fim = False
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
            
            mensagem_emissor = conn_emissor.recv(1024).decode()
            print(f"MENSAGEM DO EMISSOR: {mensagem_emissor}")
            if "fim" in mensagem_emissor:
                print("Recebimento de mensagem de fim de tarefas do emissor.")
                fim = True
                break
            elif mensagem_emissor:
                print(f"Tarefa recebida do emissor: {mensagem_emissor}")
                print(f"Processando...")
        except BlockingIOError:
            pass
        
##FUNÇÕES DE ESCALONAMENTO    
        
        


##GLOBAIS##
tarefas = {}
algoritmo = ""

if __name__ == "__main__":
    nome_arq = sys.argv[1]
    algoritmo = sys.argv[2]
    print(algoritmo)
    with open(nome_arq, "r") as arq:
        for linha in arq:
            entradas = linha.strip("\n").split(";")
            tarefas[entradas[0]] = entradas[1:]
    for tarefa in tarefas:
        tarefas[tarefa] = [int(x) for x in tarefas[tarefa]]
        
        
    proc_clock = multiprocessing.Process(target=clock)
    time.sleep(0.500)
    proc_escalonador = multiprocessing.Process(target=escalonador)
    time.sleep(0.500)
    proc_emissor = multiprocessing.Process(target=emissor, args=(tarefas,))
    
    proc_clock.start()
    time.sleep(0.500)
    proc_escalonador.start()
    time.sleep(0.500)
    proc_emissor.start()
    
    
    proc_clock.join()
    proc_emissor.join()
    proc_escalonador.join()    
