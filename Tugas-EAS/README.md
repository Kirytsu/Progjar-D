# Old Maid Game Server-Client System

This project implements a simple Old Maid card game using Python. It features a client-server architecture with load balancing, process/thread pools, and simple HTTP-based message protocol with TCP/IP.

## Folder Structure

- `game_client.py` — Client interface to connect and sending HTTP request to game server.
- `game_server.py` — Main HTTP game server logic.
- `game_manager.py` — Game state and player management.
- `oldmaid_logic.py` — Core Old Maid game logic.
- `game_ui.py` — GUI for the player to start the game.
- `loadbalancer.py` — Load balancer to distribute clients into available backend servers using round robin.
- `server_process_pool_http.py` — Server using a process pool for handling clients.
- `server_thread_http.py` — Server using multi-threading for handling clients.
- `server_thread_pool_http.py` — Server using a thread pool for handling clients.
- `assets/` — Card image assets for the game UI.
- `killPort.sh` — Utility scripts to kill python process that run at backend server port.
- `runServer.sh` — Utility scripts to run all available backend server and load balancer.

## How to Run

1. **Start backend server and load balancer :** 
   - `bash runServer.sh`

2. **Start the client :**
   - `python game_ui.py`


## Features

- Multiple backend server implementations (multithread/process pool/thread pool)
- Load balancing for client connections
- Persistent HTTP connection (1 TCP socket per client)
- Game state management on each backend server
- Card assets for UI

## Requirements

- Python 3.8+
- Pygame for gameUI: `pip install pygame`

## Note

- Each server could only hold up to 6 players.
- Need minimum 2 players to start the game. 
- Each connection will be distributed using round robin. May need to run 4 client to start the first game. 