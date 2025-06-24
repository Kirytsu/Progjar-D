# Server HTTP untuk Operasi File Sederhana

Implementasi server HTTP sederhana untuk melakukan operasi list directory server, upload file ke server, dan juga delete file dari server.

## Struktur Folder Tugas 4

- `http.py` - Kelas implementasi dari HTTP server
- `server_thread_pool_http.py` - Mendefinisikan server agar berjalan dengan thread pool 
- `server_process_pool_http.py` - Mendefinisikan server agar berjalan dengan process pool
- `client.py` - Implementasi client untuk membuat request ke HTTP server

## Format HTTP Request Percobaan pada Client

### List

```
GET /list HTTP/1.1
Host: hostname
Accept: */*

```

### Upload

```
POST /upload/{filename} HTTP/1.1
Host: hostname
Content-Type: application/json
Content-Length: [length]

{"filename": "{filename.txt}", "content": "{contentBase64==}"}
```

### Hapus File

```
DELETE /delete/{filename.txt} HTTP/1.1
Host: hostname
Accept: */*

```

## Status Code Response

- 200: Success
- 400: Bad Request
- 404: File Not Found
- 500: Internal Server Error