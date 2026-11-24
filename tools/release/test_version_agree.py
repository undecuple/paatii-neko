#!/usr/bin/env python3
"""Checks that the version marks of this tree agree: CMake project VERSION, CITATION.cff and the top CHANGELOG
release (bump_version.agree, plus the newest `## [X.Y.Z]` heading). Run from the repo root or any folder:
  python3 tools/release/test_version_agree.py
"""
import os
import pathlib
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bump_version  # noqa: E402

ROOT = pathlib.Path(HERE).parents[1]


class VersionAgree(unittest.TestCase):
    def test_marks_agree(self):
        v = bump_version.current_version(ROOT)
        probs = bump_version.agree(ROOT, v)
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        if not re.search(r"^## \[\d+\.\d+\.\d+\]", text, re.M):
            # before the first release release.py adds the CITATION version and date; only that gap is allowed
            probs = [p for p in probs if not p.startswith("CITATION.cff: version is missing")]
        self.assertEqual(probs, [])

    def test_changelog_top_release(self):
        v = bump_version.current_version(ROOT)
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        heads = re.findall(r"^## \[(\d+\.\d+\.\d+)\]", text, re.M)
        if heads:   # before the first release only [Unreleased] exists
            self.assertEqual(heads[0], v, "newest CHANGELOG release differs from the CMake VERSION")


if __name__ == "__main__":
    unittest.main()
