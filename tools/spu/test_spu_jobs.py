#!/usr/bin/env python3
"""Host test of tools/elf_info.py --job-dir logic on a synthetic ELF64 (no game data):
a job table of 8 {ptr, eaBinary, sizeBinary} entries (sizes not a multiple of 16) must give 8 binaries padded to 16,
named by the FNV-1a-64 fingerprint, and a short table (decoy) must be ignored.
  python3 tools/spu/test_spu_jobs.py
"""
import os, struct, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import elf_info  # noqa: E402


def build(path):
    base, rod_va, dat_va = 0x10000, 0x20000, 0x40000
    jobs = []
    rod = b""
    for k in range(8):
        sz = 0x400 + 0x10 * k + 8            # runtime size: rounded up to 16
        jb = bytes((k * 7 + i) & 0xFF for i in range(sz + 8))[: (sz + 15) & ~15]
        pad = (-len(rod)) % 128
        rod += b"\0" * pad
        jobs.append((rod_va + len(rod), sz, jb))
        rod += jb
    tab = b"".join(struct.pack(">III", dat_va + 8 * k, ea, sz) for k, (ea, sz, _) in enumerate(jobs))
    decoy = struct.pack(">III", dat_va, rod_va, 0x400) * 3  # run of 3 < min_run
    dat = tab + b"\0" * 12 + decoy
    phoff = 64
    segs = [(rod, rod_va, 4), (dat, dat_va, 6)]
    off = phoff + 56 * len(segs)
    hdr = b"\x7fELF\x02\x02\x01" + b"\0" * 9 + struct.pack(">HHIQQQIHHHHHH", 2, 21, 1, 0, phoff, 0, 0, 64, 56, len(segs), 0, 0, 0)
    ph, body = b"", b""
    for data, va, fl in segs:
        ph += struct.pack(">IIQQQQQQ", 1, fl, off + len(body), va, va, len(data), len(data), 0x80)
        body += data
    open(path, "wb").write(hdr + ph + body)
    return jobs


class SpuJobs(unittest.TestCase):
    def test_jobs(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "t.elf")
            jobs = build(p)
            got = elf_info.spu_jobs(elf_info.Elf(p))
            self.assertEqual(len(got), 8)
            for ea, sz, jb in jobs:
                fp = elf_info.fnv1a64(jb)
                self.assertEqual(got[fp], ((sz + 15) & ~15, jb))


if __name__ == "__main__":
    unittest.main()
