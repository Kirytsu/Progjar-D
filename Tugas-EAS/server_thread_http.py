from socket import *
import socket
import time
import sys
import logging
import threading
from game_server import HttpServer

httpserver = HttpServer()

class ProcessTheClient(threading.Thread):
	"""Class untuk menangani client dengan threading"""
	def __init__(self, connection, address):
		threading.Thread.__init__(self)
		self.connection = connection
		self.address = address

	def run(self):
		self.connection.settimeout(5) 
		rcv = ""
		while True:
			try:
				data = self.connection.recv(32)
				if data:
					# merubah input dari socket (berupa bytes) ke dalam string
					# agar bisa mendeteksi \r\n
					d = data.decode()
					rcv = rcv + d
					if rcv[-2:] == '\r\n':
						# end of command, proses string
						# logging.warning("data dari client: {}" . format(rcv))
						hasil = httpserver.proses(rcv)
						# hasil akan berupa bytes
						# untuk bisa ditambahi dengan string, maka string harus di encode
						hasil = hasil + "\r\n\r\n".encode()
						# logging.warning("balas ke  client: {}" . format(hasil))
						# hasil sudah dalam bentuk bytes
						self.connection.sendall(hasil)
						rcv = ""
						# self.connection.close()
						# return
				else:
					break	
			except OSError as e:
				self.connection.close()
				break
		self.connection.close()
		return

def Server():
	the_clients = []
	my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

	my_socket.bind(('0.0.0.0', 50001))
	my_socket.listen(1)
	print("Server berjalan dengan multithread di port 50001")
	while True:
		connection, client_address = my_socket.accept()
		# logging.warning("connection from {}".format(client_address))
		p = ProcessTheClient(connection, client_address)
		p.start()
		the_clients.append(p)
		# membersihkan thread yang sudah selesai dan menampilkan jumlah thread yang sedang aktif
		the_clients = [t for t in the_clients if t.is_alive()]
		jumlah = ['x' for i in the_clients if i.is_alive()]
		print(jumlah)

def main():
	Server()

if __name__=="__main__":
	main()