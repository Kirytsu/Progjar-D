import json
import os
import socket
import threading
from datetime import datetime
from game_manager import GameManager

class HttpServer:
	def __init__(self):
		self.game_manager = GameManager()
	
	def response(self,kode=404,message='Not Found',messagebody=bytes(),headers={}):
		tanggal = datetime.now().strftime('%c')
		resp=[]
		resp.append("HTTP/1.0 {} {}\r\n" . format(kode,message))
		resp.append("Date: {}\r\n" . format(tanggal))
		resp.append("Connection: close\r\n")
		resp.append("Server: myserver/1.0\r\n")
		resp.append("Content-Length: {}\r\n" . format(len(messagebody)))
		for kk in headers:
			resp.append("{}:{}\r\n" . format(kk,headers[kk]))
		resp.append("\r\n")

		response_headers=''
		for i in resp:
			response_headers="{}{}" . format(response_headers,i)
		#menggabungkan resp menjadi satu string dan menggabungkan dengan messagebody yang berupa bytes
		#response harus berupa bytes
		#message body harus diubah dulu menjadi bytes
		if (type(messagebody) is not bytes):
			messagebody = messagebody.encode()

		response = response_headers.encode() + messagebody
		#response adalah bytes
		return response

	def proses(self,data):
		
		requests = data.split("\r\n")
		#print(requests)

		baris = requests[0]
		#print(baris)

		all_headers = [n for n in requests[1:] if n!='']

		j = baris.split(" ")
		try:
			method=j[0].upper().strip()
			if (method=='GET'):
				object_address = j[1].strip()
				return self.http_get(object_address, all_headers)
			else:
				return self.response(400,'Bad Request','',{})
		except IndexError:
			return self.response(400,'Bad Request','',{})

	def http_get(self,object_address,headers):
		with self.game_manager.lock:
			if (object_address == '/get_game_state'):
				data = json.dumps({'status': 'OK', 'game_state': self.game_manager.game_state})
				return self.response(200,'OK',data,{'Content-Type': 'application/json'})
			
			if (object_address == '/join_game'):
				success, result = self.game_manager.join_game()
				if success:
					data = json.dumps({'status': 'OK', 'player_id': result})
				else:
					data = json.dumps({'status': 'FAILED', 'message': result})
				return self.response(200,'OK',data,{'Content-Type': 'application/json'})
			
			if (object_address == '/start_game'):
				if self.game_manager.start_game():
					data = json.dumps({'status': 'OK'})
				else:
					data = json.dumps({'status': 'FAILED'})
				return self.response(200,'OK',data,{'Content-Type': 'application/json'})
			
			if object_address.startswith('/draw_card/'):
				parts = object_address.split('/')
				if len(parts) >= 4:
					player_id = parts[2]
					from_player = parts[3]
					card_index = int(parts[4]) if len(parts) >= 5 else None
					
					if self.game_manager.draw_card(player_id, from_player, card_index):
						data = json.dumps({'status': 'OK'})
					else:
						data = json.dumps({'status': 'FAILED'})
				else:
					data = json.dumps({'status': 'FAILED'})
				return self.response(200,'OK',data,{'Content-Type': 'application/json'})
			
			if object_address.startswith('/leave_game/'):
				parts = object_address.split('/')
				if len(parts) >= 3:
					player_id = parts[2]
					if self.game_manager.leave_game(player_id):
						data = json.dumps({'status': 'OK'})
					else:
						data = json.dumps({'status': 'FAILED'})
				else:
					data = json.dumps({'status': 'FAILED'})
				return self.response(200,'OK',data,{'Content-Type': 'application/json'})
		
		return self.response(404,'Not Found','',{})

def handle_client(client_socket, http_server):
	try:
		request = client_socket.recv(1024).decode()
		response = http_server.proses(request)
		client_socket.send(response)
	except:
		pass
	finally:
		client_socket.close()

if __name__ == "__main__":
	http_server = HttpServer()
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	server_socket.bind(('localhost', 44444))
	server_socket.listen(5)
	
	print("Game HTTP Server berjalan pada 44444")
	
	while True:
		client_socket, address = server_socket.accept()
		client_thread = threading.Thread(target=handle_client, args=(client_socket, http_server))
		client_thread.start()
