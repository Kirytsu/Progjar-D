import json
import os
import sys
import uuid
from datetime import datetime
from glob import glob
from datetime import datetime
from game_manager import GameManager

class HttpServer:
    def __init__(self, shared_state=None):
        self.game_manager = GameManager(shared_state=shared_state)
        self.types = {
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.html': 'text/html',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.gif': 'image/gif'
        }
    
    def response(self,kode=404,message='Not Found',messagebody=bytes(),headers={}):
        tanggal = datetime.now().strftime('%c')
        resp=[]
        resp.append("HTTP/1.1 {} {}\r\n" . format(kode,message))
        resp.append("Date: {}\r\n" . format(tanggal))
        resp.append("Connection: keep-alive\r\n")
        resp.append("Server: gameserver/1.1\r\n")
        resp.append("Content-Length: {}\r\n" . format(len(messagebody)))
        for kk in headers:
            resp.append("{}:{}\r\n" . format(kk,headers[kk]))
        resp.append("\r\n")

        response_headers=''
        for i in resp:
            response_headers="{}{}" . format(response_headers,i)

        if (type(messagebody) is not bytes):
            messagebody = messagebody.encode()

        response = response_headers.encode() + messagebody
        return response

    def proses(self,data):
        requests = data.split("\r\n")
        baris = requests[0]
        all_headers = [n for n in requests[1:] if n!='']

        j = baris.split(" ")
        try:
            method=j[0].upper().strip()
            if (method=='GET'):
                object_address = j[1].strip()
                return self.http_get(object_address, all_headers)
            else:
                return self.response(400,'Bad Request','',{})
        except IndexError:
            return self.response(400,'Bad Request','',{})

    def http_get(self,object_address,headers):
        files = glob('./*')
        thedir='./'
  
        # Simple URLs
        if (object_address == '/'):
            return self.response(200,'OK','Ini Adalah web Server percobaan',dict())
        if (object_address == '/video'):
            return self.response(302,'Found','',dict(location='https://youtu.be/katoxpnTf04'))
        if (object_address == '/santai'):
            return self.response(200,'OK','santai saja',dict())
  
        # Handle client HTTP requests
        lock = getattr(self.game_manager, 'lock', None) or getattr(self.game_manager, 'shared_lock', None)
        with lock:
            if (object_address == '/get_game_state'):
                # Convert shared state to regular Python objects for JSON serialization
                game_state_dict = self._prepare_game_state_for_json()
                data = json.dumps({'status': 'OK', 'game_state': game_state_dict})
                return self.response(200,'OK',data,{'Content-Type': 'application/json'})
            
            if (object_address == '/join_game'):
                success, result = self.game_manager.join_game()
                if success:
                    data = json.dumps({'status': 'OK', 'player_id': result})
                else:
                    data = json.dumps({'status': 'FAILED', 'message': result})
                return self.response(200,'OK',data,{'Content-Type': 'application/json'})
            
            if (object_address == '/start_game'):
                if self.game_manager.start_game():
                    data = json.dumps({'status': 'OK'})
                else:
                    data = json.dumps({'status': 'FAILED'})
                return self.response(200,'OK',data,{'Content-Type': 'application/json'})

            if (object_address == '/restart_game'):
                if self.game_manager.restart_game():
                    data = json.dumps({'status': 'OK'})
                else:
                    data = json.dumps({'status': 'FAILED'})
                return self.response(200,'OK',data,{'Content-Type': 'application/json'})

            if object_address.startswith('/draw_card/'):
                parts = object_address.split('/')
                if len(parts) >= 4:
                    player_id = parts[2]
                    from_player = parts[3]
                    card_index = int(parts[4]) if len(parts) >= 5 else None

                    if self.game_manager.draw_card(player_id, from_player, card_index):
                        data = json.dumps({'status': 'OK'})
                    else:
                        data = json.dumps({'status': 'FAILED'})
                else:
                    data = json.dumps({'status': 'FAILED'})
                return self.response(200,'OK',data,{'Content-Type': 'application/json'})

            if object_address.startswith('/leave_game/'):
                parts = object_address.split('/')
                if len(parts) >= 3:
                    player_id = parts[2]
                    if self.game_manager.leave_game(player_id):
                        data = json.dumps({'status': 'OK'})
                    else:
                        data = json.dumps({'status': 'FAILED'})
                else:
                    data = json.dumps({'status': 'FAILED'})
                return self.response(200,'OK',data,{'Content-Type': 'application/json'})
  
        # Static files
        object_address=object_address[1:]
        if thedir+object_address not in files:
            return self.response(404,'Not Found','',{})
        fp = open(thedir+object_address,'rb')
        isi = fp.read()
        
        fext = os.path.splitext(thedir+object_address)[1]
        content_type = self.types.get(fext, 'application/octet-stream')
        
        headers={}
        headers['Content-type']=content_type
        
        return self.response(200,'OK',isi,headers)
    
    def _prepare_game_state_for_json(self):
        """Convert shared state objects to regular Python objects for JSON serialization"""
        game_state = self.game_manager.game_state
        result = {}
        
        # Handle players list
        if 'players' in game_state:
            result['players'] = list(game_state['players'])
        
        # Handle events list
        if 'events' in game_state:
            result['events'] = list(game_state['events'])
        
        # Handle cards dictionary
        if 'cards' in game_state:
            cards_dict = {}
            for player_id, cards in game_state['cards'].items():
                cards_dict[player_id] = list(cards) if hasattr(cards, '__iter__') else cards
            result['cards'] = cards_dict
        
        # Handle simple values
        for key in ['current_turn', 'status']:
            if key in game_state:
                result[key] = game_state[key]
        
        return result