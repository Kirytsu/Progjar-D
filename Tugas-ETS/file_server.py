from socket import *
import socket
import threading
import logging
import time
import sys
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from file_protocol import  FileProtocol
fp = FileProtocol()

def handle_client_request(connection):
    try:
        data_b = ""
        while True:
            data = connection.recv(1024) # 4 bytes
            if data:
                data_b += data.decode()
            else:
                break
        
            if data_b.endswith("\r\n\r\n"):
                break

        if data_b:
            d = data_b[:-4]
            hasil = fp.proses_string(d)
            hasil += "\r\n\r\n"
            connection.sendall(hasil.encode())
    except Exception as e:
        logging.error(f"Error handling client: {e}")
    finally:
        connection.close()
        
# Multithreading
class ProcessTheClient(threading.Thread):
    def __init__(self, connection, address):
        self.connection = connection
        self.address = address
        threading.Thread.__init__(self)

    def run(self):
        handle_client_request(self.connection)

class Server(threading.Thread):
    def __init__(self, ipaddress='0.0.0.0', mode='thread', pool_size=5):
        # Bind IP, port 50000
        self.ipinfo = (ipaddress, 50000)
        self.the_clients = []
        # Mode untuk concurrency executor
        self.mode = mode
        self.pool_size = pool_size
        self.executor = None
        
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        threading.Thread.__init__(self)

        if self.mode == 'threadpool':
            self.executor = ThreadPoolExecutor(max_workers=self.pool_size)
        elif self.mode == 'processpool':
            self.executor = ProcessPoolExecutor(max_workers=self.pool_size)
                
    def run(self):
        logging.warning(f"server berjalan di ip address {self.ipinfo} mode={self.mode}")
        self.my_socket.bind(self.ipinfo)
        self.my_socket.listen(100)
        # Server timeout untuk stresstest
        self.my_socket.settimeout(5)

        try:
            while True:
                try:
                    self.connection, self.client_address = self.my_socket.accept()
                    logging.warning(f"connection from {self.client_address}")
                    # Pool executor
                    if self.mode in ['threadpool', 'processpool']:
                        self.executor.submit(handle_client_request, self.connection)
                    else:
                        clt = ProcessTheClient(self.connection, self.client_address)
                        clt.start()
                        self.the_clients.append(clt)
                except socket.timeout:
                    logging.warning("No connection in 5 seconds, shutting down server...")
                    break
        except KeyboardInterrupt:
            logging.warning("Server interrupted, shutting down...")
        except Exception as e:
            logging.error(f"Server error: {e}")
        finally:
            if self.executor:
                self.executor.shutdown(wait=True)
            self.my_socket.close()
            logging.warning("Server shutdown complete.")

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['thread', 'threadpool', 'processpool'], default='thread')
    parser.add_argument('--poolsize', type=int, default=5)
    args = parser.parse_args()
    svr = Server(ipaddress='0.0.0.0', mode=args.mode, pool_size=args.poolsize)
    svr.start()
    svr.join()

if __name__ == "__main__":
    main()