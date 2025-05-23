import socket
import json
import base64
import logging
import argparse
import sys

server_address = ('127.0.0.1', 50000)

def send_command(command_str=""):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(server_address)
        command_str += "\r\n\r\n"
        sock.sendall(command_str.encode())

        data_received = ""
        while True:
            data = sock.recv(1024)
            if data:
                data_received += data.decode()
                if data_received.endswith("\r\n\r\n"):
                    data_received = data_received[:-4] 
                    break
            else:
                break
        hasil = json.loads(data_received)
        return hasil
    except Exception as e:
        return {"status": "ERROR", "data": str(e)}

def remote_list():
    return send_command("LIST")

def remote_download(filename=""):
    result = send_command(f"GET {filename}")
    if result['status'] == 'OK':
        with open(result['data_namafile'], 'wb') as f:
            f.write(base64.b64decode(result['data_file']))
    return result

def remote_upload(filename=""):
    try:
        with open(filename, 'rb') as f:
            filedata = base64.b64encode(f.read()).decode()
        return send_command(f"UPLOAD {filename} {filedata}")
    except Exception as e:
        return {"status": "ERROR", "data": f"Upload failed: {e}"}

def remote_delete(filename=""):
    return send_command(f"DELETE {filename}")

def task(action, filename=None):
    if action == 'list':
        return remote_list()
    elif action == 'download' and filename:
        return remote_download(filename)
    elif action == 'upload' and filename:
        return remote_upload(filename)
    elif action == 'delete' and filename:
        return remote_delete(filename)
    else:
        return {"status": "ERROR", "data": "Invalid action or missing filename"}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--operation', choices=['download', 'upload', 'list', 'delete'], required=True)
    parser.add_argument('--files', nargs='*')
    args = parser.parse_args()

    if args.operation == 'list':
        result = task('list')
        print(json.dumps(result))
    elif args.operation in ['download', 'upload', 'delete']:
        if not args.files:
            print(json.dumps({"status": "ERROR", "data": "Missing files"}))
            sys.exit(1)
        for f in args.files:
            result = task(args.operation, f)
            print(json.dumps(result))
    else:
        print(json.dumps({"status": "ERROR", "data": "Invalid command"}))

if __name__ == '__main__':
    main()
