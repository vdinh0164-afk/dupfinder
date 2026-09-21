"""dupfinder: find duplicate files by content, from the command line.

This file makes `src/dupfinder/` a Python *package* (a folder Python can
import as a single unit). Its main job here is to re-export the pieces
someone using this package would want, so they can write:

    from dupfinder import find_duplicates

instead of the longer:

    from dupfinder.core import find_duplicates
"""

from dupfinder.core import find_duplicates

__version__ = "0.1.0"
# We'll bump this number for each PyPI release later (task #6). Tools like
# `pip show dupfinder` and `dupfinder --version` read this.

__all__ = ["find_duplicates"]
# __all__ controls what `from dupfinder import *` pulls in. It's optional,
# but it documents "these are the public names this package offers."
