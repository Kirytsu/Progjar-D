import json
import logging

from file_interface import FileInterface

"""
* class FileProtocol bertugas untuk memproses 
data yang masuk, dan menerjemahkannya apakah sesuai dengan
protokol/aturan yang dibuat

* data yang masuk dari client adalah dalam bentuk bytes yang 
pada akhirnya akan diproses dalam bentuk string

* class FileProtocol akan memproses data yang masuk dalam bentuk
string
"""



class FileProtocol:
    def __init__(self):
        self.file = FileInterface()
    def proses_string(self, string_datamasuk=''):
        # logging.warning(f"string diproses: {string_datamasuk}")
        try:
            # Split tidak lagi menggunakan shlex karena cenderung akan rusak pada 
            # data dengan ukuran besar misalnya isi file
            if string_datamasuk.startswith('UPLOAD'):
                command, rest = string_datamasuk.split(' ', 1)
                filename, filedata = rest.split(' ', 1)
                params = [filename, filedata]
                logging.warning(f"Processing request: {command} {filename}")
                cl = getattr(self.file, command.lower())(params)
                return json.dumps(cl)
            else:
                c = string_datamasuk.strip().split()
                command = c[0].lower()
                params = c[1:]
                logging.warning(f"Processing request: {command} {params}")
                cl = getattr(self.file, command)(params)
                return json.dumps(cl)
        except Exception as e:
            logging.error(f"Error processing string: {e}")
            return json.dumps(dict(status='ERROR', data='request tidak dikenali'))

if __name__=='__main__':
    #contoh pemakaian
    fp = FileProtocol()
    print(fp.proses_string("LIST"))
    print(fp.proses_string("GET pokijan.jpg"))
