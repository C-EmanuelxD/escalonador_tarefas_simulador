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
    skt_clock.bind((HOST, 4000))
    skt_clock.listen(1)
    conn, addr = skt_clock.accept() #Espera alguem conectar (Emissor deve ser a conexão)
    print(f"Clock conectado por {addr} / Esperado: {porta_emissor}")
    conn.setblocking(False) #Não deixa esperar mensagens e apenas checa se existem mensagens e se existem ele passa
    
    #Conectar ao emissor#
    skt_emissor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    skt_emissor.connect((HOST, porta_emissor))
    
    #Conectar ao escalonador#
    skt_escalonador = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    skt_escalonador.connect((HOST, porta_escalonador))
    ###########################################
    
    while True:
        try:
            msg = skt_clock.recv(1024)
            if msg and msg.decode() == 'fim':
                print("Fim de escalonamento")
                break
        except BlockingIOError: #Se não há dados na msg de fim só continua o processo
            pass
        
        skt_emissor.sendall(str(ciclo).encode())
        print(f"Ciclo de clock enviado ao emissor: {ciclo}")
            
        time.sleep(0.005)

        skt_escalonador.sendall(str(ciclo).encode())
        print(f"Ciclo de clock enviado ao escalonador: {ciclo}")
        
            
        time.sleep(0.100)
        ciclo += 1
        
    print("Fechando conexões de sockets...")
    conn.close()
    skt_emissor.close()
    skt_escalonador.close()
    skt_clock.close()
    print("Conexões fechadas.")
    

def emissor():
    s_em = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    s_em.bind((HOST, porta_emissor))
    s_em.listen(2)

def escalonador():
    s_es = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    s_es.bind((HOST, porta_escalonador))
    s_es.listen(2)


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
        
        
    
        
            