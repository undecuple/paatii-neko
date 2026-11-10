#!/usr/bin/env python3
"""Identify the player's copy of the game's program file (EBOOT) against the table of known builds (eboot_ids.json).

  eboot_ids.py --eboot FILE [--sfo PARAM.SFO] [--need-elf] [--table JSON]

FILE is the decrypted EBOOT (an ELF) or the disc's EBOOT.BIN (an encrypted SELF); PARAM.SFO is the disc's
PS3_GAME/PARAM.SFO. Each finding is one line "LEVEL CODE text" (OK, WARN, FAIL); the text names the build and
never a path. Exit 0 = no FAIL, 1 = a FAIL, 2 = the file could not be read.

Codes:
  S1  PARAM.SFO: the title and version (FAIL: another game, the Japanese release, another version)
  E1  EBOOT: a known build (OK), the Japanese release (FAIL), an unknown build of the right game (WARN), a program
      that does not match the original (WARN: may be patched or damaged), neither ELF nor SELF (FAIL)
  E2  EBOOT is still encrypted where a decrypted one is needed (--need-elf: FAIL)
A decrypted file is matched by its whole-file hash, else by its segment hash (the loaded segments only, so another
decrypter's layout still matches; definition in the shared EBOOT id table). An unknown one with the supported
build's entry point and code size is "unknown build, may still work"; only when those differ too is it called
modified.
"""
import argparse
import hashlib
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TABLE = os.path.join(HERE, "eboot_ids.json")
SELF_MAGIC = b"SCE\0"
ELF_MAGIC = b"\x7fELF"


def load_table(path=TABLE):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    return d.get("entries", d.get("builds"))


REGION_WORDS = {"Asia": "Asian English", "JP": "Japanese", "US": "US", "EU": "European"}


def release(b):
    """'the Japanese release' from the table's short region label."""
    return f"the {REGION_WORDS.get(b['region'], b['region'])} release"


def parse_sfo(d):
    """PARAM.SFO bytes -> {key: str or int}."""
    if d[:4] != b"\0PSF" or len(d) < 20:
        raise ValueError("not a PARAM.SFO")
    kt, dt, n = struct.unpack("<III", d[8:20])
    out = {}
    for i in range(n):
        ko, fmt, ln, _mx, do = struct.unpack("<HHIII", d[20 + 16 * i:36 + 16 * i])
        k = d[kt + ko:d.index(b"\0", kt + ko)].decode("ascii", "replace")
        v = d[dt + do:dt + do + ln]
        out[k] = struct.unpack("<I", v[:4])[0] if fmt == 0x404 else v.rstrip(b"\0").decode("utf-8", "replace")
    return out


def elf_layout(head):
    """64-bit big-endian ELF header bytes -> (entry, file size of the first executable PT_LOAD) or None."""
    if head[:4] != ELF_MAGIC or len(head) < 64:
        return None
    entry, phoff = struct.unpack(">QQ", head[24:40])
    phentsize, phnum = struct.unpack(">HH", head[54:58])
    for i in range(phnum):
        o = phoff + i * phentsize
        if o + 48 > len(head):
            break
        typ, flags = struct.unpack(">II", head[o:o + 8])
        filesz = struct.unpack(">Q", head[o + 32:o + 40])[0]
        if typ == 1 and flags & 1:
            return entry, filesz
    return entry, None


def segment_sha256(path):
    """Shared EBOOT id table: SHA-256 over each PT_LOAD with filesz or memsz (BE64 vaddr, filesz, memsz, then the
    filesz bytes at offset), in program-header order; nothing else. None when the file is not a 64-bit BE ELF."""
    with open(path, "rb") as f:
        d = f.read(64)
        if d[:4] != ELF_MAGIC or len(d) < 64 or d[4] != 2 or d[5] != 2:
            return None
        phoff = struct.unpack(">Q", d[0x20:0x28])[0]
        phentsize, phnum = struct.unpack(">HH", d[0x36:0x3A])
        h = hashlib.sha256()
        for i in range(phnum):
            f.seek(phoff + i * phentsize)
            ph = f.read(56)
            if len(ph) < 56:
                return None
            typ = struct.unpack(">I", ph[0:4])[0]
            off, vaddr = struct.unpack(">QQ", ph[8:24])
            filesz, memsz = struct.unpack(">QQ", ph[32:48])
            if typ != 1 or (filesz == 0 and memsz == 0):
                continue
            h.update(struct.pack(">QQQ", vaddr, filesz, memsz))
            f.seek(off)
            left = filesz
            while left:
                b = f.read(min(left, 1 << 20))
                if not b:
                    return None
                h.update(b)
                left -= len(b)
    return h.hexdigest()


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def name(b):
    return f"{b['title']} ({b['title_id']}, version {b['app_ver']})"


def check_sfo(sfo, builds):
    """-> [(level, code, text)] for the disc's PARAM.SFO values."""
    sup = [b for b in builds if b["status"] == "tested"]
    want = " or ".join(f"{b['title_id']}, version {b['app_ver']}" for b in sup)
    tid, ver = sfo.get("TITLE_ID", ""), sfo.get("APP_VER", "")
    known = [b for b in builds if b["title_id"] == tid]
    if not known:
        return [("FAIL", "S1", f"This disc is {sfo.get('TITLE', '?')} ({tid or '?'}), not "
                               f"{sup[0]['title']} ({want}).")]
    b = next((k for k in known if k["app_ver"] == ver), None)
    if b is None:
        return [("FAIL", "S1", f"This is version {ver or '?'} of {known[0]['title']}; the port needs {want}.")]
    if b["status"] != "tested":
        return [("FAIL", "S1", f"This is {release(b)}, {name(b)}. The port is built from "
                               f"{release(sup[0])}, {want}.")]
    return [("OK", "S1", f"{name(b)} found.")]


def check_eboot(path, builds, need_elf=False):
    """-> [(level, code, text)] for an EBOOT file (decrypted ELF or encrypted SELF)."""
    with open(path, "rb") as f:
        head = f.read(65536)
    size = os.path.getsize(path)
    sup = [b for b in builds if b["status"] == "tested"]
    kind = "self" if head[:4] == SELF_MAGIC else "elf" if head[:4] == ELF_MAGIC else None
    if kind is None:
        return [("FAIL", "E1", "The program file is neither the disc's EBOOT.BIN nor a decrypted one: the copy is "
                               "damaged or not this game's.")]
    digest = sha256_of(path)
    pre = "self_" if kind == "self" else ""
    hit = next((b for b in builds if b.get(pre + "sha256") == digest and b.get(pre + "size") in (None, size)), None)
    same_segments = False
    if hit is None and kind == "elf":   # shared table: whole-file hash, else the segment hash, else unknown
        seg = segment_sha256(path)
        hit = next((b for b in builds if seg and b.get("segment_sha256") == seg), None)
        same_segments = hit is not None
    out = []
    if hit and hit["status"] != "tested":
        out.append(("FAIL", "E1", f"The program file is from {release(hit)}, {name(hit)}. The port "
                                  f"is built from {release(sup[0])}, {name(sup[0])}."))
    elif hit:
        out.append(("OK", "E1", f"Program file of {name(hit)}"
                                + (" (still encrypted)." if kind == "self" else
                                   " (same program, laid out by another tool)." if same_segments else ".")))
    elif kind == "elf":
        lay = elf_layout(head)
        same = [b for b in sup if lay and lay[0] == int(b["entry"], 16)
                and lay[1] == int(b["text_size"], 16)]
        if same:
            out.append(("WARN", "E1", f"The program file looks like {name(same[0])} but is not a known copy "
                                      "(unknown build, may still work)."))
        else:
            out.append(("WARN", "E1", f"The program file does not match the original {name(sup[0])}. It may be "
                                      "patched or damaged. The port may not work; please use an unmodified copy."))
    else:
        out.append(("WARN", "E1", f"The encrypted program file does not match {name(sup[0])}. It may be patched "
                                  "or damaged. The port may not work; please use an unmodified copy."))
    if need_elf and kind == "self":
        out.append(("FAIL", "E2", "The program file is still encrypted. Decrypt it first (see Getting started)."))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--eboot", required=True)
    ap.add_argument("--sfo")
    ap.add_argument("--need-elf", action="store_true")
    ap.add_argument("--table", default=TABLE)
    a = ap.parse_args(argv)
    builds = load_table(a.table)
    try:
        res = []
        if a.sfo:
            with open(a.sfo, "rb") as f:
                res += check_sfo(parse_sfo(f.read()), builds)
        res += check_eboot(a.eboot, builds, a.need_elf)
    except (OSError, ValueError) as e:
        print(f"FAIL E0 cannot read the game files ({e.__class__.__name__})")
        return 2
    for level, code, text in res:
        print(f"{level} {code} {text}")
    return 1 if any(r[0] == "FAIL" for r in res) else 0


if __name__ == "__main__":
    sys.exit(main())
