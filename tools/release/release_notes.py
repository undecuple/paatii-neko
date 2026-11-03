#!/usr/bin/env python3
"""Draft GitHub release notes from the CHANGELOG section of a version.

  python3 tools/release/release_notes.py X.Y.Z [--root R] [--out FILE]

Reads `## [X.Y.Z] - DATE` from CHANGELOG.md and prints a first paragraph, the section's items as a Markdown list
grouped under its ### headings, and a fixed last paragraph. Releases below 1.0.0 are pre-releases and say so. Exit 1
with a message when CHANGELOG.md or the section is missing or has no items.
"""
import argparse
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]

NAME = "Paatii Neko!"
PARA2 = ("You need your own copy of the game; none of it is included or downloaded. "
         "See the README for what works, what goes online and how to build it.")


class NotesError(Exception):
    pass


def is_prerelease(version):
    return int(version.split(".")[0]) == 0


def section(text, version):
    lines = text.splitlines()
    head = re.compile(r"^## \[" + re.escape(version) + r"\](?!\S)")
    for i, ln in enumerate(lines):
        if head.match(ln):
            body = []
            for nxt in lines[i + 1:]:
                if nxt.startswith("## "):
                    break
                body.append(nxt)
            return ln, body
    raise NotesError(f"no '## [{version}]' section in CHANGELOG.md"
                     + (" (only [Unreleased]: release.py turns it into the release)"
                        if re.search(r"^## \[Unreleased\]", text, re.M) else ""))


def build(text, version):
    _, body = section(text, version)
    groups, cur = [], None
    for ln in body:
        if ln.startswith("### "):
            cur = (ln[4:].strip(), [])
            groups.append(cur)
        elif ln.startswith("- "):
            if cur is None:
                cur = ("Changes", [])
                groups.append(cur)
            cur[1].append(ln)
        elif ln.strip() and cur and cur[1] and ln.startswith((" ", "\t")):
            cur[1][-1] += "\n" + ln                  # continuation of the previous item
    groups = [g for g in groups if g[1]]
    if not groups:
        raise NotesError(f"the '## [{version}]' section has no items")
    first = f"{NAME} {version}" + (", a pre-release" if is_prerelease(version) else "")
    out = [f"{first}. New in {version}:", ""]
    for name, items in groups:
        out += [f"**{name}**", ""] + items + [""]
    out += ["See CHANGELOG.md for the full list.", "", PARA2]
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("version")
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    if not re.fullmatch(r"\d+\.\d+\.\d+", a.version):
        print(f"release_notes: '{a.version}' is not X.Y.Z", file=sys.stderr)
        return 1
    try:
        notes = build((pathlib.Path(a.root) / "CHANGELOG.md").read_text(encoding="utf-8"), a.version)
    except FileNotFoundError:
        print("release_notes: CHANGELOG.md does not exist", file=sys.stderr)
        return 1
    except NotesError as e:
        print(f"release_notes: {e}", file=sys.stderr)
        return 1
    if a.out:
        pathlib.Path(a.out).write_text(notes, encoding="utf-8", newline="\n")
    else:
        sys.stdout.write(notes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
