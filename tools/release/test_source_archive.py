#!/usr/bin/env python3
"""Host test for source_archive.py on a temp repo with one pinned submodule; no network, no game data.
Run: python3 tools/release/test_source_archive.py
"""
import contextlib
import hashlib
import io
import os
import pathlib
import subprocess
import sys
import tarfile
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import source_archive  # noqa: E402

ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.com", GIT_COMMITTER_NAME="t",
           GIT_COMMITTER_EMAIL="t@example.com", GIT_AUTHOR_DATE="2026-01-02T03:04:05Z",
           GIT_COMMITTER_DATE="2026-01-02T03:04:05Z", GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)


def git(cwd, *a):
    return subprocess.run(["git", "-C", str(cwd), *a], env=ENV, check=True, capture_output=True, text=True).stdout.strip()


def run(*args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = source_archive.main(list(args))
    return rc, out.getvalue(), err.getvalue()


class Archive(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = pathlib.Path(self.tmp.name)
        sub = self.d / "repo" / "third_party" / "lib"
        sub.mkdir(parents=True)
        git(sub, "init", "-q")
        (sub / "lib.c").write_text("int lib;\n")
        git(sub, "add", ".")
        git(sub, "commit", "-qm", "lib")
        self.subsha = git(sub, "rev-parse", "HEAD")
        (sub / "later.c").write_text("not pinned\n")        # an untracked file must not be archived
        repo = self.d / "repo"
        git(repo, "init", "-q")
        (repo / "a.txt").write_text("a\n")
        (repo / "run.sh").write_text("#!/bin/sh\n")
        (repo / "run.sh").chmod(0o755)
        (repo / ".gitignore").write_text("work/\n")
        git(repo, "add", "a.txt", "run.sh", ".gitignore")
        git(repo, "update-index", "--add", "--cacheinfo", f"160000,{self.subsha},third_party/lib")
        git(repo, "commit", "-qm", "main")
        self.repo = repo

    def tearDown(self):
        self.tmp.cleanup()

    def go(self, out="out", *extra):
        return run("--repo", str(self.repo), "--out-dir", str(self.d / out), *extra, "0.1.0")

    def names(self, out="out"):
        with tarfile.open(self.d / out / "paatii-neko-0.1.0-source.tar.gz") as t:
            return [m.name for m in t], t

    def test_contents(self):
        rc, _, err = self.go()
        self.assertEqual(rc, 0, err)
        with tarfile.open(self.d / "out" / "paatii-neko-0.1.0-source.tar.gz") as t:
            names = [m.name for m in t]
            self.assertEqual(names, sorted(names))
            self.assertTrue(all(n.startswith("paatii-neko-0.1.0") for n in names))
            self.assertIn("paatii-neko-0.1.0/a.txt", names)
            self.assertIn("paatii-neko-0.1.0/third_party/lib/lib.c", names)
            self.assertNotIn("paatii-neko-0.1.0/third_party/lib/later.c", names)
            stamp = t.extractfile("paatii-neko-0.1.0/third_party/lib/.tlp-commit").read().decode()
            self.assertEqual(stamp, self.subsha + "\n")   # the pinned commit, for builds without .git
            self.assertEqual(t.getmember("paatii-neko-0.1.0/run.sh").mode & 0o111, 0o111)
            self.assertEqual({m.mtime for m in t}, {1767323045})   # the commit date, 2026-01-02T03:04:05Z
            self.assertEqual({(m.uid, m.gid) for m in t}, {(0, 0)})

    def test_sums_and_determinism(self):
        self.assertEqual(self.go("one")[0], 0)
        self.assertEqual(self.go("two")[0], 0)
        a = (self.d / "one" / "paatii-neko-0.1.0-source.tar.gz").read_bytes()
        self.assertEqual(a, (self.d / "two" / "paatii-neko-0.1.0-source.tar.gz").read_bytes())
        self.assertEqual(a[4:8], b"\0\0\0\0")                      # gzip mtime 0
        self.assertEqual((self.d / "one" / "SHA256SUMS").read_text(),
                         hashlib.sha256(a).hexdigest() + "  paatii-neko-0.1.0-source.tar.gz\n")

    def test_refusals(self):
        self.assertEqual(run("--repo", str(self.repo), "--out-dir", str(self.d / "o"), "v0.1.0")[0], 1)
        self.assertEqual(self.go("o", "--commit", "nosuchref")[0], 1)
        self.assertFalse((self.d / "o").exists())
        (self.repo / "third_party" / "lib" / ".git").rename(self.d / "gitdir")   # submodule not checked out
        rc, _, err = self.go("o")
        self.assertEqual(rc, 1)
        self.assertIn("not checked out", err)

    def test_refuses_private_tree(self):
        (self.repo / "docs" / "in-progress").mkdir(parents=True)
        (self.repo / "docs" / "in-progress" / "status.md").write_text("private\n")
        git(self.repo, "add", "docs")
        git(self.repo, "commit", "-qm", "private notes")
        rc, _, err = self.go("p")
        self.assertEqual(rc, 1)
        self.assertIn("private files", err)
        self.assertFalse((self.d / "p").exists())


if __name__ == "__main__":
    unittest.main()
