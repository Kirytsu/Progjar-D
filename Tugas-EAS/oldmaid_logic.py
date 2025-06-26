import random
from collections import defaultdict

# Simple card game logic for Old Maid
SUITS = ['hearts', 'diamonds', 'clubs', 'spades']
RANKS = ['A', '02', '03', '04', '05', '06', '07', '08', '09', '10', 'J', 'Q', 'K']

def create_deck():
    """Create deck with one queen removed (Old Maid)"""
    deck = []
    for suit in SUITS:
        for rank in RANKS:
            deck.append(f"{suit}_{rank}")
    
    # Remove one queen to make it Old Maid
    queens = [card for card in deck if '_Q' in card]
    if queens:
        deck.remove(random.choice(queens))
    
    random.shuffle(deck)
    return deck

def deal_cards(deck, players):
    """Deal cards to players"""
    hands = {player: [] for player in players}
    for i, card in enumerate(deck):
        player = players[i % len(players)]
        hands[player].append(card)
    return hands

def remove_pairs(hand):
    """Remove pairs from hand"""
    ranks = defaultdict(list)
    for card in hand:
        rank = card.split('_')[1]
        ranks[rank].append(card)
    
    new_hand = []
    for rank, cards in ranks.items():
        if len(cards) % 2 == 1:
            new_hand.append(cards[0])
    
    return new_hand
