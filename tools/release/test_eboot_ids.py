#!/usr/bin/env python3
"""Host test for eboot_ids.py: known, foreign-region, unknown-but-same-layout, modified, still-encrypted and broken
program files, and PARAM.SFO for this game, another game, another region and another version. Self-contained: builds
fake ELF, SELF and SFO files and a table of their hashes; also checks the shipped table's shape."""
import contextlib
import hashlib
import io
import json
import os
import shutil
import struct
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import eboot_ids as ei  # noqa: E402

FAILS = []


def check(cond, what, detail=""):
    print(("ok   " if cond else "FAIL ") + what + ("" if cond else f"  [{detail}]"))
    if not cond:
        FAILS.append(what)


def fake_elf(entry, text, pad=b""):
    """A 64-bit big-endian ELF header with one executable PT_LOAD of `text` bytes, then `pad`."""
    eh = b"\x7fELF\x02\x02\x01" + b"\0" * 9
    eh += struct.pack(">HHIQQQIHHHHHH", 2, 21, 1, entry, 64, 0, 0, 64, 56, 1, 0, 0, 0)
    ph = struct.pack(">IIQQQQQQ", 1, 5, 0, 0x10000, 0x10000, text, text, 0x10000)
    return eh + ph + pad


def fake_sfo(pairs):
    """PARAM.SFO with utf-8 string values."""
    keys = b"".join(k.encode() + b"\0" for k, _ in pairs)
    vals = [v.encode() + b"\0" for _, v in pairs]
    kt = 20 + 16 * len(pairs)
    dt = kt + len(keys)
    idx, ko, do = b"", 0, 0
    for (k, _), v in zip(pairs, vals):
        idx += struct.pack("<HHIII", ko, 0x204, len(v), len(v), do)
        ko += len(k) + 1
        do += len(v)
    return b"\0PSF" + struct.pack("<IIII", 0x101, kt, dt, len(pairs)) + idx + keys + b"".join(vals)


def put(path, data):
    with open(path, "wb") as f:
        f.write(data)
    return path


def entry(path):
    with open(path, "rb") as f:
        d = f.read()
    return {"size": len(d), "sha256": hashlib.sha256(d).hexdigest()}


def run(args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ei.main(args)
    return rc, out.getvalue()


def main():
    tbl = ei.load_table()
    sup = [b for b in tbl if b["status"] == "tested"]
    check(len(sup) == 1 and sup[0]["title_id"] == "BCAS20087", "shipped table: BCAS20087 is the one supported build")
    check(all(len(b[p + "sha256"]) == 64 and b[p + "size"] for b in tbl for p in ("", "self_")),
          "shipped table: every row has SELF and ELF sizes and SHA-256 hashes")
    check(all(set(b) >= {"title_id", "region", "app_ver", "size", "sha256", "status"} for b in tbl)
          and {b["status"] for b in tbl} <= {"tested", "untested", "unsupported"},
          "shipped table: the shared list fields on every row")

    tmp = tempfile.mkdtemp(prefix="eboot_ids_")
    try:
        us = put(os.path.join(tmp, "us.elf"), fake_elf(0x854558, 0x7feee0, b"A" * 64))
        jp = put(os.path.join(tmp, "jp.elf"), fake_elf(0x894908, 0x839ee0, b"J" * 64))
        us_self = put(os.path.join(tmp, "us.bin"), b"SCE\0" + b"S" * 128)
        relaid = put(os.path.join(tmp, "relaid.elf"), fake_elf(0x854558, 0x7feee0, b"B" * 80))
        patched = put(os.path.join(tmp, "patched.elf"), fake_elf(0x854560, 0x7feee0, b"A" * 64))
        junk = put(os.path.join(tmp, "junk.bin"), b"PK\3\4 not a program")
        table = os.path.join(tmp, "table.json")
        def row(b, elf, self_):
            return dict(b, size=elf["size"], sha256=elf["sha256"], self_size=self_["size"],
                        self_sha256=self_["sha256"])
        rows = [row(tbl[0], entry(us), entry(us_self)), row(tbl[1], entry(jp), {"size": 1, "sha256": "0" * 64})]
        with open(table, "w", encoding="utf-8") as f:
            json.dump({"builds": rows}, f)
        t = ["--table", table]

        rc, txt = run(t + ["--eboot", us])
        check(rc == 0 and "OK E1" in txt and "BCAS20087" in txt, "the supported decrypted build is OK", txt)
        rc, txt = run(t + ["--eboot", jp])
        check(rc == 1 and "FAIL E1" in txt and "Japanese release" in txt, "the Japanese build fails by name", txt)
        rc, txt = run(t + ["--eboot", us_self])
        check(rc == 0 and "still encrypted" in txt, "the disc's encrypted file is recognised", txt)
        rc, txt = run(t + ["--eboot", us_self, "--need-elf"])
        check(rc == 1 and "FAIL E2" in txt and "Decrypt it first" in txt, "--need-elf refuses an encrypted file", txt)
        rc, txt = run(t + ["--eboot", relaid])
        check(rc == 0 and "WARN E1" in txt and "may still work" in txt,
              "same entry and code size, other bytes: unknown build, may still work", txt)
        rc, txt = run(t + ["--eboot", patched])
        check(rc == 0 and "WARN E1" in txt and "patched or damaged" in txt, "another entry point: modified", txt)
        rc, txt = run(t + ["--eboot", junk])
        check(rc == 1 and "FAIL E1" in txt and "neither" in txt, "a file that is no program fails", txt)
        check(tmp not in txt and "junk" not in txt, "no path in the player text", txt)

        def sfo(tid, ver, title="X"):
            return put(os.path.join(tmp, "PARAM.SFO"), fake_sfo([("APP_VER", ver), ("TITLE", title),
                                                                ("TITLE_ID", tid)]))
        rc, txt = run(t + ["--eboot", us, "--sfo", sfo("BCAS20087", "01.00")])
        check(rc == 0 and "OK S1" in txt, "PARAM.SFO of the supported build is OK", txt)
        rc, txt = run(t + ["--eboot", us, "--sfo", sfo("BCJS30034", "01.00")])
        check(rc == 1 and "FAIL S1" in txt and "Japanese release" in txt, "PARAM.SFO of the Japanese release fails",
              txt)
        rc, txt = run(t + ["--eboot", us, "--sfo", sfo("BCAS20087", "01.01")])
        check(rc == 1 and "version 01.01" in txt, "another version fails with both versions named", txt)
        rc, txt = run(t + ["--eboot", us, "--sfo", sfo("BLUS30001", "01.00", "Other Game")])
        check(rc == 1 and "Other Game (BLUS30001)" in txt, "another game fails by its own name", txt)
        rc, txt = run(t + ["--eboot", us, "--sfo", put(os.path.join(tmp, "bad.sfo"), b"nope")])
        check(rc == 2 and "FAIL E0" in txt, "an unreadable PARAM.SFO is exit 2", txt)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"test_eboot_ids: {'PASS' if not FAILS else 'FAIL ' + ', '.join(FAILS)}")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
