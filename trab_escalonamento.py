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
    

def emissor():
    s_em = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    s_em.connect((HOST, porta_clock))
    
    while True:
        clock = s_em.recv(8).decode()
        print(f"Ciclo de clock: {clock} recebido no emissor!")
        if clock == '4':
            print("Fim: emissor")
            break
    
def escalonador():
    s_es = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    s_es.connect((HOST, porta_clock))

    while True:
        clock = s_es.recv(8).decode()
        print(f"Ciclo de clock: {clock} recebido no escalonador!")
        if clock == '4':
            print("Fim: ESCALONADOR")
            print("Enviando sinal de fim para clock...")
            s_es.sendall(b"fim")
            print("Sinal enviado!")
            break


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
    proc_emissor = multiprocessing.Process(target=emissor)
    time.sleep(0.500)
    proc_escalonador = multiprocessing.Process(target=escalonador)
    
    proc_clock.start()
    time.sleep(0.500)
    proc_emissor.start()
    time.sleep(0.500)
    proc_escalonador.start()
    
    
    proc_clock.join()
    proc_emissor.join()
    proc_escalonador.join()    
