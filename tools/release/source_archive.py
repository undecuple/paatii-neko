#!/usr/bin/env python3
"""Write the source archive of a release commit and its checksum file.

  python3 tools/release/source_archive.py [--repo R] [--commit C] [--out-dir D] X.Y.Z

Writes D/paatii-neko-X.Y.Z-source.tar.gz (default D is work/release): `git archive` of the commit plus every
submodule at the commit it is pinned to, all under one top folder paatii-neko-X.Y.Z/. Then writes D/SHA256SUMS with the
archive's hash. Deterministic: entries sorted, owner and mtime fixed (the commit date), gzip without a name or time.
The submodule must be checked out locally at the pinned commit. Stdlib and git only; no network.
Run it on the PUBLIC export commit (a clone of the public repo), never on the private tree: it refuses a commit
that carries private notes (PRIVATE below).
"""
import argparse
import gzip
import hashlib
import io
import pathlib
import subprocess
import sys
import tarfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]


# Paths that exist only in the private tree; the public export never carries them.
PRIVATE = ("docs/in-progress/", "docs/completed/", "the decision log")


class ArchiveError(Exception):
    pass


def git(repo, *args):
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
    if r.returncode:
        raise ArchiveError("git " + " ".join(args[:2]) + " failed: " + r.stderr.decode(errors="replace").strip()[:200])
    return r.stdout


def submodules(repo, commit):
    """[(path, sha)] of the gitlinks in the commit."""
    out = []
    for ln in git(repo, "ls-tree", "-r", "-z", commit).decode().split("\0"):
        if ln.startswith("160000 "):
            meta, path = ln.split("\t", 1)
            out.append((path, meta.split()[2]))
    return sorted(out)


def members(tar_bytes, prefix, entries):
    with tarfile.open(fileobj=io.BytesIO(tar_bytes)) as t:
        for m in t:
            name = prefix + m.name
            entries[name.rstrip("/")] = (m, t.extractfile(m).read() if m.isfile() else None)


def build(repo, commit, version):
    """(gzip bytes) of the archive; raises ArchiveError."""
    top = f"paatii-neko-{version}/"
    mtime = int(git(repo, "show", "-s", "--format=%ct", commit).decode().strip())
    entries = {}
    members(git(repo, "archive", "--format=tar", commit), top, entries)
    private = sorted(n[len(top):] for n in entries if n[len(top):].startswith(PRIVATE) or n[len(top):] in PRIVATE)
    if private:
        raise ArchiveError(f"commit carries private files ({private[0]}, ...): build from the public export commit")
    for path, sha in submodules(repo, commit):
        sub = repo / path
        if not (sub / ".git").exists():
            raise ArchiveError(f"submodule {path} is not checked out (git submodule update --init)")
        try:
            data = git(sub, "archive", "--format=tar", sha)
        except ArchiveError:
            raise ArchiveError(f"submodule {path} does not have its pinned commit {sha[:8]}")
        members(data, top + path + "/", entries)
        # A tarball has no .git: the build scripts read the pinned commit from this file instead (tools/build-tlp.sh).
        stamp = tarfile.TarInfo(".tlp-commit"); stamp.type, stamp.mode = tarfile.REGTYPE, 0o644
        entries[top + path + "/.tlp-commit"] = (stamp, (sha + "\n").encode())
        entries[(top + path).rstrip("/")] = (entries.get((top + path).rstrip("/"), (None,))[0], None)
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.PAX_FORMAT) as out:
        for name in sorted(entries):
            m, data = entries[name]
            ti = tarfile.TarInfo(name)
            if m is None or m.isdir():
                ti.type, ti.mode = tarfile.DIRTYPE, 0o755
            else:
                ti.type, ti.mode = m.type, m.mode
                ti.linkname = m.linkname
                ti.size = len(data) if data is not None else 0
            ti.mtime, ti.uid, ti.gid, ti.uname, ti.gname = mtime, 0, 0, "", ""
            out.addfile(ti, io.BytesIO(data) if data is not None and ti.isfile() else None)
    gz = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=gz, mtime=0, compresslevel=9) as g:
        g.write(raw.getvalue())
    return gz.getvalue()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("version")
    ap.add_argument("--repo", default=str(ROOT))
    ap.add_argument("--commit", default="HEAD")
    ap.add_argument("--out-dir")
    a = ap.parse_args(argv)
    repo = pathlib.Path(a.repo)
    out_dir = pathlib.Path(a.out_dir) if a.out_dir else repo / "work" / "release"
    try:
        if len(a.version.split(".")) != 3 or not all(p.isdigit() for p in a.version.split(".")):
            raise ArchiveError(f"'{a.version}' is not X.Y.Z")
        commit = git(repo, "rev-parse", "--verify", a.commit + "^{commit}").decode().strip()
        data = build(repo, commit, a.version)
    except ArchiveError as e:
        print(f"source_archive: {e}", file=sys.stderr)
        return 1
    name = f"paatii-neko-{a.version}-source.tar.gz"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / name).write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    (out_dir / "SHA256SUMS").write_text(f"{digest}  {name}\n", encoding="utf-8", newline="\n")
    print(f"wrote {out_dir / name} from {commit[:10]}")
    print(f"wrote {out_dir / 'SHA256SUMS'}: {digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
