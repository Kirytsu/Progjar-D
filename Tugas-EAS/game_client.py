import socket
import json
import logging

class ClientInterface:
    
    # Connect to load balancer
    def __init__(self, host='localhost', port=44444):
        self.server_address = (host, port)
        self.player_id = None
        # Creating TCP Socket 
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(self.server_address)
    
    def send_command(self,command_str=""):
        # Format HTTP request 
        request = (
            f"GET {command_str} HTTP/1.1\r\n"
            f"Host: {self.server_address[0]}\r\n"
            f"Connection: keep-alive\r\n"
            f"User-Agent: gameclient/1.1\r\n"
            f"\r\n"
        )
        # logging.warning(f"connecting to {self.server_address}")
        try:
            self.sock.sendall(request.encode())
            # Look for the response, waiting until socket is done (no more data)
            data_received = "" #empty string
            while True:
                #socket does not receive all data at once, data comes in part, need to be concatenated at the end of process
                data = self.sock.recv(1024)
                if data:
                    #data is not empty, concat with previous content
                    data_received += data.decode()
                    if data_received.endswith("\r\n\r\n"):
                        break
                else:
                    # no more data, stop the process by break
                    break
            # at this point, data_received (string) will contain all data coming from the socket
            # to be able to use the data_received as a dict, need to load it using json.loads()
            hasil = json.loads(data_received.split("\r\n\r\n", 1)[1])
            # logging.warning("data received from server:")
            return hasil
        except Exception as e:
            logging.warning(f"error during data receiving {e}")
            return False
    
    def join_game(self):
        result = self.send_command("/join_game")
        if result and result.get('status') == 'OK':
            self.player_id = result['player_id']
            return True, f"Joined as {self.player_id}"
        else:
            return False, "Failed to join"
    
    def get_game_state(self):
        result = self.send_command("/get_game_state")
        if result and result.get('status') == 'OK':
            return result['game_state']
        return None
    
    def start_game(self):
        self.send_command("/start_game")
    
    def draw_card(self, target_player, card_index):
        self.send_command(f"/draw_card/{self.player_id}/{target_player}/{card_index}")
    
    def leave_game(self):
        if self.player_id:
            self.send_command(f"/leave_game/{self.player_id}")
    
    def restart_game(self):
        """Request to restart the game"""
        result = self.send_command("/restart_game")
        if result and result.get('status') == 'OK':
            return True
        return False
