import random
import sys
from game import Game
import numpy as np
import pygame
from agent import Agent, LegacyAlphaBeta, RandomAgent, AlphaBetaAgent, SARSA_FeatureAgent
from tqdm import tqdm
args = sys.argv
NUM_ROWS, NUM_COLS, NUM_EPISODES = int(args[1]), int(args[2]), int(args[3])

def SarsaLambda(
    game: Game, # connect-4 game
    gamma:float, # discount factor
    lam:float, # decay rate
    alpha:float, # step size
    X:SARSA_FeatureAgent,
    Opponent:Agent,
    num_episode:int,
) -> np.array:
    """
    Implement True online Sarsa(\lambda)
    """

    def epsilon_greedy_policy(game,done,w,epsilon=0.2):
        nA = game.col_count
        Q = [np.dot(w, X(game,done,a)) for a in range(nA)]
        if np.random.rand() < epsilon:
            valid_moves = game.get_valid_moves()
            if len(valid_moves) == 0:
                return None
            move = random.choice(valid_moves)
            return move
        else:
            act = np.argmax(Q)
            while not game.is_valid_location(act):
                Q[act] = np.NINF
                act = np.argmax(Q)
                if Q[act] == np.NINF:
                    return None
            return act
    
    def update(w, x, z, Q_old, gamma, alpha, observation, done, reward, action_prime, X:SARSA_FeatureAgent):
        x_prime = X(observation, done, action_prime)
        Q = np.dot(w,x)
        Q_prime = np.dot(w, x_prime)
        delta = reward + gamma * Q_prime - Q
        z = lam * gamma * z + (1-(alpha * gamma * lam * np.dot(z,x))) * x
        w = w + alpha * (delta + Q - Q_old) * z - alpha * (Q - Q_old) * x
        return w, z, Q_prime, x_prime

    w = np.zeros((X.feature_vector_len() * game.col_count), dtype=np.float32)
    explor = .2
    e_decay = .01
    win_count = 0
    
    for ep in tqdm(range(num_episode)):
        observation = Game(NUM_ROWS, NUM_COLS) #change game reset'
        #add opponent action if SARSA agent is p2 / alternate initiative each episode
        if ep % 2 == 0:
            opponent_action = Opponent.get_action(observation)
            observation.drop_piece(opponent_action, Opponent.color)
        flipped_board = np.fliplr(np.copy(observation.board))
        flipped_observation = Game(NUM_ROWS, NUM_COLS, flipped_board)

        done = len(game.get_valid_moves()) == 0
        action = epsilon_greedy_policy(observation, done, w, explor)
        flipped_action =  game.col_count - 1 - action
        x = X(observation, done, action)
        flipped_x = X(flipped_observation, done, flipped_action)
        z = np.zeros(X.feature_vector_len() * observation.col_count)
        flipped_z = np.copy(z)
        Q_old = 0
        flipped_Q_old = 0
        while not done:
            observation, reward, done, win_count = step(observation, action, Opponent, win_count)
            action_prime = epsilon_greedy_policy(observation, done, w, epsilon=explor)
            if action_prime == None:
                break
            flipped_action_prime = game.col_count - 1 - action_prime
            flipped_board = np.fliplr(np.copy(observation.board))
            flipped_observation = Game(NUM_ROWS, NUM_COLS, flipped_board)
            
            w, z, Q_old, x = update(w, x, z, Q_old, gamma, alpha, observation, done, reward, action_prime, X)
            w, flipped_z, flipped_Q_old, flipped_x = update(w, flipped_x, flipped_z, flipped_Q_old, gamma, alpha, flipped_observation, done, reward, flipped_action_prime, X)

                # x_prime = X(observation, done, action_prime)
                # Q = np.dot(w,x)
                # Q_prime = np.dot(w, x_prime)
                # delta = reward + gamma * Q_prime - Q
                # z = lam * gamma * z + (1-(alpha * gamma * lam * np.dot(z,x))) * x
                # w = w + alpha * (delta + Q - Q_old) * z - alpha * (Q - Q_old) * x
                # Q_old = Q_prime
                # x = x_prime
            action = action_prime
            explor = explor * (1-e_decay)

    # X.set_weights(w)
    print("win count: ", win_count)
    np.save("out.npy", w)
    # print(boards)
    return w

def step(game : Game, action, opponent : Agent, win_count):
    if action == None:
        return game, 0.0, True, win_count
    player_color = opponent.opponent_color
    game.drop_piece(action, player_color)
    reward = 0.0
    if game.winning_move_faster(player_color):
        reward = 1.0
        win_count += 1
        return game, reward, True, win_count
    opponent_action = opponent.get_action(game)
    #tie
    if opponent_action == None:
        return game, 0.0, True, win_count
    game.drop_piece(opponent_action, opponent.color)

    if game.winning_move_faster(opponent.color):
        reward = -1.0
        return game, reward, True, win_count
    return game, 0.0, len(game.get_valid_moves()) == 0, win_count


game = Game(NUM_ROWS, NUM_COLS)

# SQUARESIZE = 100
# width = NUM_COLS * SQUARESIZE
# height = (NUM_ROWS+1) * SQUARESIZE
# size = (width, height)
# screen = pygame.display.set_mode(size)

alpha = AlphaBetaAgent(2, 2)
rando = RandomAgent(2)
sarsa_agent = SARSA_FeatureAgent(1, NUM_COLS)
print(SarsaLambda(
    game, # connect-4 game
    0.95, # discount factor
    0.1, # decay rate
    0.01, # step size
    sarsa_agent,
    alpha, #opponent
    NUM_EPISODES, # episode
)) 