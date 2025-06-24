import sys
import os.path
import uuid
import json
import base64
from glob import glob
from datetime import datetime

class HttpServer:
	def __init__(self):
		self.sessions={}
		self.types={}
		self.types['.pdf']='application/pdf'
		self.types['.jpg']='image/jpeg'
		self.types['.txt']='text/plain'
		self.types['.html']='text/html'
		self.file_dir = './files'
		os.makedirs(self.file_dir, exist_ok=True)
	
	# Function to upload file
	def upload_file(self, filename, content_b64):
		try:
			file_data = base64.b64decode(content_b64)
			with open(os.path.join(self.file_dir, filename), 'wb') as f:
				f.write(file_data)
			return True
		except:
			return False

	# Function to delete file
	def delete_file(self, filename):
		try:
			os.remove(os.path.join(self.file_dir, filename))
			return True
		except:
			return False

	def response(self,kode=404,message='Not Found',messagebody=bytes(),headers={}):
		tanggal = datetime.now().strftime('%c')
		resp=[]
		resp.append("HTTP/1.1 {} {}\r\n" . format(kode,message))
		resp.append("Date: {}\r\n" . format(tanggal))
		resp.append("Connection: close\r\n")
		resp.append("Server: myserver/1.1\r\n")
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

	def proses(self, data):
		# Split headers and body
		print(data)
		header_body_split = data.split("\r\n\r\n", 1)
		header_part = header_body_split[0]
		body = header_body_split[1] if len(header_body_split) > 1 else ""
		requests = header_part.split("\r\n")

		baris = requests[0]

		all_headers = [n for n in requests[1:] if n != '']

		j = baris.split(" ")
		try:
			method = j[0].upper().strip()
			object_address = j[1].strip()
			if method == 'GET':
				return self.http_get(object_address, all_headers)
			elif method == 'POST':
				return self.http_post(object_address, all_headers, body)
			elif method == 'DELETE':
				return self.http_delete(object_address, all_headers)
			else:
				return self.response(400, 'Bad Request', '', {})
		except IndexError:
			return self.response(400, 'Bad Request', '', {})	


    # method=='GET'
	def http_get(self,object_address,headers):
		files = glob('./files/*')
		#print(files)
		thedir='./'
		if (object_address == '/'):
			return self.response(200,'OK','Ini Adalah web Server percobaan',dict())

		elif (object_address == '/video'):
			return self.response(302,'Found','',dict(location='https://youtu.be/katoxpnTf04'))
		elif (object_address == '/santai'):
			return self.response(200,'OK','santai saja',dict())
		# Isi directory melalui /list
		elif (object_address == '/list'):
			file_dir = './files'
			os.makedirs(file_dir, exist_ok=True)
			files_list = []
			for f in os.listdir(file_dir):
				if os.path.isfile(os.path.join(file_dir, f)):
					files_list.append({
						'name': f,
						'size': os.path.getsize(os.path.join(file_dir, f))
					})
			response_data = json.dumps({'files': files_list})
			return self.response(200, 'OK', response_data, {'Content-type': 'application/json'})

		object_address=object_address[1:]
		if thedir+object_address not in files:
			return self.response(404,'Not Found','',{})
		fp = open(thedir+object_address,'rb') #rb => artinya adalah read dalam bentuk binary
		#harus membaca dalam bentuk byte dan BINARY
		isi = fp.read()
		
		fext = os.path.splitext(thedir+object_address)[1]
		content_type = self.types[fext]
		
		headers={}
		headers['Content-type']=content_type
		
		return self.response(200,'OK',isi,headers)

	# method=='POST'
	def http_post(self, object_address, headers, body):
		if object_address == '/upload':
			try:
				# Parse JSON body
				data = json.loads(body)
				filename = data.get('filename')
				content = data.get('content')
				if self.upload_file(filename, content):
					return self.response(200, 'OK', json.dumps({'status': 'success'}), {'Content-Type': 'application/json'})
			except Exception as e:
				return self.response(500, 'Internal Server Error', json.dumps({'status': 'error', 'message': str(e)}), {'Content-Type': 'application/json'})
		else:
			return self.response(400, 'Bad Request', json.dumps({'status': 'error', 'message': 'Invalid POST endpoint'}), {'Content-Type': 'application/json'})

	# method=='DELETE'
	def http_delete(self,object_address,headers):
		if object_address.startswith('/delete/'):
			# parsing nama file setelah /delete/
			filename = object_address[8:] 
			if self.delete_file(filename):
				return self.response(200, 'OK', json.dumps({'status': 'success'}), {'Content-Type': 'application/json'})
			else:
				return self.response(404, 'Not Found', json.dumps({'status': 'error'}), {'Content-Type': 'application/json'})
		return self.response(400, 'Bad Request', 'Invalid delete request', {})

if __name__=="__main__":
	httpserver = HttpServer()
	d = httpserver.proses('GET testing.txt HTTP/1.0')
	print(d)
	d = httpserver.proses('GET donalbebek.jpg HTTP/1.0')
	print(d)