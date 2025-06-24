import sys
import socket
import json
import logging
import ssl
import os
import base64
import socket

# alamat server Mesin1
server_address = ('172.16.16.101', 50000)
# server_address = ('www.ietf.org',443)

def make_socket(destination_address='172.16.16.101', port=50000):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (destination_address, port)
        logging.warning(f"connecting to {server_address}")
        sock.connect(server_address)
        return sock
    except Exception as ee:
        logging.warning(f"error {str(ee)}")


def make_secure_socket(destination_address='localhost', port=50000):
    try:
        # get it from https://curl.se/docs/caextract.html
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.load_verify_locations(os.getcwd() + '/domain.crt')

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (destination_address, port)
        logging.warning(f"connecting to {server_address}")
        sock.connect(server_address)
        secure_socket = context.wrap_socket(sock, server_hostname=destination_address)
        logging.warning(secure_socket.getpeercert())
        return secure_socket
    except Exception as ee:
        logging.warning(f"error {str(ee)}")



def send_command(command_str, is_secure=False):
    alamat_server = server_address[0]
    port_server = server_address[1]
    #    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # gunakan fungsi diatas
    if is_secure == True:
        sock = make_secure_socket(alamat_server, port_server)
    else:
        sock = make_socket(alamat_server, port_server)

    # logging.warning(f"connecting to {server_address}")
    try:
        command_str += "\r\n"
        # logging.warning(f"sending message ")
        sock.sendall(command_str.encode())
        # logging.warning(command_str)
        data_received = "" 
        while True:
            data = sock.recv(2048)
            if data:
                data_received += data.decode()
                if "\r\n\r\n" in data_received:
                    break
            else:
                break
        hasil = data_received
        logging.warning("data received from server:")
        return hasil
    except Exception as ee:
        logging.warning(f"error during data receiving {str(ee)}")
        return False
    
def parse_http_response(response: str):
    try:
        headers, body = response.split("\r\n\r\n", 1)
        status_line = headers.split("\r\n")[0]
        status_code = int(status_line.split()[1])
        return status_code, body
    except Exception as e:
        print("Failed to parse HTTP response:", e)
        return None, None
    
def list_dir():
    response = send_command(f"GET /list{Header}")
    status_code, body = parse_http_response(response)
    if status_code != 200:
        return f"Failed to get server directory: HTTP {status_code}"
    try:
        body = response.split("\r\n\r\n", 1)[1].strip()
        dir = json.loads(body)
    except (IndexError, json.JSONDecodeError) as e:
        return f"Failed to parse JSON: {e}\nResponse:\n{repr(response)}"
    
    dirList = "Server Directory:\n"
    for file in dir['files']:
        dirList += f"- File: {file['name']}, Size: {file['size']} bytes\n"
    
    return dirList

def upload_file(filepath, host='localhost'):
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        return
    filename = os.path.basename(filepath)
    with open(filepath, 'rb') as f:
        content = base64.b64encode(f.read()).decode()
    
    # format konten file yang diupload dengan JSON
    data = json.dumps({
        'filename': filename,
        'content': content
    })
    request = (
        f"POST /upload HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        "Content-Type: application/json\r\n"
        f"Content-Length: {len(data)}\r\n"
        "\r\n"
        f"{data}"
    )
    
    response = send_command(request)
    status_code, body = parse_http_response(response)
    return f"Upload status: HTTP {status_code}\nResponse body: {body}"

def delete_file(filepath, host='localhost'):
    response = send_command(f"DELETE /delete/{filepath}")
    status_code, body = parse_http_response(response)
    return f"Delete status: HTTP {status_code}\nResponse body: {body}"
    
# Template untuk http header get, delete
ip_addr = socket.gethostbyname(socket.gethostname())
Header = f""" HTTP/1.1
Host: {server_address[0]}
User-Agent: {ip_addr}
Accept: */*
"""
        
if __name__ == '__main__':
    print("================Tes List File================")
    print(list_dir())
    
    print("================Tes Upload File tes.txt ke server================")
    print(upload_file('tes.txt'))
    
    print("================Tes List File================")
    print(list_dir())
    
    print("================Tes Delete File tes.txt dari server================")
    print(delete_file('tes.txt'))
    
    print("================Tes List File================")
    print(list_dir())