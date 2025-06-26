from socket import *
import socket
import time
import sys
import logging
import multiprocessing
from concurrent.futures import ProcessPoolExecutor

# Configure logging for load balancer
logging.basicConfig(level=logging.INFO, format='%(asctime)s - LB - %(message)s')

class BackendList:
	def __init__(self):
		self.servers=[]
		self.servers.append(('127.0.0.1', 50001)) # Multithread - GAME MASTER
		self.servers.append(('127.0.0.1', 50002)) # Thread Pool - File ops
		self.servers.append(('127.0.0.1', 50003)) # Process Pool - File ops
		self.current=1  # Start from index 1 for non-game requests
		self.game_master = 0  # Index 0 is always the game master
	
	def get_game_server(self):
		"""Always return the game master server for game operations"""
		s = self.servers[self.game_master]
		print(f"Game request -> {s}")
		return s
	
	def getserver(self): 
		"""Round Robin for non-game requests (files, etc.)"""
		s = self.servers[self.current]
		print(f"File request -> {s}")
		self.current = self.current + 1
		if (self.current >= len(self.servers)):
			self.current = 1  # Skip game master for round robin
		return s




def ProcessTheClient(connection,address,backend_sock,mode='toupstream'):
		try:
			while True:
				try:
					if (mode=='toupstream'):
						datafrom_client = connection.recv(1024)  # Increased buffer for HTTP requests
						if datafrom_client:
								backend_sock.sendall(datafrom_client)
						else:
								backend_sock.close()
								break
					elif (mode=='toclient'):
						datafrom_backend = backend_sock.recv(1024)  # Increased buffer for responses

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

def is_game_request(data):
	"""Check if the request is a game-related operation"""
	try:
		request_str = data.decode('utf-8', errors='ignore')
		game_endpoints = [
			'/get_game_state',
			'/join_game', 
			'/leave_game/',
			'/start_game',
			'/draw_card/',
			'/play_card/'
		]
		return any(endpoint in request_str for endpoint in game_endpoints)
	except:
		return False



def Server():
	the_clients = []
	my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	backend = BackendList()

	my_socket.bind(('0.0.0.0', 44444))
	my_socket.listen(1)
	
	print("Game-Aware Load Balancer started on port 44444")
	print("Game requests -> Server 50001 (Game Master)")
	print("File requests -> Servers 50002, 50003 (Round Robin)")

	with ProcessPoolExecutor(20) as executor:
		while True:
				connection, client_address = my_socket.accept()
				backend_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				backend_sock.settimeout(1)
				
				# Peek at the request to determine routing
				try:
					# Receive first chunk to analyze request
					first_data = connection.recv(1024, socket.MSG_PEEK)
					
					# Route based on request type
					if is_game_request(first_data):
						backend_address = backend.get_game_server()
						logging.warning(f"{client_address} -> GAME request -> {backend_address}")
					else:
						backend_address = backend.getserver()
						logging.warning(f"{client_address} -> FILE request -> {backend_address}")
				except:
					# Default to game server if can't determine
					backend_address = backend.get_game_server()
					logging.warning(f"{client_address} -> DEFAULT to game server -> {backend_address}")
				
				try:
					backend_sock.connect(backend_address)

					toupstream = executor.submit(ProcessTheClient, connection, client_address,backend_sock,'toupstream')
					toclient = executor.submit(ProcessTheClient, connection, client_address,backend_sock,'toclient')

					#menampilkan jumlah process yang sedang aktif
					jumlah = ['x' for i in the_clients if i.running()==True]
				except Exception as err:
					logging.error(err)
					pass

def main():
	Server()

if __name__=="__main__":
	main()
