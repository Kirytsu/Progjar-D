#!/bin/bash

# Run 3 HTTP servers with different concurrency models
echo "Starting backend servers..."
python3 server_thread_http.py &  # Port 50001 - Multithread
python3 server_process_pool_http.py &  # Port 50002 - Process Pool
python3 server_thread_pool_http.py &   # Port 50003 - Thread Pool


sleep 2
echo "Starting Load Balancer..."
python3 loadbalancer.py &  # Port 44444
wait
