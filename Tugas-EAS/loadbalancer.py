from socket import *
import socket
import time
import sys
import logging
import multiprocessing
from concurrent.futures import ProcessPoolExecutor

class BackendList:
    def __init__(self):
        self.servers = []
        self.servers.append(('127.0.0.1', 50001)) # Multithread server
        # self.servers.append(('127.0.0.1', 50002)) # Process Pool server
        # self.servers.append(('127.0.0.1', 50003)) # Thread Pool server
        self.current = 0
        self.client_map = {}  # mapping client_ip -> backend

    def getserver(self, client_ip=None):
        # IP HASH
        # if client_ip:
        #     if client_ip in self.client_map:
        #         return self.client_map[client_ip]
        #     s = self.servers[self.current]
        #     self.client_map[client_ip] = s
        #     self.current = (self.current + 1) % len(self.servers)
        #     return s
        
        # Round robin
        s = self.servers[self.current]
        self.current = (self.current + 1) % len(self.servers)
        return s

def ProcessTheClient(connection, address, backend_sock, mode='toupstream'):
    try:
        while True:
            try:
                if mode == 'toupstream':
                    datafrom_client = connection.recv(32)
                    if datafrom_client:
                        backend_sock.sendall(datafrom_client)
                    else:
                        backend_sock.close()
                        break
                elif mode == 'toclient':
                    datafrom_backend = backend_sock.recv(32)
                    if datafrom_backend:
                        connection.sendall(datafrom_backend)
                    else:
                        connection.close()
                        break
            except OSError as e:
                pass
    except Exception as ee:
        logging.warning(f"error {str(ee)}")
    connection.close()
    return

def Server():
    the_clients = []
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    backend = BackendList()

    my_socket.bind(('0.0.0.0', 44444))
    my_socket.listen(1)
    print("Load Balancer berjalan di port 44444")

    with ProcessPoolExecutor(20) as executor:
        while True:
            connection, client_address = my_socket.accept()
            client_ip = client_address[0]
            backend_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            backend_sock.settimeout(1)
            backend_address = backend.getserver(client_ip)
            logging.warning(f"{client_address} connecting to {backend_address}")
            try:
                backend_sock.connect(backend_address)
                toupstream = executor.submit(ProcessTheClient, connection, client_address, backend_sock, 'toupstream')
                toclient = executor.submit(ProcessTheClient, connection, client_address, backend_sock, 'toclient')
                jumlah = ['x' for i in the_clients if i and hasattr(i, 'running') and i.running() == True]
            except Exception as err:
                logging.error(err)
                pass

def main():
    Server()

if __name__ == "__main__":
    main()
