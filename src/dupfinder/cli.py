"""Command-line entry point for dupfinder.

This is the ONLY file that touches argparse/sys/print-for-the-user. All
the actual duplicate-finding logic lives in core.py and gets imported
here — this file's job is just: parse what the user typed, call
find_duplicates(), and print the result nicely.

HOW THE WHOLE FILE FITS TOGETHER (read this first):
  build_parser()  -> defines WHAT you're allowed to type on the command
                      line (what arguments/flags exist), but doesn't run
                      anything yet.
  main()          -> the actual entry point. Uses build_parser() to read
                      what you typed, calls find_duplicates() from
                      core.py to do the real work, then prints the
                      results and returns an exit code.
  if __name__ ...  -> the few lines that run when you execute this file
                      (or the installed `dupfinder` command) directly.
"""

from __future__ import annotations
# Lets us write type hints like "list[str] | None" below on Python
# versions where that syntax wouldn't normally be allowed yet. Same
# reason core.py has this line.

import argparse   # the standard library's command-line argument parser
import sys        # gives us sys.stderr (for error messages) and sys.exit()
from pathlib import Path  # object-oriented file path handling

from dupfinder.core import find_duplicates
# ^ importing OUR OWN function from a different file in the same package.
# Because __init__.py did `from dupfinder.core import find_duplicates`,
# we could technically also write `from dupfinder import find_duplicates`
# — both work, this version is just more explicit about where it's from.
from dupfinder import __version__
# grabs the version string ("0.1.0") we defined in __init__.py


def build_parser() -> argparse.ArgumentParser:
    """Construct the argparse parser (kept separate from main() so tests
    can build/inspect it without actually running the program)."""

    parser = argparse.ArgumentParser(
        prog="dupfinder",  # the name shown in help text / error messages
        description="Find duplicate files (by content, not just name) in a folder.",
        # ^ this shows up when someone runs `dupfinder --help`
    )

    # A POSITIONAL argument — no leading "--", so it's provided by position,
    # e.g. `dupfinder ~/Downloads`. nargs="?" makes it OPTIONAL despite being
    # positional (normally a positional arg is required), and `default="."`
    # means "use the current folder" if the user doesn't type one at all.
    parser.add_argument(
        "folder",
        nargs="?",
        default=".",
        type=Path,
        # type=Path tells argparse "take whatever string the user typed
        # and run Path(...) on it for me" — so `args.folder` below is
        # already a real Path object, not a plain string we'd have to
        # convert ourselves.
        help="Folder to scan for duplicates (default: current directory)",
    )

    # An OPTIONAL flag — starts with "--", order doesn't matter, and
    # action="store_true" means it's a simple on/off switch: just writing
    # `--absolute` sets it to True; leaving it out leaves it False. There's
    # no value to type after it (unlike `folder` above).
    parser.add_argument(
        "-a",
        "--absolute",
        # having BOTH "-a" and "--absolute" just gives the user a short
        # and a long way to type the same flag — `-a` or `--absolute`
        # both work identically.
        action="store_true",
        help="Print absolute paths instead of paths relative to how you typed them",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"dupfinder {__version__}",
        # argparse handles --version specially: if the user passes it,
        # argparse immediately prints this string and exits the whole
        # program right there — none of the code in main() below even runs.
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Program entry point.

    Returns an exit code (0 = success/no problem, non-zero = error), which
    is the standard contract command-line tools follow so that other
    programs/scripts calling this one can check whether it succeeded.

    Accepting `argv` as a parameter (instead of always reading sys.argv
    directly) is what lets tests call main(["some", "args"]) later without
    needing to actually spawn a subprocess.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    # If argv is None, parse_args() automatically falls back to reading
    # sys.argv itself (the real command-line arguments). Passing an
    # explicit list, like main(["testdata", "--absolute"]), overrides
    # that — which is exactly what a future test will do.
    #
    # `args` is now an object with one attribute PER argument we defined
    # above: args.folder, args.absolute. argparse builds this for us
    # automatically based on the names we gave add_argument().

    if not args.folder.is_dir():
        # A friendly error instead of a confusing crash/stack trace if the
        # user typos a folder name.
        print(f"Error: '{args.folder}' is not a folder.", file=sys.stderr)
        # file=sys.stderr sends this to the "error output" stream instead
        # of normal stdout. This matters for real tools: it means someone
        # can do `dupfinder somefolder > results.txt` and this error
        # message will still show up on their screen instead of getting
        # silently written into results.txt along with the real output.
        return 1  # non-zero = "something went wrong"

    duplicates = find_duplicates(args.folder)
    # this is the ENTIRE reason cli.py exists: one call out to the real
    # logic in core.py. Everything else in this file is just handling
    # input/output around this one line.

    if not duplicates:
        print("No duplicates found.")
        return 0  # 0 = success. No duplicates isn't an error — it worked fine.

    total_wasted = 0
    for file_hash, paths in duplicates.items():
        display_paths = [p.resolve() if args.absolute else p for p in paths]
        # This is a "list comprehension with a conditional expression."
        # Read it right-to-left: "for p in paths, take p.resolve() if
        # args.absolute is True, otherwise just take p as-is." It's
        # shorthand for:
        #   display_paths = []
        #   for p in paths:
        #       if args.absolute:
        #           display_paths.append(p.resolve())
        #       else:
        #           display_paths.append(p)
        # p.resolve() converts a relative path like "testdata/a.txt" into
        # a full one like "/home/you/project/testdata/a.txt".

        print(f"\nDuplicate set ({file_hash[:8]}...):")
        for p in display_paths:
            print(f"  {p}")

        # Every copy after the first one is "wasted" space — e.g. 3 copies
        # of a 10MB file means 20MB you could get back by keeping just one.
        size = paths[0].stat().st_size
        total_wasted += size * (len(paths) - 1)

    mb_wasted = total_wasted / (1024 * 1024)
    # bytes -> megabytes: 1024 bytes = 1 KB, 1024 KB = 1 MB
    print(f"\n{len(duplicates)} duplicate set(s) found — about {mb_wasted:.1f} MB reclaimable.")
    # {mb_wasted:.1f} is an f-string "format spec" — the :.1f means
    # "format this number as a float with exactly 1 digit after the
    # decimal point," e.g. 3.14159 -> "3.1". Without it you'd get long,
    # ugly numbers like 12.847999999999999 printed to the user.

    return 0  # finding duplicates isn't itself an "error" for this tool


if __name__ == "__main__":
    # This block ONLY runs when this file is executed directly (e.g.
    # `python cli.py` or, once packaged, the installed `dupfinder`
    # command). If some other file did `import cli`, this block would be
    # skipped entirely.
    sys.exit(main())
    # sys.exit(code) is what actually terminates the process and hands
    # that exit code back to whatever ran this program (your shell, a
    # script, or later, a CI pipeline). main() computes the code (0 or 1);
    # sys.exit() is what makes that number "count" at the OS level.
