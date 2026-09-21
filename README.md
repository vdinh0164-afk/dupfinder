# dupfinder

Find duplicate files by **content**, not by name — recursively, from the command line.

Two files count as duplicates only if their bytes are identical. Same name,
different content? Not a duplicate. Different name, same content? Duplicate.

## Why

Photo backups, downloaded files, and old project folders tend to accumulate
copies of the same file under different names or in different folders.
dupfinder scans a directory tree and reports which files are byte-for-byte
identical, along with how much disk space you'd reclaim by keeping just one
copy of each.

## Installation

From inside this project folder:

​```bash
pip install .
​```

This installs the `dupfinder` command using the entry point defined in
`pyproject.toml`. If you're actively developing on the project instead,
install it in editable mode so your code changes take effect without
reinstalling:

​```bash
pip install -e .
​```

## Usage

​```bash
dupfinder [folder] [-a | --absolute] [--version]
​```

- `folder` — the directory to scan (defaults to the current directory `.`
  if omitted).
- `-a`, `--absolute` — print full absolute paths instead of paths relative
  to how you typed the folder argument.
- `--version` — print the installed version and exit.

### Example

​```
$ dupfinder ~/Pictures

Duplicate set (6c91aa73...):
  Pictures/vacation/photo1.jpg
  Pictures/backup/photo1_copy.jpg

1 duplicate set(s) found — about 2.4 MB reclaimable.
​```

If nothing matches, dupfinder says so plainly:

​```
$ dupfinder ~/empty_folder
No duplicates found.
​```

## How it works

Hashing every file's full contents is the reliable way to detect duplicates,
but it's expensive on a large folder. dupfinder skips that cost wherever it
can:

1. Every file is grouped by size first (`os.walk` + `stat`). Two files of
   different sizes can never be duplicates.
2. Only within size groups with two or more files does dupfinder actually
   hash the contents (SHA-256, read in 8KB chunks so large files don't get
   loaded into memory all at once).
3. Files that share a hash are reported as a duplicate set.

The detection logic lives in `src/dupfinder/core.py` and has no
command-line code in it — `src/dupfinder/cli.py` is a thin wrapper around
it that handles argument parsing and printing.

## Running the tests

​```bash
pip install -e .
pip install pytest
pytest
​```

The test suite covers both the pure logic (`tests/test_core.py`) and the
command-line behavior (`tests/test_cli.py`).

## Project layout

​```
src/dupfinder/
  core.py    # duplicate-detection logic (no CLI code)
  cli.py     # argument parsing and printing (the only file that does)
  __init__.py
tests/
  test_core.py
  test_cli.py
pyproject.toml
​```