from socket import *
import socket
import time
import sys
import logging
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from game_server import HttpServer

# Create shared state manager at module level
def create_shared_state():
    manager = multiprocessing.Manager()
    return manager.dict({
        'players': manager.list(),
        'cards': manager.dict(),
        'current_turn': None,
        'status': 'waiting',
        'events': manager.list(),
        'deck_initialized': False
    })

# Pass shared_state as parameter to worker function
def ProcessTheClient(connection, address, shared_state):
    # Create HttpServer with shared state for this process
    httpserver = HttpServer(shared_state=shared_state)
    
    socket.setdefaulttimeout(5)  
    rcv = ""
    while True:
        try:
            data = connection.recv(32)
            if data:
                d = data.decode()
                rcv = rcv + d
                if rcv[-2:] == '\r\n':
                    hasil = httpserver.proses(rcv)
                    hasil = hasil + "\r\n\r\n".encode()
                    connection.sendall(hasil)
                    rcv = ""
            else:
                break
        except OSError as e:
            connection.close()
            break
    connection.close()
    return

def Server():
    the_clients = []
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    my_socket.bind(('0.0.0.0', 50002))
    my_socket.listen(1)
    print("Server berjalan dengan process pool di port 50002")
    
    # Create shared state once for all processes
    shared_state = create_shared_state()
    
    with ProcessPoolExecutor(20) as executor:
        while True:
            connection, client_address = my_socket.accept()
            # Pass shared_state to each worker process
            p = executor.submit(ProcessTheClient, connection, client_address, shared_state)
            the_clients.append(p)
            jumlah = ['x' for i in the_clients if i.running() == True]
            print(f"Active processes: {len(jumlah)}")

def main():
    Server()

if __name__ == "__main__":
    main()