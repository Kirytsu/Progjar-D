import socket
import json
import base64
import logging

server_address=('0.0.0.0',7777)

def send_command(command_str=""):
    global server_address
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_address)
    logging.warning(f"connecting to {server_address}")
    try:
        logging.warning(f"sending message ")
        command_data = command_str + "\r\n\r\n"
        sock.sendall(command_data.encode())
        # Look for the response, waiting until socket is done (no more data)
        data_received="" #empty string
        while True:
            #socket does not receive all data at once, data comes in part, need to be concatenated at the end of process
            data = sock.recv(1024)
            if data:
                #data is not empty, concat with previous content
                data_received += data.decode()
                if "\r\n\r\n" in data_received:
                    break
            else:
                # no more data, stop the process by break
                break
        # at this point, data_received (string) will contain all data coming from the socket
        # to be able to use the data_received as a dict, need to load it using json.loads()
        hasil = json.loads(data_received)
        logging.warning("data received from server:")
        return hasil
    except:
        logging.warning("error during data receiving")
        return False


def remote_list():
    command_str=f"LIST"
    hasil = send_command(command_str)
    if (hasil['status']=='OK'):
        print("Daftar file : ")
        for nmfile in hasil['data']:
            print(f"- {nmfile}")
        return True
    else:
        print("Gagal")
        return False

def remote_get(filename=""):
    command_str=f"GET {filename}"
    hasil = send_command(command_str)
    if (hasil['status']=='OK'):
        #proses file dalam bentuk base64 ke bentuk bytes
        namafile= hasil['data_namafile']
        isifile = base64.b64decode(hasil['data_file'])
        fp = open(namafile,'wb+')
        fp.write(isifile)
        fp.close()
        print(f"Berhasil mengambil {filename}")
        return True
    else:
        print("Gagal")
        return False

def remote_upload(filename=""):
    try:
        with open(filename, 'rb') as f:
            filedata = base64.b64encode(f.read()).decode()
            command_str = f"UPLOAD {filename} {filedata}"
            hasil = send_command(command_str)
            if (hasil['status']=='OK'):
                print(hasil['data'])
                return True
            else:
                print("Gagal")
                return False
    except Exception as e:
        print(f"Error: {e}")
        

def remote_delete(filename=""):
    command_str = f"DELETE {filename}"
    hasil = send_command(command_str)
    if (hasil['status']=='OK'):
        print(hasil['data'])
        return True
    else:
        print("Gagal")
        return False

if __name__=='__main__':
    server_address=('172.16.16.101',50000)
    remote_list()
    remote_get('pokijan.jpg')
    remote_get('donalbebek.jpg')
    remote_delete('donalbebek.jpg')
    remote_delete('pokijan.jpg')
    remote_list()
    remote_upload('donalbebek.jpg')
    # remote_upload('pokijan.jpg')
    remote_list()