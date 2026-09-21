"""Core duplicate-detection logic for dupfinder.

This module has no CLI code in it on purpose — just pure functions that
take a folder path and return duplicate groups. Keeping this separate
from argparse/CLI code makes it trivial to unit test later (task #4)
and reusable if we ever want a GUI or web version.

HOW THE WHOLE FILE FITS TOGETHER (read this first):
  _file_hash()       -> a small helper. Given ONE file, returns a
                         fingerprint (hash) of its contents.
  find_duplicates()  -> the main function. Given a FOLDER, walks every
                         file in it and calls _file_hash() on the ones
                         that need it, then groups files that share a
                         hash together.

This file has no `if __name__ == "__main__":` block anymore — the
command-line entry point now lives in cli.py, which imports
find_duplicates() from here. See cli.py for how this gets run.
"""

from __future__ import annotations  # lets us write "str | Path" as a type hint below

import hashlib          # provides the SHA-256 hashing algorithm
import os                # provides os.walk(), for recursively listing folders
from collections import defaultdict  # a dict that auto-creates missing keys
from pathlib import Path             # object-oriented file path handling


def _file_hash(path: Path, chunk_size: int = 8192) -> str:
    """Compute the SHA-256 hash of a file's contents.

    Reads in fixed-size chunks instead of `path.read_bytes()` so that
    hashing a multi-gigabyte file doesn't load the whole thing into
    memory at once.
    """
    # A leading underscore in `_file_hash` is a Python convention meaning
    # "internal helper, not meant to be used outside this module."

    hasher = hashlib.sha256()  # create an empty hash "in progress" object

    with open(path, "rb") as f:  # "rb" = read bytes (not text) — files can be
                                  # images, videos, etc., not just text
        while chunk := f.read(chunk_size):
            # This is the "walrus operator" (:=). It does two things at once:
            #   1. reads up to 8192 bytes from the file into `chunk`
            #   2. checks if `chunk` is truthy (non-empty) to decide whether
            #      the while loop keeps going
            # f.read() returns b"" (empty bytes) once you hit the end of the
            # file, and b"" is falsy, so the loop naturally stops there.
            hasher.update(chunk)  # feed this chunk into the running hash

    return hasher.hexdigest()  # convert the hash to a readable hex string
    # e.g. "a948904f2f0f479b8f8197694b30184b0d2ed1c1cd2a1ec0fb85d299a192a44"
    # Two files with identical content ALWAYS produce this exact same
    # string. Different content (even by one byte) produces a totally
    # different string.


def find_duplicates(root: str | Path) -> dict[str, list[Path]]:
    """Find duplicate files (by content) under `root`, recursively.

    Returns a dict mapping content-hash -> list of file paths that share
    that hash. Only hashes that have 2+ files (i.e. actual duplicates)
    are included.

    Strategy (and why it's built this way):
    1. Walk the tree and group files by size first. Hashing is
       relatively expensive; two files can't possibly be duplicates if
       they're different sizes, so grouping by size first lets us skip
       hashing the vast majority of files in a typical folder.
    2. Within each size group that has 2+ files, hash the actual
       contents and group by hash. Only a hash collision across
       *different* files means a true duplicate (size match alone is
       not proof — different files can coincidentally be the same size).
    """
    root = Path(root)  # normalize input: works whether caller passed a
                        # plain string like "testdata" or a Path object

    # --- STAGE 1: group every file by its size -----------------------
    # size_groups will end up looking like: { 12: [file1, file2], 40: [file3] }
    # i.e. "these files are all exactly 12 bytes", "this one is 40 bytes"
    size_groups: dict[int, list[Path]] = defaultdict(list)
    # defaultdict(list) means: if you access a key that doesn't exist yet,
    # it auto-creates that key with an empty list `[]`, instead of raising
    # a KeyError. That's why below we can do size_groups[size].append(path)
    # without first checking "does this size already have a list?"

    for dirpath, _dirnames, filenames in os.walk(root):
        # os.walk() recursively visits every folder under `root`.
        # For EACH folder it visits, it gives you a 3-tuple:
        #   dirpath   = the folder's path (e.g. "testdata/sub")
        #   dirnames  = list of sub-folder names inside dirpath (unused here,
        #               prefixed with _ to signal "intentionally ignored")
        #   filenames = list of file names (just names, not full paths)
        #               inside dirpath
        for name in filenames:
            path = Path(dirpath) / name
            # Path(dirpath) / name joins them into one real path, e.g.
            # Path("testdata/sub") / "b.txt" -> Path("testdata/sub/b.txt")
            # (the "/" here is Path's overloaded join operator, not division)
            try:
                size = path.stat().st_size  # ask the OS: how many bytes is this file?
            except OSError:
                # File vanished, permission denied, broken symlink, etc.
                # Skip rather than crash the whole scan.
                continue
            size_groups[size].append(path)

    # --- STAGE 2: within same-size groups, hash and group by content -
    hash_groups: dict[str, list[Path]] = defaultdict(list)
    for size, paths in size_groups.items():
        # .items() gives us each (size, [list of files that size]) pair
        if len(paths) < 2:
            continue  # unique size -> can't be a duplicate, skip hashing
        for path in paths:
            try:
                file_hash = _file_hash(path)
            except OSError:
                continue
            hash_groups[file_hash].append(path)

    # --- STAGE 3: keep only REAL duplicate groups (2+ files) ----------
    return {h: paths for h, paths in hash_groups.items() if len(paths) >= 2}
    # This is a "dict comprehension" — shorthand for:
    #   result = {}
    #   for h, paths in hash_groups.items():
    #       if len(paths) >= 2:
    #           result[h] = paths
    #   return result
    # We filter again here (even though stage 1 already filtered by size)
    # because it's technically possible, though astronomically unlikely,
    # for two DIFFERENT files to land in the same size group but not
    # actually share a hash — so each hash bucket needs its own 2+ check.
