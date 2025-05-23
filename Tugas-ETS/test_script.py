import time
import csv
import os
import subprocess
import signal
import json
from concurrent.futures import ThreadPoolExecutor
from itertools import product

# Kombinasi parameter 2*3*3*3 = 54
operations = ['upload', 'download']
volumes = ['10MB', '50MB', '100MB']
client_workers = [1, 5, 50]
server_workers = [1, 5, 50]

volume_bytes = {
    '10MB': 10 * 1024 * 1024,
    '50MB': 50 * 1024 * 1024,
    '100MB': 100 * 1024 * 1024,
}

file_map = {
    '10MB': 'dummy_10MB.dat',
    '50MB': 'dummy_50MB.dat',
    '100MB': 'dummy_100MB.dat',
}

# Create dummy files
for volume, filename in file_map.items():
    if not os.path.exists(filename):
        with open(filename, 'wb') as f:
            f.write(os.urandom(volume_bytes[volume]))

def run_stress_test(mode_server):
    output_filename = f"{mode_server}_result.csv"

    with open(output_filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            'Nomor', 'Operasi', 'Volume', 'Jumlah client worker pool', 'Jumlah server worker pool',
            'Waktu total per client (s)', 'Throughput per client (Bps)',
            'Jumlah request sukses', 'Jumlah request gagal'
        ])

        nomor = 1
        for operation, volume, client_pool, server_pool in product(operations, volumes, client_workers, server_workers):
            print(f"[#{nomor}] Testing: {operation} - {volume} - client:{client_pool} - server:{server_pool}...")

            # Start server
            server_cmd = [
                'python3', 'file_server.py',
                '--mode', mode_server,
                '--poolsize', str(server_pool)
            ]
            server_process = subprocess.Popen(server_cmd)
            time.sleep(1)

            start_time = time.time()
            pool = ThreadPoolExecutor(max_workers=client_pool)
            futures = []

            for _ in range(client_pool):
                files = [file_map[volume]]
                cmd = [
                    'python3', 'file_client_cli.py',
                    '--operation', operation,
                    '--files'
                ] + files

                futures.append(pool.submit(subprocess.run, cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE))

            request_success = 0
            for future in futures:
                result = future.result()
                stdout = result.stdout.decode().strip()
                # print(stdout)

                try:
                    # Parsing JSON response dictionary
                    response = next(
                        json.loads(line)
                        for line in reversed(stdout.splitlines())
                        if line.startswith('{') and line.endswith('}')
                    )
                    # Cek status response
                    if response.get("status") == "OK":
                        request_success += 1
                    else:
                        print(f"[ERROR] Operation failed")
                except Exception as e:
                    print(f"[ERROR] Could not parse response")
                    
            # total time dan throughput tidak dibagi jumlah client karena konkuren
            total_time = (time.time() - start_time)
            throughput = (volume_bytes[volume] / total_time) if total_time > 0 else 0        
            server_process.wait()
            request_failed = client_pool - request_success

            writer.writerow([
                nomor, operation, volume, client_pool, server_pool,
                round(total_time, 2), round(throughput, 2),
                request_success, request_failed
            ])

            nomor += 1

if __name__ == '__main__':
    # Run stress test dipisah dengan 2 mode server {multithreading pool dan multiprocessing pool} 
    run_stress_test('threadpool')
    run_stress_test('processpool')  
