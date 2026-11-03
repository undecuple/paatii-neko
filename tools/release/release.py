#!/usr/bin/env python3
"""One-command release step; after the Killzone 3 port's release tools.

  python3 tools/release/release.py [--dry-run] [--date YYYY-MM-DD] [--sfo F | --no-sfo] X.Y.Z

Checks everything first and writes nothing if any part disagrees: the version is X.Y.Z (tags are vX.Y.Z, no
suffixes) and not older than the current one; CHANGELOG.md exists and has an [Unreleased] section with items (it is
never created here); the release notes build; the .recomp.json check (recomp_card.py) passes. Then it bumps the
version marks (bump_version.py), turns [Unreleased] into `## [X.Y.Z] - DATE`, writes work/release/notes-X.Y.Z.md and
checks that the marks agree. Every release is a GitHub pre-release until 1.0.0. No network, no git.
"""
import argparse
import datetime
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bump_version  # noqa: E402
import recomp_card  # noqa: E402
import release_notes  # noqa: E402

ROOT = HERE.parents[1]


def plan(root, version, date, sfo=None, use_sfo=True):
    """(errors, edits, notes text). Nothing is written."""
    if bump_version.parse(version) is None:
        return [f"'{version}' is not X.Y.Z (no v prefix, no suffix)"], {}, ""
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        return [f"date '{date}' is not YYYY-MM-DD"], {}, ""
    if not (root / "CHANGELOG.md").is_file():
        return ["CHANGELOG.md does not exist; create it with an [Unreleased] section first (this tool never does)"], {}, ""
    errors = []
    try:
        if bump_version.parse(version) < bump_version.parse(bump_version.current_version(root)):
            errors.append(f"{version} is older than the current {bump_version.current_version(root)}")
        changed, _ = bump_version.edits(root, version, date)
    except bump_version.BumpError as e:
        return [str(e)], {}, ""
    notes = ""
    try:
        notes = release_notes.build(changed.get("CHANGELOG.md", (root / "CHANGELOG.md").read_text(encoding="utf-8")), version)
    except release_notes.NotesError as e:
        errors.append(str(e))
    problems, _ = recomp_card.check(root, sfo, use_sfo)
    errors += [".recomp.json: " + p for p in problems]
    return errors, changed, notes


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("version")
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--sfo")
    ap.add_argument("--no-sfo", action="store_true")
    a = ap.parse_args(argv)
    root = pathlib.Path(a.root)
    errors, changed, notes = plan(root, a.version, a.date, a.sfo, not a.no_sfo)
    if errors:
        for e in errors:
            print("release: " + e, file=sys.stderr)
        print("release: stopped, nothing written", file=sys.stderr)
        return 1
    out = root / "work" / "release" / f"notes-{a.version}.md"
    for rel in sorted(changed):
        print(("would change " if a.dry_run else "changed ") + rel)
    if a.dry_run:
        print(f"would write {out.relative_to(root)}")
        return 0
    for rel, text in changed.items():
        (root / rel).write_text(text, encoding="utf-8")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(notes, encoding="utf-8", newline="\n")
    print(f"wrote {out.relative_to(root)}")
    bad = bump_version.agree(root, a.version)
    for b in bad:
        print("release: " + b, file=sys.stderr)
    print("release: " + (f"{a.version} ready, a GitHub pre-release" if not bad and release_notes.is_prerelease(a.version)
                         else f"{a.version} ready" if not bad else "marks disagree"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
