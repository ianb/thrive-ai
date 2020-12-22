import random

class Board:

    def __init__(self, board):
        self.board = board

    @classmethod
    def new_game(cls):
        return cls([
            [Piece.down("w"), Piece.down("w"), Piece.down("w"), Piece.down("w"), Piece.down("w")],
            [None, None, None, None, None],
            [None, None, None, None, None],
            [None, None, None, None, None],
            [Piece.up("b"), Piece.up("b"), Piece.up("b"), Piece.up("b"), Piece.up("b")],
        ])

    def apply_move(self, move):
        if move[0] == "move":
            return self.apply_piece_move(move[1], move[2])
        elif move[0] == "peg":
            return self.apply_peg_move(move[1], move[2])
        else:
            assert 0

    def apply_piece_move(self, source, dest):
        new_board = [row[:] for row in self.board]
        new_board[dest[1]][dest[0]] = new_board[source[1]][source[0]]
        new_board[source[1]][source[0]] = None
        return self.__class__(new_board)

    def apply_peg_move(self, source, peg_index):
        new_board = [row[:] for row in self.board]
        new_board[source[1]][source[0]] = new_board[source[1]][source[0]].with_peg(peg_index)
        return self.__class__(new_board)

    def move_moves(self, color):
        moves = []
        for row in range(5):
            for col in range(5):
                piece = self.board[row][col]
                if not piece:
                    continue
                if piece.color != color:
                    continue
                source = (col, row)
                for i in range(len(piece.positions)):
                    if not piece.positions[i]:
                        continue
                    dir = piece.directions[i]
                    new_row = row + dir[1]
                    new_col = col + dir[0]
                    if new_row < 0 or new_row >= 5 or new_col < 0 or new_col >= 5:
                        continue
                    existing = self.board[new_row][new_col]
                    if existing and existing.color == color:
                        continue
                    moves.append(("move", source, (new_col, new_row)))
        return moves

    def peg_moves(self, color):
        moves = []
        for row in range(5):
            for col in range(5):
                piece = self.board[row][col]
                if not piece or piece.color != color:
                    continue
                for i in range(25):
                    if i == 12:
                        continue
                    if not piece.positions[i]:
                        moves.append(("peg", (col, row), i))
        return moves

    def winner(self):
        for color in "w", "b":
            count = 0
            for row in range(5):
                for col in range(5):
                    piece = self.board[row][col]
                    if piece and piece.color == color:
                        count += 1
            if count <= 1:
                return "w" if color == "b" else "b"
        return None

    def __str__(self):
        s = []
        for row in range(5):
            s.append("------+-------+-------+-------+------")
            for i in range(5):
                line = []
                for col in range(5):
                    piece = self.board[row][col]
                    if not piece:
                        line.append("     ")
                    else:
                        line.append(piece.str_line(i))
                    if col != 4:
                        line.append(" | ")
                s.append("".join(line))
        s.append("------+-------+-------+-------+------")
        return "\n".join(s)


class Piece:

    def __init__(self, color, positions):
        assert color in ["w", "b"]
        self.color = color
        self.positions = positions

    directions = [
        (-2, -2), (-1, -2), (0, -2), (1, -2), (2, -2),
        (-2, -1), (-1, -1), (0, -1), (1, -1), (2, -1),
        (-2, 0),  (-1, 0),  None,    (1, 0),  (2, 0),
        (-2, 1),  (-1, 1),  (0, 1),  (1, 1),  (2, 1),
        (-2, 2),  (-1, 2),  (0, 2),  (1, 2),  (2, 2),
    ]

    @classmethod
    def down(cls, color):
        return cls(color, [
            False, False, False, False, False,
            False, False, False, False, False,
            False, False, False, False, False,
            False, False, True, False, False,
            False, False, False, False, False])

    @classmethod
    def up(cls, color):
        return cls(color, [
            False, False, False, False, False,
            False, False, True, False, False,
            False, False, False, False, False,
            False, False, False, False, False,
            False, False, False, False, False])

    def with_peg(self, pos):
        newpos = self.positions[:]
        if isinstance(pos, tuple):
            pos = self.directions.index(pos)
        assert not newpos[pos], "Attempted to double-add a peg"
        assert pos != 12, "Got a center peg"
        newpos[pos] = True
        return self.__class__(self.color, newpos)

    def peg_count(self):
        return len([p for p in self.positions if p])

    def str_line(self, i):
        assert i >= 0 and i < 5
        return "".join([
            self.color if n == 12 else ("×" if self.positions[n] else "·")
            for n in range(i * 5, i * 5 + 5)
        ])

    def __str__(self):
        return "\n".join([self.str_line(i) for i in range(5)])

    def peg_add_moves(self):
        return [
            self.directions[i]
            for i in range(25)
            if i != 12 and not self.positions[i]
        ]

class Runner:

    def __init__(self, board, player_w, player_b):
        self.board = board
        self.player_w = player_w
        self.player_b = player_b
        self.playing = "w"

    def play_turn(self):
        player = self.player_w
        if self.playing == "b":
            player = self.player_b
        move = player.choose_move(self.playing, self.board)
        assert move and move[0] == "move", "Need a proper move"
        self.log_move(move)
        self.board = self.board.apply_move(move)
        for i in range(2):
            if not self.board.peg_moves(self.playing):
                print("Win by no pegs left")
                return self.playing
            move = player.choose_peg(self.playing, self.board)
            self.log_move(move)
            assert move and move[0] == "peg", "Need a proper peg move"
            self.board = self.board.apply_move(move)
        self.playing = "b" if self.playing == "w" else "w"
        winner = self.board.winner()
        if winner:
            return winner
        return None

    def log_move(self, move):
        name = "White"
        if self.playing == "b":
            name = "Blue"
        if move[0] == "move":
            print(f"{name} moves piece at {move[1][0]},{move[1][1]} to {move[2][0]},{move[2][1]}")
        else:
            print(f"{name} adds peg to piece at {move[1][0]},{move[1][1]} at dir {Piece.directions[move[2]]}")

    def run(self):
        while True:
            next = "White" if self.playing == "w" else "Black"
            print(f"Board; next turn for {next}:")
            print(self.board)
            winner = self.play_turn()
            if winner:
                if winner == "b":
                    print("Blue wins!")
                else:
                    print("White wins!")
                print(self.board)
                return

class Random:

    def choose_move(self, color, board):
        moves = board.move_moves(color)
        # print("Possible moves:", moves)
        return random.choice(moves)

    def choose_peg(self, color, board):
        moves = board.peg_moves(color)
        # print("Possible peg moves:", moves)
        return random.choice(moves)

class Human:

    def choose_move(self, color, board):
        moves = board.move_moves(color)
        print(moves)
        print("Choose your move:")
        for i in range(len(moves)):
            move = moves[i]
            print(f"{i+1}: Move {move[1][0]},{move[1][1]} -> {move[2][0]},{move[2][1]}")
        while True:
            num = input("Which? ")
            if num:
                num = int(num)
                return moves[num - 1]

    def choose_peg(self, color, board):
        moves = board.peg_moves(color)
        print("Choose pegs:")
        seen = []
        for move in moves:
            piece = move[1]
            if piece in seen:
                continue
            seen.append(piece)
            print(f"{len(seen)}: Piece {piece[0]},{piece[1]}")
        while True:
            num = input("Which piece? ")
            if num:
                num = int(num)
                pos = seen[num - 1]
                break
        choices = []
        for move in moves:
            if move[1] != pos:
                continue
            choices.append(move)
            print(f"{len(choices)}: Peg in position {Piece.directions[move[2]]}")
        while True:
            num = input("Which peg? ")
            if num:
                num = int(num)
                return choices[num - 1]

class Scoring:

    def choose_move(self, color, board):
        moves = board.move_moves(color)
        return self.choose_score(color, moves, board)

    def choose_peg(self, color, board):
        moves = board.peg_moves(color)
        return self.choose_score(color, moves, board)

    def score_board(self, color, board):
        my_pieces = 0
        my_pegs = 0
        their_pieces = 0
        their_pegs = 0
        for row in range(5):
            for col in range(5):
                piece = board.board[row][col]
                if not piece:
                    continue
                if piece.color == color:
                    my_pieces += 1
                    my_pegs += piece.peg_count()
                else:
                    their_pieces += 1
                    their_pegs += piece.peg_count()
        if my_pieces <= 1:
            return -1000
        if their_pieces <= 1:
            return 1000
        return my_pieces * 100 + my_pegs * 5 - their_pieces * 50 - their_pegs

    def choose_score(self, color, moves, board):
        best_score = 0
        best_moves = []
        for move in moves:
            new_board = board.apply_move(move)
            score = self.score_board(color, new_board)
            if score > best_score:
                best_score = score
                best_moves = [move]
        return random.choice(best_moves)

if __name__ == "__main__":
    runner = Runner(Board.new_game(), Scoring(), Human())
    runner.run()
