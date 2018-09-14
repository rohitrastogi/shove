import constants
import itertools
import random


def generate_deck(hole_cards, board):
    flat_hole_cards = set([card for hand in hole_cards for card in hand] + board)
    return [(card, suit) for suit in list(constants.SUITS) for card in constants.INT_TO_RANK.keys() if (card, suit) not in flat_hole_cards]

#exhaustively enumerate all possible boards
def enumerate_boards(deck, board_size):
    return itertools.combinations(deck, constants.MAX_BOARD_SIZE - board_size)

#generate num_samples random boards (for Monte Carlo Simulation)
def sample_boards(num_samples, deck, board_size):
    for _ in range(num_samples):
        yield random.sample(deck, constants.MAX_BOARD_SIZE - board_size) 

def populate_hists(hole_cards, board):
    rank_hist = {}
    suit_hist = {}
    for (rank, suit) in hole_cards + list(board):
        if rank in rank_hist:
            rank_hist[rank] += 1
        else:
            rank_hist[rank] = 1
        
        if suit in suit_hist:
            suit_hist[suit].append(rank)
        else:
            suit_hist[suit] = [rank]
    return rank_hist, suit_hist

def evaluate_hand(hand, board):
    rank_hist, suit_hist = populate_hists(hand, board)
    #Sort in decreasing order by rank frequency. Break ties using decreasing rank.
    #Example shape: [(13, 2), (12, 2), (4, 2), (10, 1)]
    sorted_rank_hist = sorted(rank_hist.items(), key = lambda kv: ((-kv[1]), -kv[0]))
    for i, (rank, freq) in enumerate(sorted_rank_hist):
        #quads
        if freq == 4:
            return 7, get_kicker([rank], rank_hist, 1)
        elif freq == 3:
            #full house 
            if sorted_rank_hist[i + 1][1] == 2:
                pair_rank = sorted_rank_hist[i+1][0]
                return 6, rank, pair_rank
            #trips
            else:
                return 3, rank, get_kicker([rank], rank_hist, 2)
        elif freq == 2:
            #two pair
            if sorted_rank_hist[i + 1][1] == 2:
                low_pair_rank = sorted_rank_hist[i+1][0]
                return 2, rank, low_pair_rank, get_kicker([rank, low_pair_rank], rank_hist, 1)
            #single pair or possibly a straight or flush
            else:
                return evaluate_hand_helper(hand, board, rank_hist, suit_hist, rank)
    #straights, flushes, high cards
    return evaluate_hand_helper(hand, board, rank_hist, suit_hist, rank)

def evaluate_hand_helper(hand, board, rank_hist, suit_hist, rank):
    straight_kicker = detect_straight(rank_hist)
    flush_cards = detect_flush(suit_hist)
    if straight_kicker:
        #royal flush
        if straight_kicker == constants.RANK_TO_INT['A'] and flush_cards:
            return 9, None
        #straight flush
        elif flush_cards:
            return 8, straight_kicker
        #straight
        else:
            return 4, straight_kicker
    #flush
    if flush_cards:
        return 5, flush_cards
    #single pair
    if rank_hist[rank] == 2:
        return 1, rank, get_kicker([rank], rank_hist, 3)
    high_card = max(hand + list(board), key = lambda x: x[0])
    #high card
    return 0, high_card[0], get_kicker(high_card, rank_hist, 4)

def get_kicker(to_remove, rank_hist, kicker_length):
    filtered_ranks = filter(lambda x: x not in to_remove, rank_hist.keys())
    return sorted(filtered_ranks, reverse = True)[:kicker_length]

#return highest card of straight if a straight is present. otherwise, return False
def detect_straight(rank_hist):
    max_kicker = -1
    for rank in rank_hist:
        is_valid_straight = True
        lower = rank - constants.SIZE_OF_HAND + 1
        for i in range(lower, rank + 1):
            if i not in rank_hist:
                is_valid_straight = False
        if is_valid_straight:
            max_kicker = max(rank, max_kicker)
    return max_kicker if max_kicker is not -1 else False

#return list of top 5 cards that make a flush if a flush is present. otherwise, return False 
def detect_flush(suit_hist):
    for suit in suit_hist:
        if len(suit_hist[suit]) >= 5:
            return sorted(suit_hist[suit], reverse = True)[:constants.SIZE_OF_HAND]
    return False

def update_simulation_state(hole_cards, board, hand_hists, win_hist):
    evaluated_hands = []
    for i, hand in enumerate(hole_cards):
        evaluated_hand = evaluate_hand(hand, board)
        evaluated_hands.append(evaluated_hand)
        hand_hists[i][evaluated_hand[0]] += 1
    best_hand = max(evaluated_hands)
    best_hand_indices = [i for i, hand in enumerate(evaluated_hands) if hand == best_hand]
    if len(best_hand_indices) > 1:
        win_hist[len(hole_cards)] += 1
    else:
        win_hist[best_hand_indices[0]] += 1

def calculate_equity(hand_hists, win_hist):
    print(hand_hists, win_hist)
    num_its = sum(win_hist)
    win_perc = [val/num_its for val in win_hist]
    hand_perc = [[val/num_its for val in player_hist] for player_hist in hand_hists]
    return win_perc, hand_perc
        
def run_simulation(hole_cards, board):
    deck = generate_deck(hole_cards, board)
    hand_hists = [[0]*len(constants.HANDS) for hand in hole_cards]
    win_hist = [0] * (len(hole_cards) + 1)
    for board in sample_boards(10000, deck, len(board)):
        update_simulation_state(hole_cards, board, hand_hists, win_hist)
    win_perc, hand_perc = calculate_equity(hand_hists, win_hist)
    print(win_perc)
    print(hand_perc)
    
#should be roughly 87% in favor of aces
run_simulation([[(13, 'D'), (13, 'H')],[(2, 'S'), (7, 'H')]], [])
