from random import *


# Initializes game.
def new_game(size):
    return [[0 for col in range(size)] for row in range(size)]


# Adds a two to the board.
def add_two(board):
    rand1 = randint(0, len(board) - 1)
    rand2 = randint(0, len(board) - 1)
    while board[rand1][rand2] != 0:
        rand1 = randint(0, len(board) - 1)
        rand2 = randint(0, len(board) - 1)
    board[rand1][rand2] = 2
    return board


# Determines state of the game.
# Returns -1 if loose, 0 if unknown, and 1 if win.
def get_game_state(board):
    last_row = len(board) - 1
    last_col = len(board[last_row]) - 1

    # Determines if the game is in win.
    for row in range(len(board)):
        for col in range(len(board[row])):
            if board[row][col] == 2048:
                return 1

    # Checks if it is possible to condense.
    for row in range(len(board) - 1):
        for col in range(len(board[row]) - 1):
            if (board[row][col] == board[row + 1][col] or
                board[row][col] == board[row][col + 1]):
                return 0

    # Checks for any zero entries.
    for row in range(len(board)):
        for col in range(len(board)):
            if board[row][col] == 0:
                return 0

    # Checks left/right entries on the last row.
    for col in range(last_col):
        if board[last_row][col] == board[last_row][col + 1]:
            return 0

    # Checks up/down on the last column.
    for row in range(last_row):
        if board[row][last_col] == board[row + 1][last_col]:
            return 0

    return -1


def reverse(board):
    new_board = []
    for row in range(len(board)):
        new_board.append([])
        for col in range(len(board[row])):
            value = board[row][len(board[row]) - col - 1]
            new_board[row].append(value)
    return new_board


# .
def transpose(board):
    new_board = []
    for col in range(len(board[0])):
        new_board.append([])
        for row in range(len(board)):
            new_board[col].append(board[row][col])
    return new_board


# Shifts everything to the left.
def shift_left(board):
    new_board = new_game(len(board))
    made_move = False

    for row in range(len(board)):
        count = 0
        for col in range(len(board[row])):
            if board[row][col] != 0:
                new_board[row][count] = board[row][col]
                if col != count:
                    made_move = True
                count += 1
    return (new_board, made_move)


# Merges blocks.
def merge(board):
    made_move = False
    for row in range(len(board)):
        for col in range(len(board[row]) - 1):
            if (board[row][col] == board[row][col + 1] and
                board[row][col] != 0):
                board[row][col] *= 2
                board[row][col + 1] = 0
                made_move = True
    return (board, made_move)


# Moves the board.
def move_board(game, direction):
    has_shift = False
    has_merge = False

    if direction == 'w':
        print('... UP ...')
        game = transpose(game)
        game, has_shift = shift_left(game)
        game, has_merge = merge(game)
        game, _ = shift_left(game)
        game = transpose(game)
    elif direction == 'a':
        print('... LEFT ...')
        game, has_shift = shift_left(game)
        game, has_merge = merge(game)
        game, _ = shift_left(game)
    elif direction == 's':
        print('... RIGHT ...')
        game = reverse(game)
        game, has_shift = shift_left(game)
        game, has_merge = merge(game)
        game, _ = shift_left(game)
        game = reverse(game)
    elif direction == 'z':
        print('... DOWN ...')
        game = reverse(transpose(game))
        game, has_shift = shift_left(game)
        game, has_merge = merge(game)
        game, _ = shift_left(game)
        game = transpose(reverse(game))
    else:
        print('... INVALID MOVE ...')

    made_move = has_shift or has_merge
    return (game, made_move)


# Prints the board.
def print_board(board):
    for row in board:
        for col in row:
            print('{0} '.format(col), end=' ')
        print()
    print()


def main():
    # Initialize board.
    board = new_game(size=4)
    add_two(board)
    add_two(board)
    print_board(board)

    # Loop until game state ended.
    game_state = 0

    while game_state == 0:
        direction = input('Enter direction to move (w = UP, a = LEFT, s = RIGHT, z = DOWN): ')
        board, made_move = move_board(board, direction)
        if made_move:
            add_two(board)

            # Prints the board.
            print_board(board)

            # Set variables for next loop.
            game_state = get_game_state(board)

    # Prints the results of the game.
    if game_state == 1:
        print('YOU WON!')
    else:
        print('YOU LOST')

if __name__ == '__main__':
    main()
