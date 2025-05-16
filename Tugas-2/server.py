from socket import *
import socket
import threading
import logging
import time
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

def process_request(msg):
        # Connection status (1) to continue (0) to stop
        status = 1
        if (msg.startswith("TIME") and msg.endswith("\r\n")):
                wib_tz = ZoneInfo("Asia/Jakarta")
                now_utc = datetime.now(ZoneInfo("UTC"))
                now_wib = now_utc.astimezone(wib_tz)
                cur_time = now_wib.strftime("JAM %H:%M:%S")
                resp = f"{cur_time}\r\n"

                if (msg.endswith("QUIT\r\n")):
                        status = 0
                        resp += f"Closing connection...\r\n"
        else:
                resp = "Unknownn command\r\n"
        return resp, status

class ProcessTheClient(threading.Thread):
        def __init__(self,connection,address):
                self.connection = connection
                self.address = address
                threading.Thread.__init__(self)

        def run(self):
                while True:
                        data = self.connection.recv(32)
                        if data:
                                req_msg = data.decode()
                                logging.warning(f"{self.address[0]} Port {self.address[1]} : {data}")
                                response, status = process_request(req_msg)
                                self.connection.sendall(response.encode())

                                if (status == 0):
                                        break
                        else:
                                break
                self.connection.close()
                logging.warning(f"Connection to {self.address[0]} Port {self.address[1]} closed")

class Server(threading.Thread):
        def __init__(self):
                self.the_clients = []
                self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                threading.Thread.__init__(self)

        def run(self):
                self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.my_socket.bind(('0.0.0.0', 45000))
                logging.warning(f"Server listen at port 45000")
                self.my_socket.listen(1)
                while True:
                        self.connection, self.client_address = self.my_socket.accept()
                        logging.warning(f"connection from {self.client_address}")

                        clt = ProcessTheClient(self.connection, self.client_address)
                        clt.start()
                        self.the_clients.append(clt)
                        
def main():
        svr = Server()
        svr.start()

if __name__=="__main__":
        main()