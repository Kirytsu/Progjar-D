#!/bin/bash
# Load Balancer Implementation with Multiple Backend Servers

# tes 1 game server 
python3 game_server.py 

# TODO Load Balancer, harus ada sinkronisasi state antar backend server
# Run 3 HTTP servers with different concurrency models
# echo "Starting backend servers..."
# python3 server/server_thread_http.py &        # Port 50001 - Multithread
# python3 server/server_thread_pool_http.py &   # Port 50002 - Thread Pool
# python3 server/server_process_pool_http.py &  # Port 50003 - Process Pool

# Wait for servers to start
# sleep 3

# echo "Starting Load Balancer..."
# Load Balancer routes game requests to master, others to all servers
# python3 server/lb.py &  # Port 44444
# wait
