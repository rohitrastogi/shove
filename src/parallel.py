import multiprocessing as mp  
import equity as utils
import constants

#TODO: investigate performance of using pipes instead of queues

def process(input_queue, output_queue, hole_cards):
    hand_hists = [[0]*len(constants.HANDS) for hand in hole_cards]
    win_hist = [0] * (len(hole_cards) + 1)
    while True:
        board = input_queue.get()
        if not board:
            break
        utils.update_simulation_state(hole_cards, board, hand_hists, win_hist)
    output_queue.put((hand_hists, win_hist))

def reduce_process_results(queue):
    from functools import reduce
    queue_list = []
    for i in iter(queue.get, None):
        queue_list.append(i)
    def helper(x, y):
        hand_hists1, win_hist1 = x[0], x[1]
        hand_hists2, win_hist2 = y[0], y[1]
        win_hist_sum = [first + second for first, second in zip(win_hist1, win_hist2)]
        hand_hists_sum = [[first + second for first, second in zip(hand_hists1[i], hand_hists2[i])] for i in range(len(hand_hists1))]
        return hand_hists_sum, win_hist_sum
    return reduce(helper, queue_list)

def run_simulation_parallel(hole_cards, board):
    deck = utils.generate_deck(hole_cards, board)
    #TODO: experiment with input_queue size relative to the number of processes
    #discover ratio of producer(generator)/consumer(equity calculation)
    input_queue = mp.Queue(maxsize = 4)
    output_queue = mp.Queue(maxsize = 4)
    pool = mp.Pool(4, initializer = process, initargs = (input_queue, output_queue, hole_cards))
    for board in utils.enumerate_boards(deck, len(board)):
        input_queue.put(board)
    for _ in range(4):
        input_queue.put(None)
    pool.close()
    pool.join()
    output_queue.put(None) #add sentinel
    hand_hists, win_hist = reduce_process_results(output_queue)
    win_perc, hand_perc = utils.calculate_equity(hand_hists, win_hist)
    print(win_perc)
    print(hand_perc)
    