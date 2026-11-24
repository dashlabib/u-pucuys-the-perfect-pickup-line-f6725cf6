#!/usr/bin/env python3
"""Publish the one-line entry for the make.fun bounty
"The Perfect Pickup Line".

The pickup line lives in ``entry.txt`` next to this file. This
program reads it, checks it against the bounty gate (UTF-8 text, a
single line, 1 to 200 characters, not only white space), writes the
exact text to ``entry.txt`` in the output directory, and reads it
back to confirm the published bytes match. Standard library only:
no network access, no clock reads, no randomness, so two runs
always produce identical output.

The output directory is ``$MAKEFUN_OUTPUT_DIR`` when set, else
``/output``. Pass ``--output-dir <dir>`` to choose it on the command
line instead, or ``--verify-only`` to check the line without
writing anything.
"""

import argparse
import os
import sys
from pathlib import Path

MAX_CHARS = 200


def load_line() -> str:
    here = Path(__file__).resolve().parent
    # Only the file's trailing newline is formatting; any other
    # surrounding whitespace is part of the entry and is rejected
    # by validate() below, so a stray space cannot slip through.
    text = (here / "entry.txt").read_text(encoding="utf-8")
    return text.rstrip("\r\n")


def validate(text: str) -> None:
    if not text or text.isspace():
        raise SystemExit("entry is empty or only white space")
    if text != text.strip():
        raise SystemExit("entry has leading or trailing whitespace")
    if len(text) > MAX_CHARS:
        raise SystemExit(
            f"entry is {len(text)} characters, over the {MAX_CHARS} limit"
        )
    if "\n" in text or "\r" in text:
        raise SystemExit("entry must be a single line")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=None,
                        help="directory to write entry.txt into")
    parser.add_argument("--verify-only", action="store_true",
                        help="validate the line without writing it")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    text = load_line()
    validate(text)
    if args.verify_only:
        print(f"Valid: {len(text)} characters")
        return 0
    out_dir = Path(args.output_dir or os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "entry.txt"
    out_path.write_text(text, encoding="utf-8")
    published = out_path.read_text(encoding="utf-8")
    if published != text:
        raise SystemExit("published entry does not match entry.txt")
    print(f"Wrote {len(text)} characters to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
