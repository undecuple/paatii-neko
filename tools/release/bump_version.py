#!/usr/bin/env python3
"""Bump the release version marks. Used by release.py.

Marks that exist today: `project(tlp VERSION X.Y.Z)` in port/tlp/CMakeLists.txt, and CITATION.cff (`version` and
`date-released`, added on the first release). Marks that will exist (stubs, skipped while the file is absent):
port/tlp/app.rc (FILEVERSION/PRODUCTVERSION as X,Y,Z,0 and the two version strings), installer/*.iss (AppVersion)
and a launcher resource under installer/launcher/*.rc. The exe version block is X.Y.Z.0, the same string everywhere.
CHANGELOG.md `## [Unreleased]` becomes `## [X.Y.Z] - DATE`.

  python3 tools/release/bump_version.py [--check] [--date YYYY-MM-DD] X.Y.Z
"""
import argparse
import datetime
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]

CMAKE = "port/tlp/CMakeLists.txt"
CFF = "CITATION.cff"
RC_FILES = ("port/tlp/app.rc", "installer/launcher/launcher.rc")     # stubs until they exist
ISS_GLOB = "installer/*.iss"                                          # stub until it exists
CHANGELOG = "CHANGELOG.md"


class BumpError(Exception):
    pass


def parse(v):
    m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", v)
    return tuple(int(x) for x in m.groups()) if m else None


def sub1(text, pattern, repl, what):
    new, n = re.subn(pattern, repl, text, flags=re.M)
    if n != 1:
        raise BumpError(f"expected exactly one {what}, found {n}")
    return new


def current_version(root):
    t = (root / CMAKE).read_text(encoding="utf-8")
    m = re.search(r"^\s*VERSION\s+(\d+\.\d+\.\d+)\s*$", t, re.M)
    if not m:
        raise BumpError(f"no project VERSION in {CMAKE}")
    return m.group(1)


def changelog_release(text, version, date):
    """Turn `## [Unreleased]` into the release heading; refuse when it is missing or has no items."""
    if re.search(rf"^## \[{re.escape(version)}\]", text, re.M):
        return text                                    # already released: nothing to do
    m = re.search(r"^## \[Unreleased\][ \t]*$", text, re.M)
    if not m:
        raise BumpError(f"{CHANGELOG} has no '## [Unreleased]' section")
    body = re.split(r"^## ", text[m.end():], maxsplit=1, flags=re.M)[0]
    if not re.search(r"^- ", body, re.M):
        raise BumpError(f"the [Unreleased] section of {CHANGELOG} has no items")
    return text[:m.start()] + f"## [{version}] - {date}" + text[m.end():]


def edits(root, version, date):
    """({path: new text} for files whose text changes, [marks that are absent])."""
    out, absent = {}, []

    def edit(rel, fn):
        p = root / rel
        if not p.is_file():
            absent.append(rel)
            return
        old = p.read_text(encoding="utf-8")
        new = fn(old)
        if new != old:
            out[rel] = new

    quad = ",".join(version.split(".") + ["0"])

    edit(CMAKE, lambda t: sub1(t, r"^(\s*VERSION\s+)\d+\.\d+\.\d+(\s*)$", rf"\g<1>{version}\2", "project VERSION"))

    def cff(t):
        if re.search(r"^version:", t, re.M):
            t = sub1(t, r"^(version:\s*).*$", rf'\g<1>"{version}"', "CITATION version")
        else:
            t = sub1(t, r"^(license:.*)$", rf'\1\nversion: "{version}"', "license line")
        if re.search(r"^date-released:", t, re.M):
            return re.sub(r"^(date-released:\s*).*$", rf'\g<1>"{date}"', t, flags=re.M)
        return sub1(t, r"^(version:.*)$", rf'\1\ndate-released: "{date}"', "version line")
    edit(CFF, cff)

    def rc(t):
        t = sub1(t, r"^(\s*FILEVERSION\s+).*$", rf"\g<1>{quad}", "FILEVERSION")
        t = sub1(t, r"^(\s*PRODUCTVERSION\s+).*$", rf"\g<1>{quad}", "PRODUCTVERSION")
        t = sub1(t, r'(VALUE "FileVersion",\s*")[^"]*(")', rf"\g<1>{version}.0\2", "FileVersion")
        return sub1(t, r'(VALUE "ProductVersion",\s*")[^"]*(")', rf"\g<1>{version}.0\2", "ProductVersion")
    for rel in RC_FILES:
        edit(rel, rc)
    iss = sorted(root.glob(ISS_GLOB))
    if not iss:
        absent.append(ISS_GLOB)
    for p in iss:
        edit(str(p.relative_to(root)),
             lambda t: sub1(t, r'^(\s*#define AppVersion ")[^"]*(")', rf"\g<1>{version}.0\2", "AppVersion"))
    edit(CHANGELOG, lambda t: changelog_release(t, version, date))
    return out, absent


def agree(root, version):
    """Problems where a mark that exists does not carry version (the check release.py runs after the edits)."""
    probs, quad = [], ",".join(version.split(".") + ["0"])
    for rel, pat, want in ((CMAKE, r"^\s*VERSION\s+(\S+)\s*$", version), (CFF, r'^version:\s*"?([^"\s]+)"?\s*$', version)):
        p = root / rel
        if p.is_file():
            m = re.search(pat, p.read_text(encoding="utf-8"), re.M)
            if not m or m.group(1) != want:
                probs.append(f"{rel}: version is {m.group(1) if m else 'missing'}, want {want}")
    for rel in RC_FILES:
        p = root / rel
        if p.is_file():
            t = p.read_text(encoding="utf-8")
            if not re.search(rf"^\s*FILEVERSION\s+{quad}\s*$", t, re.M) or f'"{version}.0"' not in t:
                probs.append(f"{rel}: version block is not {version}.0")
    return probs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("version")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--root", default=str(ROOT))
    a = ap.parse_args(argv)
    root = pathlib.Path(a.root)
    new = parse(a.version)
    if new is None or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", a.date):
        print("bump_version: version must be X.Y.Z and date YYYY-MM-DD", file=sys.stderr)
        return 2
    try:
        if new < parse(current_version(root)):
            raise BumpError(f"{a.version} is older than the current {current_version(root)}")
        changed, absent = edits(root, a.version, a.date)
    except BumpError as e:
        print(f"bump_version: {e}", file=sys.stderr)
        return 1
    for rel in sorted(changed):
        print(("would change " if a.check else "changed ") + rel)
    for rel in absent:
        print(f"not present yet: {rel}")
    if not a.check:
        for rel, text in changed.items():
            (root / rel).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
