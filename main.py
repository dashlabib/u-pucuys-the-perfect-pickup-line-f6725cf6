#!/usr/bin/env python3
"""Publish the one-line entry for the make.fun bounty
"The Perfect Pickup Line".

The pickup line lives in ``entry.txt`` next to this file. This
program reads that file as raw bytes, decodes it as UTF-8, checks
the single line against the bounty gate (1 to 200 characters, not
only white space, no embedded line breaks), and publishes the raw
bytes verbatim to ``entry.txt`` in the output directory. Publishing
is byte-for-byte: the trailing newline in ``entry.txt`` is
formatting of the source file and is carried over unchanged, never
stripped, so the published file is identical to the source file.
After writing, the program reads the published file back and
compares bytes; a mismatch is a hard failure.

Standard library only: no network access, no clock reads, no
randomness, so two runs always produce identical output.

The output directory is ``--output-dir`` when given, else
``$MAKEFUN_OUTPUT_DIR`` when set, else ``/output``. Pass
``--verify-only`` to check the line without writing anything.
"""

import argparse
import os
import sys
import typing
from pathlib import Path

DEFAULT_MAX_CHARS = 200
MIN_CHARS = 1
DEFAULT_OUTPUT_DIR = "/output"
ENTRY_FILENAME = "entry.txt"


def entry_path() -> Path:
    """Return the path of the entry file shipped with this program."""
    return Path(__file__).resolve().parent / ENTRY_FILENAME


def load_raw(path: Path) -> bytes:
    """Read the entry file as raw bytes, failing loudly if unreadable."""
    try:
        return path.read_bytes()
    except FileNotFoundError:
        raise SystemExit(f"entry file not found: {path}")
    except OSError as exc:
        raise SystemExit(f"cannot read entry file {path}: {exc}")


def decode(raw: bytes) -> str:
    """Decode raw entry bytes as UTF-8 and drop the one trailing newline.

    Only the file's single trailing line ending (``\\n`` or ``\\r\\n``)
    is formatting and is removed for validation. Every other byte,
    including any leading or trailing space, is part of the entry and
    is rejected by :func:`validate` below, so a stray space cannot
    slip through unnoticed.
    """
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SystemExit(f"entry is not valid UTF-8: {exc}")
    if text.endswith("\r\n"):
        return text[:-2]
    if text.endswith("\n") or text.endswith("\r"):
        return text[:-1]
    return text


def fail(message: str) -> "typing.NoReturn":
    """Abort with a single clear error line on stderr (exit code 1)."""
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def validate(text: str, max_chars: int = DEFAULT_MAX_CHARS) -> None:
    """Reject any entry that breaks the bounty gate, naming the reason."""
    if not text or text.isspace():
        fail("entry is empty or only white space")
    if text != text.strip():
        fail("entry has leading or trailing whitespace")
    if len(text) < MIN_CHARS:
        fail(
            f"entry is {len(text)} characters, below the "
            f"{MIN_CHARS}-character minimum"
        )
    if len(text) > max_chars:
        fail(
            f"entry is {len(text)} characters, over the "
            f"{max_chars}-character limit"
        )
    if "\n" in text or "\r" in text:
        fail("entry must be a single line")
    if "\t" in text:
        fail("entry must not contain a tab character")
    bad = [ch for ch in text if ord(ch) < 32 or ord(ch) == 127]
    if bad:
        fail(
            "entry must not contain control characters "
            f"(found U+{ord(bad[0]):04X})"
        )


def resolve_output_dir(args: argparse.Namespace) -> Path:
    """Pick the output directory: CLI flag beats env var beats default."""
    if args.output_dir:
        return Path(args.output_dir)
    return Path(os.environ.get("MAKEFUN_OUTPUT_DIR", DEFAULT_OUTPUT_DIR))


def publish(raw: bytes, out_dir: Path) -> Path:
    """Write the raw entry bytes verbatim and verify them by re-reading.

    Returns the path written. Raises SystemExit if the directory
    cannot be created, the write fails, or the bytes read back do
    not match the bytes written.
    """
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise SystemExit(f"cannot create output directory {out_dir}: {exc}")
    out_path = out_dir / ENTRY_FILENAME
    try:
        out_path.write_bytes(raw)
    except OSError as exc:
        raise SystemExit(f"cannot write {out_path}: {exc}")
    try:
        published = out_path.read_bytes()
    except OSError as exc:
        raise SystemExit(f"cannot read back {out_path}: {exc}")
    if published != raw:
        raise SystemExit("published entry does not match entry.txt")
    return out_path


def parse_args(argv=None) -> argparse.Namespace:
    """Parse the command-line options for this publisher."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default=None,
        help="directory to write entry.txt into "
        "(default: $MAKEFUN_OUTPUT_DIR or /output)",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="validate the line without writing it",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=DEFAULT_MAX_CHARS,
        help=f"maximum entry length in characters (default: {DEFAULT_MAX_CHARS})",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="print nothing on success (errors still go to stderr)",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    """Load, validate, and publish (or just verify) the entry."""
    args = parse_args(argv)
    if args.max_chars < MIN_CHARS:
        fail(f"--max-chars must be at least {MIN_CHARS}, got {args.max_chars}")
    raw = load_raw(entry_path())
    text = decode(raw)
    validate(text, args.max_chars)
    if args.verify_only:
        if not args.quiet:
            print(f"Valid: {len(text)} characters")
        return 0
    out_path = publish(raw, resolve_output_dir(args))
    if not args.quiet:
        print(f"Wrote {len(text)} characters to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
