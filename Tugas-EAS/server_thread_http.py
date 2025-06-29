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
		# HTTP keep-alive: handle multiple requests per connection
		buffer = b""
		self.connection.settimeout(10)
		while True:
			try:
				data = self.connection.recv(4096)
				if not data:
					break
				buffer += data
				while True:
					# Look for end of headers
					header_end = buffer.find(b"\r\n\r\n")
					if header_end == -1:
						break  # Not enough data for headers
					headers = buffer[:header_end].decode(errors="replace").split("\r\n")
					# Parse Content-Length
					content_length = 0
					for h in headers:
						if h.lower().startswith("content-length:"):
							try:
								content_length = int(h.split(":", 1)[1].strip())
							except:
								content_length = 0
					total_len = header_end + 4 + content_length
					if len(buffer) < total_len:
						break  # Wait for full body
					request_data = buffer[:header_end + 4 + content_length]
					# Process request (ignore body for GET)
					request_str = request_data[:header_end + 4].decode(errors="replace")
					hasil = httpserver.proses(request_str)
					# Send response (already includes headers and body)
					self.connection.sendall(hasil)
					# Remove processed request from buffer
					buffer = buffer[total_len:]
					# Check Connection header to see if we should close
					close_conn = False
					for h in headers:
						if h.lower().startswith("connection:") and "close" in h.lower():
							close_conn = True
					if close_conn:
						self.connection.close()
						return
			except socket.timeout:
				break
			except Exception as e:
				# logging.warning(f"Exception: {e}")
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
