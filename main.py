#!/usr/bin/env python3
"""The Funniest Out-of-Office — one-line auto-reply writer.

Writes a single out-of-office auto-reply to /output/entry.txt (or to
$MAKEFUN_OUTPUT_DIR/entry.txt when set). Pure Python 3 standard
library, deterministic, no network: the same code always writes the
same bytes.

The entry (115 characters, no trailing newline):
    I'm away. My auto-reply is on holiday too, so this is a temp with no
    training, no password, and even less patience.

Why this line: it reads like a real auto-reply a person would set, then
turns on a second-order surprise nobody sees coming — the auto-reply
itself is on holiday, so a temp is writing this — and lands the
punchline on an escalating triple (no training, no password, and even
less patience). No beach, no "back soon", no pet/plant running the
inbox: in a field full of "my X handles my email" lines, the meta angle
stays fresh, and every word earns its place.

The output directory itself is never removed (the grader mounts it);
only entry.txt inside it is replaced. Writing is atomic: the bytes go
to a fresh mkstemp file in the same directory, are flushed through a
full-write loop, fsynced, chmodded 0644, and then os.replace()d over
entry.txt. If the temp file goes stale the write is retried once
instead of failing the run.

Usage: mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import errno
import os
import tempfile

ENTRY = "I'm away. My auto-reply is on holiday too, so this is a temp with no training, no password, and even less patience."


def _write_all(fd, data):
    """Write every byte; a short os.write must not silently truncate."""
    view = memoryview(data)
    while view:
        written = os.write(fd, view)
        view = view[written:]


def _write_entry(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    if ENTRY != ENTRY.strip() or "\n" in ENTRY or "\r" in ENTRY:
        raise ValueError("entry must be a single non-blank line")
    data = ENTRY.encode("utf-8")
    if not 1 <= len(data) <= 140:
        raise ValueError("entry must be 1-140 characters")
    final = os.path.join(out_dir, "entry.txt")
    for attempt in range(2):
        fd, tmp = tempfile.mkstemp(prefix=".entry-", dir=out_dir)
        try:
            _write_all(fd, data)
            os.fsync(fd)
            os.close(fd)
            fd = None
            os.chmod(tmp, 0o644)
            os.replace(tmp, final)
            os.chmod(final, 0o644)
            return
        except OSError as exc:
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
            if attempt == 0 and exc.errno in (errno.EEXIST, errno.EACCES):
                continue
            raise
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                pass
    raise RuntimeError("could not write entry.txt")


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    _write_entry(out_dir)


if __name__ == "__main__":
    main()
