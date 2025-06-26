import socket
import json

class ClientInterface:
    # TO DO: Load Balancer
    def __init__(self, host='localhost', port=44444):
        self.host = host
        self.port = port
        self.player_id = None
        
    def send_request(self, endpoint):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((self.host, self.port))
            sock.send(f"GET {endpoint} HTTP/1.1\r\n\r\n".encode())
            response = b""
            while True:
                data = sock.recv(1024)
                if not data: break
                response += data
                if b"\r\n\r\n" in response: break
            sock.close()
            return json.loads(response.split(b"\r\n\r\n", 1)[1].decode()) if b"\r\n\r\n" in response else None
        except: 
            return None
    
    def join_game(self):
        result = self.send_request("/join_game")
        if result and result.get('status') == 'OK':
            self.player_id = result['player_id']
            return True, f"Joined as {self.player_id}"
        else:
            return False, "Failed to join"
    
    def get_game_state(self):
        result = self.send_request("/get_game_state")
        if result and result.get('status') == 'OK':
            return result['game_state']
        return None
    
    def start_game(self):
        self.send_request("/start_game")
    
    def draw_card(self, target_player, card_index):
        self.send_request(f"/draw_card/{self.player_id}/{target_player}/{card_index}")
    
    def leave_game(self):
        if self.player_id:
            self.send_request(f"/leave_game/{self.player_id}")
