import pygame
import sys
import os
from game_client import ClientInterface 

class SimpleOldMaidClient:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1000, 700))
        pygame.display.set_caption("Simple Old Maid")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        
        # Colors
        self.WHITE= (255, 255, 255)
        self.GREEN = (0, 140, 0)
        self.RED = (255, 0, 0)
        self.YELLOW = (255,255,100)
        
        # Game client
        self.client = ClientInterface()
        
        # Game state
        self.player_id = None
        self.players, self.my_cards, self.other_cards = [], [], {}
        self.current_turn, self.status, self.message = None, "waiting", "Connecting..."
        self.selected_card = None
        self.player_rects, self.card_rects = {}, {}
        self.hovered_card = None  # Track which card is being hovered
        self.mouse_pos = (0, 0)  # Track mouse position
        
        # Load card assets
        self.card_assets = {}
        asset_dir = os.path.join(os.path.dirname(__file__), "assets")
        if os.path.exists(asset_dir):
            for suit in ['clubs', 'diamonds', 'hearts', 'spades']:
                for val in ['02','03','04','05','06','07','08','09','10','A','J','K','Q']:
                    try:
                        img = pygame.image.load(os.path.join(asset_dir, f"{suit}_{val}.png"))
                        # Keep original aspect ratio, just store the original image
                        self.card_assets[f"{suit}_{val}"] = img
                    except: pass
            try:
                self.card_assets["back"] = pygame.image.load(os.path.join(asset_dir, "back.png"))
            except: pass
        
        self.join_game()
    
    def join_game(self):
        success, message = self.client.join_game()
        if success:
            self.player_id = self.client.player_id
            self.message = message
        else:
            self.message = message
    
    def update_state(self):
        state = self.client.get_game_state()
        if not state: return
        
        if self.player_id and self.player_id not in state.get('players', []):
            self.player_id = None
            self.join_game()
            return
        
        if self.status == 'finished' and state.get('status') == 'waiting':
            self.my_cards, self.selected_card = [], None
        
        # Update game state
        all_cards = state.get('cards', {})
        self.players = state.get('players', [])
        self.current_turn = state.get('current_turn')
        self.status = state.get('status', 'waiting')
        self.my_cards = all_cards.get(self.player_id, [])
        self.other_cards = {p: len(all_cards.get(p, [])) for p in self.players if p != self.player_id}
        events = state.get('events', [])
        if events: self.message = events[-1]
    
    def draw_card(self, card, x, y, w=60, h=84, selected=False, hovered=False):
        if card in self.card_assets:
            # Scale image while maintaining aspect ratio
            original_img = self.card_assets[card]
            orig_w, orig_h = original_img.get_size()
            
            # Calculate scale to fit within desired dimensions
            scale_w = w / orig_w
            scale_h = h / orig_h
            scale = min(scale_w, scale_h)  # Use smaller scale to maintain aspect ratio
            
            # Calculate new dimensions
            new_w = int(orig_w * scale)
            new_h = int(orig_h * scale)
            
            # Center the image in the available space
            offset_x = (w - new_w) // 2
            offset_y = (h - new_h) // 2
            
            # Draw hover and selection effects for the full area
            if hovered: pygame.draw.rect(self.screen, (100, 150, 255), (x-3, y-3, w+6, h+6), 2)
            if selected: pygame.draw.rect(self.screen, self.YELLOW, (x-2, y-2, w+4, h+4), 3)
            
            # Scale and draw the card image centered
            scaled_img = pygame.transform.scale(original_img, (new_w, new_h))
            self.screen.blit(scaled_img, (x + offset_x, y + offset_y))
            
            return pygame.Rect(x, y, w, h)
        else:
            # Draw hover and selection effects
            if hovered: pygame.draw.rect(self.screen, (100, 150, 255), (x-3, y-3, w+6, h+6), 2)
            if selected: pygame.draw.rect(self.screen, self.YELLOW, (x-2, y-2, w+4, h+4), 3)
            
            # Draw placeholder card
            pygame.draw.rect(self.screen, self.WHITE, (x, y, w, h))
            pygame.draw.rect(self.screen, (0,0,0), (x, y, w, h), 2)
            text = self.font.render(card[:6], True, (0,0,0))
            self.screen.blit(text, (x + w//2 - text.get_width()//2, y + h//2 - text.get_height()//2))
            return pygame.Rect(x, y, w, h)
    
    def draw(self):
        self.screen.fill(self.GREEN)
        
        # Update hover detection
        self.hovered_card = None
        for card_key, rect in {**self.card_rects, **self.player_rects}.items():
            if rect.collidepoint(self.mouse_pos):
                self.hovered_card = card_key
                break
        
        # Header
        y = 10
        self.screen.blit(pygame.font.Font(None, 36).render("Simple Old Maid", True, self.WHITE), (10, y))
        y += 40
        if self.player_id:
            self.screen.blit(self.font.render(f"You: {self.player_id}", True, self.WHITE), (10, y))
        y += 30
        color = self.YELLOW if self.current_turn == self.player_id else self.WHITE
        self.screen.blit(self.font.render(f"Status: {self.status}", True, color), (10, y))
        y += 30
        if self.current_turn:
            self.screen.blit(self.font.render(f"Turn: {self.current_turn}", True, self.WHITE), (10, y))
        y += 30
        self.screen.blit(self.font.render(self.message, True, self.YELLOW), (10, y))
        
        # Other players
        y_pos = 180
        self.player_rects = {}
        for player in self.players:
            if player != self.player_id:
                card_count = self.other_cards.get(player, 0)
                color = self.YELLOW if self.current_turn == player else self.WHITE
                self.screen.blit(self.font.render(f"{player}: {card_count} cards", True, color), (10, y_pos))
                x_pos = 200
                # Draw each card as clickable (show card backs with index)
                for j in range(min(card_count, 8)):
                    is_hovered = (self.hovered_card == f"{player}_{j}")
                    rect = self.draw_card('back', x_pos, y_pos - 10, 40, 56, hovered=is_hovered)
                    # Store each card position with player and card index
                    self.player_rects[f"{player}_{j}"] = rect
                    x_pos += 25
                y_pos += 80
        
        # My cards
        if self.my_cards:
            self.screen.blit(self.font.render(f"Your cards ({len(self.my_cards)}):", True, self.WHITE), (10, 500))
            self.card_rects = {}
            x_pos = 50
            for i, card in enumerate(self.my_cards[:12]):
                is_selected = (i == self.selected_card)
                is_hovered = (self.hovered_card == i)
                rect = self.draw_card(card, x_pos, 530, selected=is_selected, hovered=is_hovered)
                self.card_rects[i] = rect
                x_pos += 70
        
        # Instructions
        if self.status == "waiting":
            text = "Press SPACE to start | ESC to quit" if len(self.players) >= 2 else "Waiting for players... | ESC to quit"
        elif self.status == "playing":
            text = "Click other players to draw | ESC to quit" if self.current_turn == self.player_id else "Waiting... | ESC to quit"
        else:
            text = "Game finished! | ESC to quit"
        self.screen.blit(self.font.render(text, True, self.RED), (10, 650))
        
        pygame.display.flip()
    
    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    self.client.leave_game()
                    pygame.quit(); sys.exit()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and self.status == "waiting":
                    self.client.start_game()
                elif event.type == pygame.MOUSEMOTION:
                    self.mouse_pos = event.pos
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    for i, rect in self.card_rects.items():
                        if rect.collidepoint(event.pos):
                            self.selected_card = None if self.selected_card == i else i
                            break
                    if self.status == "playing" and self.current_turn == self.player_id:
                        for player_card, rect in self.player_rects.items():
                            if rect.collidepoint(event.pos) and "_" in player_card:
                                player, card_index = player_card.split("_", 1)
                                if self.other_cards.get(player, 0) > int(card_index):
                                    self.client.draw_card(player, card_index)
                                break
            
            self.update_state()
            self.draw()
            self.clock.tick(24)

if __name__ == "__main__":
    SimpleOldMaidClient().run()
