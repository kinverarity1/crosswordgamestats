# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

import game; reload(game)
import logging
import os.path
logger = logging.getLogger().setLevel("INFO")

# <codecell>

fn = r"z:\documents\scrabble\examples\yorra_cresta.gcg"
#fn = r"Z:\documents\scrabble\examples\2006_nsc_rd25_thevenot_kramer.gcg"
txt = open(fn, mode="r").read()

# <codecell>

outfn = r"z:\documents\scrabble\examples\%s.html" % os.path.basename(fn)
f = open(outfn, mode="w")
reload(game)
g = game.Game()
g.read_gcg(txt)
for board in g.get_boards():
    f.write(game.get_html_table_board(board))
    print game.get_ascii_board(board)
f.close()

# <codecell>

print "\n".join(["".join(r) for r in gr])

# <codecell>

outfn = r"z:\documents\scrabble\examples\%s.html" % os.path.basename(fn)
f = open(outfn, mode="w")
reload(game)
g = game.Game(gcgtxt=txt)
for board in g.get_boards():
    f.write(game.get_html_table_board(board))
    print game.get_ascii_board(board)
f.close()

# <codecell>

j = g.json

# <codecell>

import json
a = json.loads(j)
print j

# <codecell>

g2 = game.Game(jsontxt=j)

# <codecell>

g2

# <codecell>

import datetime
datetime.datetime.strptime("monkey", "%Y-%m-%d %H:%M:%S")

# <codecell>

s = "kent:: 5 17"
print s[:s.find("::")]
print s[s.find("::"):]

# <codecell>


