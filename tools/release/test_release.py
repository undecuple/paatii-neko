#!/usr/bin/env python3
"""Host test for release.py, bump_version.py and release_notes.py on temp trees; no network, no game data.
Run: python3 tools/release/test_release.py
"""
import contextlib
import io
import json
import os
import pathlib
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bump_version  # noqa: E402
import release  # noqa: E402
import release_notes  # noqa: E402
import test_recomp_card as tc  # noqa: E402

CMAKE = "project(tlp\n    VERSION 0.1.0\n    LANGUAGES C CXX\n)\n"
CFF = 'cff-version: 1.2.0\ntitle: "T"\nrepository-code: "https://github.com/o/r"\nlicense: MIT\nabstract: x\n'
LOG = ("# Changelog\n\n## [Unreleased]\n\n### Added\n\n- Thing one.\n  more of it\n\n### Fixed\n\n- Thing two.\n\n"
       "## [0.0.9] - 2026-01-01\n\n- Old.\n")
RC = ('FILEVERSION 0,1,0,0\nPRODUCTVERSION 0,1,0,0\nBEGIN\n VALUE "FileVersion", "0.1.0.0"\n'
      ' VALUE "ProductVersion", "0.1.0.0"\nEND\n')


def run(fn, *args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = fn(list(args))
    return rc, out.getvalue(), err.getvalue()


def snapshot(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}


class Release(tc.Tree):
    def setUp(self):
        super().setUp()
        (self.d / "port/tlp").mkdir(parents=True)
        (self.d / "port/tlp/CMakeLists.txt").write_text(CMAKE)
        (self.d / "CITATION.cff").write_text(CFF)  # same repo as the card links
        (self.d / ".recomp.json").write_text(json.dumps(self.card))
        self.sfo_args = ["--sfo", str(self.sfo)]

    def rel(self, *a):
        return run(release.main, "--root", str(self.d), "--date", "2026-11-01", *self.sfo_args, *a)

    def test_refuses_without_changelog(self):
        before = snapshot(self.d)
        rc, _, err = self.rel("0.1.0")
        self.assertEqual(rc, 1)
        self.assertIn("CHANGELOG.md does not exist", err)
        self.assertEqual(snapshot(self.d), before)
        self.assertFalse((self.d / "CHANGELOG.md").exists())

    def test_release(self):
        (self.d / "CHANGELOG.md").write_text(LOG)
        (self.d / "port/tlp/app.rc").write_text(RC)
        rc, out, err = self.rel("0.2.0")
        self.assertEqual(rc, 0, err)
        self.assertIn("pre-release", out)
        self.assertIn("VERSION 0.2.0", (self.d / "port/tlp/CMakeLists.txt").read_text())
        cff = (self.d / "CITATION.cff").read_text()
        self.assertIn('version: "0.2.0"\ndate-released: "2026-11-01"', cff)
        log = (self.d / "CHANGELOG.md").read_text()
        self.assertIn("## [0.2.0] - 2026-11-01", log)
        self.assertNotIn("Unreleased", log)
        rc_text = (self.d / "port/tlp/app.rc").read_text()
        self.assertIn("FILEVERSION 0,2,0,0", rc_text)
        self.assertIn('"0.2.0.0"', rc_text)
        notes = (self.d / "work/release/notes-0.2.0.md").read_text()
        self.assertIn("a pre-release", notes)
        self.assertIn("- Thing one.\n  more of it", notes)
        # a second run changes nothing
        before = snapshot(self.d)
        self.assertEqual(self.rel("0.2.0")[0], 0)
        self.assertEqual(snapshot(self.d), before)

    def test_dry_run_writes_nothing(self):
        (self.d / "CHANGELOG.md").write_text(LOG)
        before = snapshot(self.d)
        rc, out, _ = self.rel("0.2.0", "--dry-run")
        self.assertEqual(rc, 0)
        self.assertIn("would change CHANGELOG.md", out)
        self.assertEqual(snapshot(self.d), before)

    def test_bad_versions(self):
        (self.d / "CHANGELOG.md").write_text(LOG)
        for v in ("v0.2.0", "0.2", "0.2.0-rc1", "0.2.0.0"):
            self.assertEqual(self.rel(v)[0], 1, v)
        self.assertIn("older", self.rel("0.0.5")[2])

    def test_stops_on_card_problem(self):
        (self.d / "CHANGELOG.md").write_text(LOG)
        self.card["status"] = "released"
        (self.d / ".recomp.json").write_text(json.dumps(self.card))
        before = snapshot(self.d)
        rc, _, err = self.rel("0.2.0")
        self.assertEqual(rc, 1)
        self.assertIn(".recomp.json:", err)
        self.assertEqual(snapshot(self.d), before)

    def test_stops_on_empty_unreleased(self):
        (self.d / "CHANGELOG.md").write_text("# C\n\n## [Unreleased]\n\n## [0.0.9] - x\n\n- a\n")
        before = snapshot(self.d)
        rc, _, err = self.rel("0.2.0")
        self.assertEqual(rc, 1)
        self.assertIn("no items", err)
        self.assertEqual(snapshot(self.d), before)

    def test_no_unreleased(self):
        (self.d / "CHANGELOG.md").write_text("# C\n\n## [0.0.9] - x\n\n- a\n")
        self.assertIn("Unreleased", self.rel("0.2.0")[2])

    def test_notes_cli(self):
        (self.d / "CHANGELOG.md").write_text(LOG.replace("[Unreleased]", "[0.2.0] - 2026-11-01"))
        rc, out, _ = run(release_notes.main, "0.2.0", "--root", str(self.d))
        self.assertEqual(rc, 0)
        self.assertIn("**Fixed**", out)
        self.assertEqual(run(release_notes.main, "0.3.0", "--root", str(self.d))[0], 1)

    def test_one_dot_zero_is_not_prerelease(self):
        self.assertFalse(release_notes.is_prerelease("1.0.0"))
        self.assertTrue(release_notes.is_prerelease("0.9.9"))


if __name__ == "__main__":
    unittest.main()
