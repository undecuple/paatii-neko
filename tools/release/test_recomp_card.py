#!/usr/bin/env python3
"""Host test for recomp_card.py on temp trees; no network, no game data (the PARAM.SFO is built here).
Run: python3 tools/release/test_recomp_card.py
"""
import json
import os
import pathlib
import shutil
import struct
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import recomp_card  # noqa: E402

REPO = "https://github.com/o/r"
CARD = {
    "$schema": "https://recomp.fyi/schema/v1.json", "game": "G", "wikidata": "Q123", "system": "PS3", "type": "recomp",
    "original": {"region": "Asia", "serial": "BCAS00000", "revision": "01.00"}, "status": "in-progress",
    "maintainers": [{"name": "m", "link": "https://github.com/m"}],
    "links": [{"label": "S", "url": REPO + "#status"}, {"label": "B", "url": REPO + "/blob/main/docs/B.md"}],
}
README = ("![Status: partly playable](https://img.shields.io/badge/status-partly%20playable-orange)\n\n"
          "> **Status: partly playable.** Text.\n\n## Status\n\ntext\n\n## Building\n")


def sfo(path, title_id, app_ver):
    """A minimal PARAM.SFO with two string entries."""
    items = [("TITLE_ID", title_id), ("APP_VER", app_ver)]
    keys = b"".join(k.encode() + b"\0" for k, _ in items)
    data, ents, ko, do = b"", b"", 0, 0
    for k, v in items:
        raw = v.encode() + b"\0"
        ents += struct.pack("<HHIII", ko, 0x204, len(raw), len(raw), do)
        ko += len(k) + 1
        data += raw
        do += len(raw)
    kt = 20 + 16 * len(items)
    pathlib.Path(path).write_bytes(struct.pack("<4sIIII", b"\0PSF", 0x101, kt, kt + len(keys), len(items)) + ents + keys + data)


class Tree(unittest.TestCase):
    def setUp(self):
        self.d = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.d)
        (self.d / "tools").mkdir()
        shutil.copy(os.path.join(HERE, "..", "disc_info.py"), self.d / "tools" / "disc_info.py")
        (self.d / "docs").mkdir()
        (self.d / "docs" / "B.md").write_text("b")
        (self.d / "README.md").write_text(README)
        (self.d / "CITATION.cff").write_text('repository-code: "' + REPO + '"\n')
        self.sfo = self.d / "PARAM.SFO"
        sfo(self.sfo, "BCAS00000", "01.00")
        self.card = json.loads(json.dumps(CARD))

    def run_check(self, **kw):
        (self.d / ".recomp.json").write_text(json.dumps(self.card))
        return recomp_card.check(self.d, kw.get("sfo", self.sfo), kw.get("use_sfo", True))

    def has(self, text, **kw):
        problems, _ = self.run_check(**kw)
        self.assertTrue(any(text in p for p in problems), problems)


class Card(Tree):
    def test_clean(self):
        self.assertEqual(self.run_check()[0], [])

    def test_bad_json(self):
        (self.d / ".recomp.json").write_text("{")
        self.assertIn("does not parse", recomp_card.check(self.d, self.sfo)[0][0])

    def test_unknown_and_private_fields(self):
        self.card["version"] = "1"
        self.card["x-private"] = 1
        problems, _ = self.run_check()
        self.assertEqual(len(problems), 1)
        self.assertIn("'version'", problems[0])

    def test_wikidata(self):
        for bad in ("Q0", "q5", "Q01", "5"):
            self.card["wikidata"] = bad
            self.has("wikidata")
        self.card["wikidata"] = "Q9"
        self.assertEqual(self.run_check()[0], [])

    def test_https(self):
        self.card["maintainers"][0]["link"] = "http://x"
        self.card["links"][0]["url"] = "ftp://x"
        problems, _ = self.run_check()
        self.assertEqual(len(problems), 2)

    def test_status_value(self):
        self.card["status"] = "done"
        self.has("not one of")

    def test_released_needs_criteria(self):
        self.card["status"] = "released"
        self.has("no release criteria are met")
        self.has("disagrees with README")

    def test_criteria_file(self):
        (self.d / "docs" / "RELEASE-CRITERIA.md").write_text("Criteria met: yes\n")
        self.card["status"] = "released"
        (self.d / "README.md").write_text(README.replace("partly%20playable", "released").replace("partly playable", "released"))
        self.assertEqual(self.run_check()[0], [])

    def test_readme_disagree(self):
        (self.d / "README.md").write_text(README.replace("**Status: partly playable.**", "**Status: playable.**"))
        self.has("differ")

    def test_readme_badge_optional(self):
        (self.d / "README.md").write_text(README.split("\n\n", 1)[1])
        self.assertEqual(self.run_check()[0], [])

    def test_readme_status_line_without_quote(self):
        (self.d / "README.md").write_text(README.replace("> **Status:", "**Status:"))
        self.assertEqual(self.run_check()[0], [])

    def test_readme_needs_status_line(self):
        (self.d / "README.md").write_text(README.replace("> **Status: partly playable.** Text.", "Text."))
        self.has("Status: ...")

    def test_links_into_repo(self):
        self.card["links"] = [{"label": "x", "url": REPO + "/blob/main/docs/NOPE.md"},
                              {"label": "y", "url": REPO + "#nowhere"},
                              {"label": "z", "url": REPO + "/tree/main/docs"},
                              {"label": "r", "url": REPO + "/releases"},
                              {"label": "o", "url": "https://example.org/x#y"}]
        problems, _ = self.run_check()
        self.assertEqual(len(problems), 2, problems)

    def test_serial_revision(self):
        sfo(self.sfo, "BCAS11111", "01.01")
        problems, _ = self.run_check()
        self.assertEqual(len(problems), 2)

    def test_no_sfo_is_a_note(self):
        problems, notes = self.run_check(sfo=self.d / "none.sfo")
        self.assertEqual((problems, len(notes)), ([], 1))

    def test_write_caps_status(self):
        self.card["status"] = "released"
        (self.d / ".recomp.json").write_text(json.dumps(self.card))
        self.assertEqual(len(recomp_card.write(self.d)), 1)
        self.assertEqual(json.loads((self.d / ".recomp.json").read_text())["status"], "in-progress")

    def test_main_exit(self):
        (self.d / ".recomp.json").write_text(json.dumps(self.card))
        self.assertEqual(recomp_card.main(["--root", str(self.d), "--sfo", str(self.sfo)]), 0)
        self.card["wikidata"] = "x"
        (self.d / ".recomp.json").write_text(json.dumps(self.card))
        self.assertEqual(recomp_card.main(["--root", str(self.d), "--sfo", str(self.sfo)]), 1)


if __name__ == "__main__":
    unittest.main()
