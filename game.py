"""
Crossword Game Stats classes.
"""

import itertools
import json
import logging
import re
import sys


columns = "abcdefghijklmno"
scrabble_board = """
W  l   W   l  W
 w   L   L   w 
  w   l l   w  
l  w   l   w  l
    w     w    
 L   L   L   L 
  l   l l   l  
W  l   w   l  W
  l   l l   l  
 L   L   L   L 
    w     w    
l  w   l   w  l
  w   l l   w  
 w   L   L   w 
W  l   W   l  W
"""[1:-1].split("\n")

logging.basicConfig(stream=sys.stdout,
                    format="%(asctime)s %(message)s",
                    level=logging.DEBUG)
                    

class Game(object):
    """
    A game of Scrabble.
    """
    
    @property
    def json(self):
        return json.dumps({"moves": self._moves,
                           "metadata": self._metadata,
                           "players": self._players})
    
    def __init__(self, jsontxt=None, gcgtxt=None,
                 tile_bonuses=str(scrabble_board)):
        self._players = []
        self._moves = []
        self._metadata = {"players": {},
                          "tile_bonuses": tile_bonuses}
        if not jsontxt is None:
            self.read_json(jsontxt)
        elif not gcgtxt is None:
            self.read_gcg(gcgtxt)
    
    def get_boards(self):
        boards = [get_blank_board(15)]
        for move in self._moves:
            if move["board_changed"]:
                logging.debug("replaying move: %s" % move)
                if move["move_type"] == "phoney withdraw":
                    boards[-1] = boards[-2]
                    logging.debug("new board: %s" % get_ascii_board(boards[-1]))
                    continue
                board = list([list(r) for r in boards[-1]])
                for letter, (x, y) in zip(
                        list(move["word"]), move["coordinates"]):
                    board[y][x] = letter
                logging.debug("new board: %s" % get_ascii_board(board))
                boards.append(board)
        return boards[1:]
    
    def read_json(self, txt):
        jsondict = json.loads(txt)
        self._moves = jsondict["moves"]
        self._players = jsondict["players"]
        self._metadata = jsondict["metadata"]
    
    def read_gcg(self, txt):
        """
        Parser for .GCG files.
    
        Args:
            - *txt*: string of .GCG file
        """
        lines = [l.strip() for l in txt.split("\n")]
        for i, line in enumerate(lines):
            if line.startswith("#player"):
                tokens = line.split()
                pragma, player_key = tokens[:2]
                player_name = player_key
                if len(tokens) > 2:
                    player_name = " ".join(tokens[2:])
                self._players.append(player_key)
                self._metadata["players"][player_key] = {"name": player_name}
            if line.startswith("#title"):
                self._metadata["title"] = remove_substr(line, "#title")
            if line.startswith("#description"):
                description = remove_substr(line, "#description")
                lines_copy = list(lines[i:])
                for j, line2 in enumerate(list(lines[i:])):
                    line2 = line2.strip()
                    if line2.startswith("#") or line2.startswith(">"):
                        break
                    else:
                        description += "\n" + line2
                self._metadata["description"] = description
            if line.startswith(">"):
                self._moves.append(parse_gcg_event(line))
                
                
def parse_gcg_event(line):
    logging.debug("parsing: " + line)
    line = line.strip().strip("\n").strip()
    tokens = line.split()
    player_key = None
    rack = None
    word = None
    start = None
    direction = None
    score = None
    move_type = None
    coordinates = None
    board_changed = False
    coords = None
    if len(tokens) >= 1:
        player_key = tokens[0][1:-1]
    logging.debug("player_key: " + player_key)
    if len(tokens) >= 6:
        move_type = "regular play"
        board_changed = True
        logging.debug(move_type)
        rack, coords, word, score, total = tokens[1:6]
        coords = coords.lower()
        if not "~" in coords:
            logging.debug("coords: " + coords)
            if coords[0] in columns:
                direction = "vertical"
                x_adj = 0
                y_adj = -1
            else:
                try:
                    assert coords[-1] in columns
                except AssertionError:
                    direction = None
                else:
                    direction = "horizontal"
                    x_adj = 1
                    y_adj = 0
        logging.debug(str(direction))
        if not direction is None:
            def get_x(coords):
                column = re.search("[a-z]", coords).group()
                return columns.index(column)
                
            def get_y(y):
                row = re.search("[0-9]+", coords).group()
                return 14 - (int(row) - 1)
                
            start = [get_x(coords), get_y(coords)]
            coordinates = [start]
            for i in range(1, len(word)):
                coordinates.append(
                    (coordinates[-1][0] + x_adj, coordinates[-1][1] + y_adj))
                
    elif len(tokens) == 5:
        rack, special, score, total = tokens[1:]
        if special == "--":
            move_type = "phoney withdraw"
            board_changed = True
            logging.debug(move_type)
        elif special == "(challenge)":
            move_type = "acceptable challenge"
            logging.debug(move_type)
        elif special == "(time)":
            move_type = "time penalty"
            logging.debug(move_type)
        elif special.startswith("(") and special.endswith(")"):
            move_type = "last rack penalty"
            logging.debug(move_type)
        elif special == "-":
            move_type = "pass"
            logging.debug(move_type)
        elif special.startswith("-"):
            move_type = "tile exchange"
            logging.debug(move_type)
    elif len(tokens) == 4:
        move_type = "last rack bonus"
        logging.debug(move_type)
        rack, score, total = tokens[1:]
    else:
        move_type = "unspecified"
    if "~" in str(rack):
        rack = None
    if "~" in str(word):
        word = None
    if "~" in str(score):
        score = 0
    return {"player": player_key,
            "rack": rack,
            "word": word,
            "start": start,
            "coords": coords,
            "coordinates": coordinates,
            "direction": direction,
            "score": int(score),
            "move_type": move_type,
            "board_changed": board_changed}

                    
def remove_substr(s, substr):
    return s.replace(substr, "").strip("\n").strip().strip("\n")


def get_blank_board(size):
    """..."""
    rows = []
    for i in range(size):
        row = []
        for j in range(size):
            row.append(" ")
        rows.append(row)
    return rows

    
def get_ascii_board(board, labels=True):
    left = lambda n: str(n).rjust(2) + "|"
    right = lambda n: "|" + str(n).ljust(2)
    letters = ["".join(row) for row in board[::-1]]
    if labels:
        letters = (
            ["   ABCDEFGHIJKLMNO ",
             "  +---------------+"] +
            [left(n) + r + right(n) for n, r in zip(range(1, 16), letters)] +
            ["  +---------------+",
             "   ABCDEFGHIJKLMNO "])
    return "\n".join(letters)


def get_html_table_board(board):
    out = "<table id='board'>\n"
    for row in board[::-1]:
        out += "\t<tr>\n\t\t"
        for letter in row:
            out += "<td>%s</td>" % letter
        out += "\n\t</tr>\n"
    out += "</table>"
    return out
                
