import itertools
import logging
import re
import sys


alphabet = "abcdefghijklmno"
logging.basicConfig(stream=sys.stdout, format="%(asctime)s %(message)s",
                    level=logging.DEBUG)



                    
def remove(s, substr):
    return s.replace(substr, "").strip("\n").strip().strip("\n")

    
def get_board_ascii(board):
    return "\n".join(
            ["   ABCDEFGHIJKLMNO ",
             "  +---------------+"] +
            [str(n).rjust(2) + "|" + "".join(row) + "|" + str(n).ljust(2) for n, row
             in zip(range(1, 16), board[::-1])] +
            ["  +---------------+",
             "   ABCDEFGHIJKLMNO "])
    
                
    def get_boards(self):
        rows = [[" ", " ", " ", " ", " ", " ", " ", " ",
                 " ", " ", " ", " ", " ", " ", " "]]
        for i in range(1, 15):
            rows.append(list(rows[0]))
        boards = [rows]
        for move in self.moves:
            if move["board_changed"]:
                logging.debug("replaying move: %s" % move)
                if move["move_type"] == "phoney withdraw":
                    boards[-1] = boards[-2]
                    logging.debug("new board: %s" % get_board_ascii(boards[-1]))
                    continue
                board = list([list(r) for r in boards[-1]])
                for letter, (x, y) in zip(
                        list(move["word"]), move["coordinates"]):
                    board[y][x] = letter
                logging.debug("new board: %s" % get_board_ascii(board))
                boards.append(board)
        return boards[1:]