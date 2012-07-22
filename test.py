# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

import game; reload(game)
import logging
import os.path
logger = logging.getLogger().setLevel("INFO")

# <codecell>

fn = r"z:\documents\scrabble\examples\yorra_cresta.gcg"
fn = r"Z:\documents\scrabble\examples\2006_nsc_rd25_thevenot_kramer.gcg"
txt = open(fn, mode="r").read()

# <codecell>

outfn = r"z:\documents\scrabble\examples\%s.html" % os.path.basename(fn)
f = open(outfn, mode="w")
reload(game)
g = game.Game()
g.read_gcg(txt)
for board in g.get_boards():
    f.write(game.get_html_table_board(board))
f.close()

# <codecell>

print "\n".join(["".join(r) for r in gr])

# <codecell>


