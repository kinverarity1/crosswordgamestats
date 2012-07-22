class Game(object):
    """
    A game of Scrabble.
    """
    tile_bonuses = """
    player_details = {}
    players = []
    metadata = {}
    moves = []
    
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
                self.players.append(player_key)
                self.player_details[player_key] = {"name": player_name}
            if line.startswith("#title"):
                self.metadata["title"] = remove(line, "#title")
            if line.startswith("#description"):
                description = remove(line, "#description")
                lines_copy = list(lines[i:])
                for j, line2 in enumerate(list(lines[i:])):
                    line2 = line2.strip()
                    if line2.startswith("#") or line2.startswith(">"):
                        break
                    else:
                        description += "\n" + line2
                self.metadata["description"] = description
            if line.startswith(">"):
                self.moves.append(parse_event(line))

def parse_event(line):
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
            if coords[0] in alphabet:
                direction = "vertical"
                x_adj = 0
                y_adj = -1
            else:
                try:
                    assert coords[-1] in alphabet
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
                return alphabet.index(column)
                
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
            "score": score,
            "move_type": move_type,
            "board_changed": board_changed}