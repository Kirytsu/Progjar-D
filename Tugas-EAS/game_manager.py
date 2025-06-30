import threading
import time
import random
import multiprocessing
from collections import defaultdict
from oldmaid_logic import create_deck, deal_cards, remove_pairs

class GameManager:
    def __init__(self, shared_state=None):
        if shared_state is not None:
            # Using shared memory for multiprocessing
            self.game_state = shared_state
            self.shared_lock = multiprocessing.Lock()
            self.use_shared_memory = True
        else:
            # Using local memory for threading
            self.game_state = {
                'players': [],
                'cards': {},
                'current_turn': None,
                'status': 'waiting',
                'events': []
            }
            self.lock = threading.Lock()
            self.use_shared_memory = False

    def join_game(self):
        if len(self.game_state['players']) >= 6:
            return False, 'Game full'
        
        player_id = f"Player{len(self.game_state['players']) + 1}"
        
        if self.use_shared_memory:
            # For shared memory, we need to modify lists and dicts specially
            if player_id not in list(self.game_state['players']):
                # Get current players list and modify it
                players_list = list(self.game_state['players'])
                players_list.append(player_id)
                self.game_state['players'] = players_list
                
                # Update cards dictionary
                cards_dict = dict(self.game_state['cards'])
                cards_dict[player_id] = []
                self.game_state['cards'] = cards_dict
                
                # Add event
                events_list = list(self.game_state['events'])
                if self.game_state['status'] == 'playing':
                    events_list.append(f"{player_id} joined as spectator ({len(players_list)}/6)")
                else:
                    events_list.append(f"{player_id} joined ({len(players_list)}/6)")
                self.game_state['events'] = events_list
        else:
            # Regular memory operations
            if player_id not in self.game_state['players']:
                self.game_state['players'].append(player_id)
                self.game_state['cards'][player_id] = []
                
                if self.game_state['status'] == 'playing':
                    self.game_state['events'].append(f"{player_id} joined as spectator ({len(self.game_state['players'])}/6)")
                else:
                    self.game_state['events'].append(f"{player_id} joined ({len(self.game_state['players'])}/6)")
                
        return True, player_id

    def start_game(self):
        if len(self.game_state['players']) < 2 or self.game_state['status'] != 'waiting':
            return False
        
        # Get active players
        players_list = list(self.game_state['players'])
        cards_dict = dict(self.game_state['cards'])
        active_players = [p for p in players_list if not cards_dict.get(p, [])]
        
        if len(active_players) < 2:
            return False
        
        # Create and deal cards
        deck = create_deck()
        hands = deal_cards(deck, active_players)
        
        # Update cards for all players
        new_cards_dict = {}
        for player in players_list:
            new_cards_dict[player] = []
        
        for player in active_players:
            new_cards_dict[player] = remove_pairs(hands[player])
        
        # Update shared state
        if self.use_shared_memory:
            self.game_state['cards'] = new_cards_dict
            self.game_state['current_turn'] = active_players[0]
            self.game_state['status'] = 'playing'
            
            # Add event
            events_list = list(self.game_state['events'])
            events_list.append("Game started!")
            self.game_state['events'] = events_list
        else:
            self.game_state['cards'] = new_cards_dict
            self.game_state['current_turn'] = active_players[0]
            self.game_state['status'] = 'playing'
            self.game_state['events'].append("Game started!")
        
        return True

    def draw_card(self, player_id, from_player, card_index=None):
        cards_dict = dict(self.game_state['cards'])
        
        if (self.game_state['current_turn'] != player_id or 
            not cards_dict.get(from_player, [])):
            return False
        
        # Get cards
        from_player_cards = list(cards_dict.get(from_player, []))
        player_cards = list(cards_dict.get(player_id, []))
        
        if not from_player_cards:
            return False
        
        # Draw card
        if card_index is not None and 0 <= int(card_index) < len(from_player_cards):
            card = from_player_cards[int(card_index)]
        else:
            card = random.choice(from_player_cards)
        
        from_player_cards.remove(card)
        player_cards.append(card)
        
        # Shuffle and remove pairs
        random.shuffle(player_cards)
        player_cards = remove_pairs(player_cards)
        
        # Update cards in shared state
        if self.use_shared_memory:
            cards_dict[from_player] = from_player_cards
            cards_dict[player_id] = player_cards
            self.game_state['cards'] = cards_dict
            
            # Add event
            events_list = list(self.game_state['events'])
            events_list.append(f"{player_id} drew a card from {from_player}")
            self.game_state['events'] = events_list
        else:
            self.game_state['cards'][from_player] = from_player_cards
            self.game_state['cards'][player_id] = player_cards
            self.game_state['events'].append(f"{player_id} drew a card from {from_player}")
        
        # Next turn
        self._next_turn(player_id)
        
        # Check win
        if self._check_game_end():
            self.game_state['status'] = 'finished'
            self.game_state['current_turn'] = None
            self._schedule_reset(5)
        
        return True

    def leave_game(self, player_id):
        if player_id not in list(self.game_state['players']):
            return False
        
        if self.use_shared_memory:
            # Update players list
            players_list = list(self.game_state['players'])
            players_list.remove(player_id)
            self.game_state['players'] = players_list
            
            # Update cards dictionary
            cards_dict = dict(self.game_state['cards'])
            if player_id in cards_dict:
                del cards_dict[player_id]
            self.game_state['cards'] = cards_dict
            
            # Add event
            events_list = list(self.game_state['events'])
            events_list.append(f"{player_id} left")
            self.game_state['events'] = events_list
        else:
            self.game_state['players'].remove(player_id)
            if player_id in self.game_state['cards']:
                del self.game_state['cards'][player_id]
            self.game_state['events'].append(f"{player_id} left")
        
        # Reset game if current player left
        if self.game_state['status'] == 'playing':
            self._reset_to_waiting()
            
            if self.use_shared_memory:
                events_list = list(self.game_state['events'])
                events_list.append("Game reset - player left during game")
                self.game_state['events'] = events_list
            else:
                self.game_state['events'].append("Game reset - player left during game")
        
        return True

    def _next_turn(self, current_player):
        players_list = list(self.game_state['players'])
        cards_dict = dict(self.game_state['cards'])
        
        if current_player not in players_list:
            return
            
        current_idx = players_list.index(current_player)
        next_player = None
        
        for i in range(1, len(players_list)):
            next_idx = (current_idx + i) % len(players_list)
            next_candidate = players_list[next_idx]
            if cards_dict.get(next_candidate, []):
                next_player = next_candidate
                break
        
        self.game_state['current_turn'] = next_player

    def _check_game_end(self):
        cards_dict = dict(self.game_state['cards'])
        players_with_cards = [p for p, c in cards_dict.items() if c]
        
        if len(players_with_cards) <= 1:
            if self.use_shared_memory:
                events_list = list(self.game_state['events'])
                
                if players_with_cards:
                    old_maid_player = players_with_cards[0]
                    old_maid_card = None
                    for card in cards_dict.get(old_maid_player, []):
                        if '_Q' in card:
                            old_maid_card = card
                            break
                    
                    if old_maid_card:
                        events_list.append(f"{old_maid_player} is the Old Maid with {old_maid_card}!")
                    else:
                        events_list.append(f"{old_maid_player} wins!")
                else:
                    events_list.append("Game Over!")
                    
                self.game_state['events'] = events_list
            else:
                if players_with_cards:
                    old_maid_player = players_with_cards[0]
                    old_maid_card = None
                    for card in self.game_state['cards'].get(old_maid_player, []):
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
        self.game_state['status'] = 'waiting'
        self.game_state['current_turn'] = None
        
        # Clear cards for all players
        if self.use_shared_memory:
            cards_dict = dict(self.game_state['cards'])
            for player in list(self.game_state['players']):
                cards_dict[player] = []
            self.game_state['cards'] = cards_dict
            
            # Add event
            events_list = list(self.game_state['events'])
            events_list.append("Press Space to Start!")
            self.game_state['events'] = events_list
        else:
            for player in self.game_state['players']:
                self.game_state['cards'][player] = []
            self.game_state['events'].append("Press Space to Start!")

    def _schedule_reset(self, delay):
        def reset_after_delay():
            time.sleep(delay)
            with self.shared_lock if self.use_shared_memory else self.lock:
                self._reset_to_waiting()
        
        reset_thread = threading.Thread(target=reset_after_delay)
        reset_thread.daemon = True
        reset_thread.start()

    def restart_game(self):
        if self.game_state['status'] == 'finished':
            self._reset_to_waiting()
            return True
        return False