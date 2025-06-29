import threading
import time
import random
from collections import defaultdict
from oldmaid_logic import create_deck, deal_cards, remove_pairs

class GameManager:
    def __init__(self):
        self.game_state = {
            'players': [],
            'cards': {},
            'current_turn': None,
            'status': 'waiting',
            'events': []
        }
        self.lock = threading.Lock()

    def join_game(self):
        """Add a player to the game"""
        if len(self.game_state['players']) >= 6:
            return False, 'Game full'
        
        player_id = f"Player{len(self.game_state['players']) + 1}"
        if player_id not in self.game_state['players']:
            self.game_state['players'].append(player_id)
            self.game_state['cards'][player_id] = []
            
            if self.game_state['status'] == 'playing':
                # Player joins as spectator during active game
                self.game_state['events'].append(f"{player_id} joined as spectator ({len(self.game_state['players'])}/6)")
            else:
                # Player joins normally when game is waiting
                self.game_state['events'].append(f"{player_id} joined ({len(self.game_state['players'])}/6)")
                
        return True, player_id

    def start_game(self):
        """Start the game if enough players"""
        if len(self.game_state['players']) < 2 or self.game_state['status'] != 'waiting':
            return False
        
        # Get players who can participate (those who joined before game starts)
        active_players = [p for p in self.game_state['players'] if self.game_state['cards'][p] == []]
        
        if len(active_players) < 2:
            return False
        
        # Only deal cards to active players, spectators keep empty cards
        deck = create_deck()
        hands = deal_cards(deck, active_players)
        
        # Clear all cards first
        for player in self.game_state['players']:
            self.game_state['cards'][player] = []
            
        # Check players hand, then remove pairs
        for player in active_players:
            self.game_state['cards'][player] = remove_pairs(hands[player])
        
        self.game_state['current_turn'] = active_players[0]
        self.game_state['status'] = 'playing'
        self.game_state['events'].append("Game started!")
        return True

    def draw_card(self, player_id, from_player, card_index=None):
        """Handle card drawing"""
        if (self.game_state['current_turn'] != player_id or 
            not self.game_state['cards'][from_player]):
            return False
        
        # Draw card
        if card_index is not None:
            card = self.game_state['cards'][from_player][card_index]
        else:
            card = random.choice(self.game_state['cards'][from_player])
        self.game_state['cards'][from_player].remove(card)
        self.game_state['cards'][player_id].append(card)
        
        # Randomize the player's hand after drawing
        random.shuffle(self.game_state['cards'][player_id])
        self.game_state['cards'][player_id] = remove_pairs(self.game_state['cards'][player_id])
        
        # Next turn - skip players with no cards
        self._next_turn(player_id)
        
        # Check win
        if self._check_game_end():
            self.game_state['status'] = 'finished'  
            self.game_state['current_turn'] = None
            # Showing game results for 5 secs, before reset
            self._schedule_reset(5)  
        
        return True

    def leave_game(self, player_id):
        """Remove player from game"""
        if player_id not in self.game_state['players']:
            return False
        
        self.game_state['players'].remove(player_id)
        if player_id in self.game_state['cards']:
            del self.game_state['cards'][player_id]
        self.game_state['events'].append(f"{player_id} left")
        
        # Reset if game was in progress
        if self.game_state['status'] == 'playing':
            self._reset_to_waiting()
            self.game_state['events'].append("Game reset - player left during game")
        
        return True

    def _next_turn(self, current_player):
        """Find next player with cards"""
        current_idx = self.game_state['players'].index(current_player)
        next_player = None
        for i in range(1, len(self.game_state['players'])):
            next_idx = (current_idx + i) % len(self.game_state['players'])
            next_candidate = self.game_state['players'][next_idx]
            if self.game_state['cards'][next_candidate]:
                next_player = next_candidate
                break
        self.game_state['current_turn'] = next_player

    def _check_game_end(self):
        """Check if game should end"""
        players_with_cards = [p for p, c in self.game_state['cards'].items() if c]
        if len(players_with_cards) <= 1:
            if players_with_cards:
                # Find Old Maid
                old_maid_player = players_with_cards[0]
                old_maid_card = None
                for card in self.game_state['cards'][old_maid_player]:
                    if '_Q' in card:
                        old_maid_card = card
                        break
                
                if old_maid_card:
                    self.game_state['events'].append(f"{old_maid_player} is the Old Maid with {old_maid_card}!")
                else:
                    self.game_state['events'].append(f"{old_maid_player} wins!")
            else:
                self.game_state['events'].append("Game Over!")
            return True
        return False

    def _reset_to_waiting(self):
        """Reset game to waiting state"""
        self.game_state['status'] = 'waiting'
        self.game_state['current_turn'] = None
        # Clear all cards for all players (including spectators who can now join next game)
        for player in self.game_state['players']:
            self.game_state['cards'][player] = []
        self.game_state['events'].append("Press Space to Start!")

    def _schedule_reset(self, delay):
        """Schedule game reset after delay"""
        def reset_after_delay():
            time.sleep(delay)
            with self.lock:
                self._reset_to_waiting()
        
        reset_thread = threading.Thread(target=reset_after_delay)
        reset_thread.daemon = True
        reset_thread.start()

    def restart_game(self):
        """Manually restart the game (can be called when game is finished)"""
        if self.game_state['status'] == 'finished':
            self._reset_to_waiting()
            return True
        return False
