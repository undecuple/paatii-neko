#!/usr/bin/env python3
# From Killzone 3 95b4038a tools/spu/lift_spu.py (kz3ver dropped; inputs: the embedded SPU ELFs and the SPURS job
# images SPU_DUMP_MISS wrote; no WWS job modules, policy modules, coverage seeds or located lifts in Toro).
"""Lift every Toro Lets Party SPU program with ps3recomp's spu_lifter.

    lift_spu.py --ps3recomp work/ps3recomp-patched --out work/spu [--elf-dir work/spu] [--job-dir work/spu-miss]
                [-j N] [--only NAME,...]

Run it through tools/spu/lift_spu.sh (sandboxed, patched ps3recomp tree). Inputs (read-only, game-derived, never
committed):
  <elf-dir>/spu_<fo>.elf          the 5 SPU ELFs embedded in the EBOOT (tools/elf_info.py dump, file offset <fo>)
  <job-dir>/spujob_<FP>_<N>.bin   SPURS jobchain job binaries the runtime dumped on a dispatch miss
                                  (SPU_DUMP_MISS, runtime/spu/spu_workload.c): exactly the N bytes the job header's
                                  sizeBinary names, FNV-1a-64 <FP>. A dump that is an ELF (an async taskset task the
                                  same switch dumps) is skipped when it equals one of the embedded ELFs.

Job binaries are raw local-store images built by the SDK's job_elf-to-bin with job_start_w_crt: code from byte 0
(the CRT's four `ila` first), position independent. runtime/spu/spurs_job.c loads the binary at LS 0 and enters
LS 0 with r3 = CellSpursJobContext2*, r4 = the descriptor, so each one is wrapped as a one-segment SPU ELF at base 0,
entry 0, and lifted with --auto-functions plus the seeds KZ3 uses for raw modules (manual link targets, PIC switch
tables, pointer tables, `ila`-built pointers). ASSUMPTION: no code end is known for the jobs (no section headers);
the whole binary is scanned, as KZ3 does for its WWS modules.

Output: <out>/lift/<name>/spu_recomp.{c,h} + lift.log, <out>/elf_in/ (wrapped inputs), <out>/spu_lift.json.
Names: elf_<fo> (fo = 8 hex digits) and job_<FP> (FP = the 16-hex-digit fingerprint).
"""
import argparse, json, os, re, struct, sys, io, contextlib, traceback
from concurrent.futures import ProcessPoolExecutor

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
JOB_BASE = 0     # runtime/spu/spurs_job.c: binary at LS 0, entered at LS 0


def fnv1a64(b):
    """runtime/spu/spu_workload.c spu_workload_fingerprint (FNV-1a 64)."""
    h = 1469598103934665603
    for x in b:
        h = ((h ^ x) * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return h


def elf_code_end(elf):
    """End of code for SDK-built ELFs: the start of .rodata when it lies inside the executable segment."""
    from find_spu_functions import parse_elf
    p = parse_elf(elf)
    for sh in p["shs"]:
        if sh["name"] == ".rodata" and sh["addr"]:
            return sh["addr"]
    return 0


# SPU branch opcodes (9-bit, ISA "Branch Instructions"): relative ones add I16<<2 to the pc, absolute ones are I16<<2.
REL_BRANCH = {0x066, 0x064, 0x042, 0x040, 0x046, 0x044}  # brsl br brnz brz brhnz brhz
ABS_BRANCH = {0x062, 0x060}                            # brasl bra


def exec_segments(elf):
    """Executable PT_LOAD segments of an SPU ELF: [(file_off, vaddr, filesz)] in program-header order."""
    phoff, = struct.unpack(">I", elf[0x1C:0x20])
    n, = struct.unpack(">H", elf[0x2C:0x2E])
    out = []
    for i in range(n):
        t, o, v, _pa, fs, _ms, fl, _al = struct.unpack(">8I", elf[phoff + 32 * i:phoff + 32 * i + 32])
        if t == 1 and fl & 1:
            out.append((o, v, fs))
    return out


def cross_segment_targets(elf, segs, k):
    """Branch targets in exec segment k reached from the other exec segments (function entries the lift of
    segment k alone cannot see). Example: elf_00fd7280 `brsl` at 0x2324C into .text_init 0x3CC08."""
    _o, v, fs = segs[k]
    tg = set()
    for j, (so, sv, sf) in enumerate(segs):
        if j == k:
            continue
        for a in range(0, sf - 3, 4):
            w, = struct.unpack(">I", elf[so + a:so + a + 4])
            op9, i16 = w >> 23, (w >> 7) & 0xFFFF
            i16 -= 0x10000 if i16 & 0x8000 else 0
            if op9 in REL_BRANCH:
                t = (sv + a + (i16 << 2)) & 0x3FFFF
            elif op9 in ABS_BRANCH:
                t = (i16 << 2) & 0x3FFFF
            else:
                continue
            if v <= t < v + fs:
                tg.add(t)
    return sorted(tg)


def _after_return(elf, so, sv, t):
    """True when LS address t (in the segment at file offset so / vaddr sv) follows `bi`/`br`/`bra`, optionally
    padded by one `nop`/`lnop`: where a function that nothing branches to directly starts."""
    def word(a):
        return struct.unpack(">I", elf[so + a - sv:so + a - sv + 4])[0] if a - sv >= 0 else 0
    # Skip alignment padding: `nop`/`lnop`, and zero words, up to 32 of them. job_011e1180's 0xCA80,
    # called through a pointer from 0x86D4 about a thousand times a second in the level, follows 16 zero bytes.
    a = t - 4
    p = word(a)
    n = 0
    while (p >> 21 in (0x001, 0x201) or p == 0) and a - 4 >= sv and n < 32:
        a -= 4
        p = word(a)
        n += 1
    return p >> 21 == 0x1A8 or p >> 23 in (0x064, 0x060)  # bi / br / bra


def pointer_targets(elf, segs, k, end=0):
    """Function entries in exec segment k whose address some exec segment builds with `ila` (function pointers:
    the .text_init segments fill vtables with main-segment entries, and the main segment builds pointers to the
    .text_init fill functions, e.g. elf_00f89300 0x3158 `ila $r9,0x3C188`). Only addresses below the code end that
    follow a return/branch count, so `ila` of .rodata strings and of mid-function labels is not seeded."""
    so, v, fs = segs[k]
    end = end or v + fs
    tg = set()
    for (o, _sv, sf) in segs:
        for a in range(0, sf - 3, 4):
            w, = struct.unpack(">I", elf[o + a:o + a + 4])
            if w >> 25 != 0x21:  # ila
                continue
            t = (w >> 7) & 0x3FFFF
            if v + 4 <= t < end and not t & 3 and _after_return(elf, so, v, t):
                tg.add(t)
    return sorted(tg)


def load_segments(elf):
    """All PT_LOAD segments of an SPU ELF (code and data): [(file_off, vaddr, filesz)]."""
    phoff, = struct.unpack(">I", elf[0x1C:0x20])
    n, = struct.unpack(">H", elf[0x2C:0x2E])
    out = []
    for i in range(n):
        t, o, v, _pa, fs, _ms, _fl, _al = struct.unpack(">8I", elf[phoff + 32 * i:phoff + 32 * i + 32])
        if t == 1 and fs:
            out.append((o, v, fs))
    return out


def table_targets(blobs, code, end):
    """Function entries reached only through a pointer TABLE in data: a 4-aligned 32-bit word anywhere
    in the image whose value is a code address below `end` that follows a return/branch (`_after_return`).
    Example: job_011f4800 (WWS overlay image 260) keeps 0x14E88 at LS 0x1FA58; nothing branches to 0x14E88 or
    builds it with `ila`, so the lift had no function there and every call through the table ran interpreted.
    blobs: [(bytes, vaddr)] to scan; code: (bytes, vaddr) of the segment the targets must lie in."""
    cb, cv = code
    tg = set()
    for (b, bv) in blobs:
        for a in range(0, len(b) - 3, 4):
            t, = struct.unpack(">I", b[a:a + 4])
            if cv + 4 <= t < end and not t & 3 and _after_return(cb, 0, cv, t):
                tg.add(t)
    return sorted(tg)


def ila_targets(code, end):
    """`ila` immediates in a raw module that land on a function start (same filter as pointer_targets)."""
    cb, cv = code
    tg = set()
    for a in range(0, len(cb) - 3, 4):
        w, = struct.unpack(">I", cb[a:a + 4])
        if w >> 25 == 0x21:
            t = (w >> 7) & 0x3FFFF
            if cv + 4 <= t < end and not t & 3 and _after_return(cb, 0, cv, t):
                tg.add(t)
    return sorted(tg)


TERMINATORS = {"br", "bra", "bi", "iret", "stop", "stopd"}


def reachable(insns, lifter, starts):
    """Addresses reachable from the function starts by fall-through and direct branches.

    A `.word` that is reachable sits in the straight-line path of something the lifter treats as code
    (a real gap, or a bogus function start); an unreachable one follows a terminator and is data."""
    by = {i.addr: i for i in insns}
    seen, work = set(), [s for s in starts if s in by]
    while work:
        a = work.pop()
        while a in by and a not in seen:
            seen.add(a)
            i = by[a]
            t = lifter._branch_target(i)
            if t is not None and t not in seen:
                work.append(t)
            if i.mnemonic in TERMINATORS or i.mnemonic == ".word":
                break
            a += 4
    return seen


def data_refs(insns):
    """LS addresses the code loads from or builds as pointers: lqa/lqr/stqa/stqr targets and `ila` values."""
    refs = set()
    for i in insns:
        if i.mnemonic in ("lqa", "lqr", "stqa", "stqr", "ila"):
            tok = i.operands.split(",")[-1].strip()
            if tok.startswith("0x"):
                refs.add(int(tok, 16) & ~0xF)
    return sorted(refs)


def debase_includes(sub):
    """Rewrite the lifter's `#include "../../runtime/spu/X.h"` to `#include "X.h"` (resolved with
    -I<ps3recomp>/runtime/spu), so the lifted tree builds from any directory (same as ps3recomp's
    build_spu_workloads.py)."""
    import re
    for fn in ("spu_recomp.c", "spu_recomp.h"):
        p = os.path.join(sub, fn)
        if os.path.exists(p):
            t = open(p).read()
            n = re.sub(r'#include\s+"(?:\.\./)+runtime/spu/([A-Za-z0-9_]+\.h)"', r'#include "\1"', t)
            if n != t:
                open(p, "w").write(n)


def lift_one(job):
    """Run spu_lifter.main() in-process for one image and collect what it lifted."""
    name, kind, elf_path, argv_extra, meta, pt, outdir = job
    sys.path.insert(0, os.path.join(pt, "tools"))
    import spu_lifter
    hist, words, inst = {}, [], {}
    orig_lift, orig_init = spu_lifter.SPULifter.lift_function, spu_lifter.SPULifter.__init__

    def init(self, *a, **k):
        orig_init(self, *a, **k)
        inst["l"] = self

    def lift(self, insns, start, end):
        if "reach" not in inst:
            inst["reach"] = reachable(insns, self, starts_of[0])
            inst["refs"] = data_refs(insns)
        for i in insns:
            if start <= i.addr < end:
                hist[i.mnemonic] = hist.get(i.mnemonic, 0) + 1
                if i.mnemonic == ".word":
                    words.append((i.addr, i.raw, start, i.addr in inst["reach"],
                                  any(r <= i.addr < r + 0x200 for r in inst["refs"])))
        return orig_lift(self, insns, start, end)

    starts_of = [None]
    orig_cbr = spu_lifter.compute_bi_r0_jumps

    def cbr(insns, bounds):  # called once by main() with the final function bounds
        starts_of[0] = sorted(s for s, _ in bounds)
        return orig_cbr(insns, bounds)

    spu_lifter.compute_bi_r0_jumps = cbr
    spu_lifter.SPULifter.lift_function, spu_lifter.SPULifter.__init__ = lift, init
    sub = os.path.join(outdir, "lift", name)
    os.makedirs(sub, exist_ok=True)
    sys.argv = ["spu_lifter.py", "--auto-functions", elf_path, "--symbol-prefix", f"{name}_", "-o", sub] + argv_extra
    buf = io.StringIO()
    ok = True
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            spu_lifter.main()
    except BaseException:
        ok = False
        buf.write(traceback.format_exc())
    debase_includes(sub)
    open(os.path.join(sub, "lift.log"), "w").write(" ".join(sys.argv[1:]) + "\n" + buf.getvalue())
    l = inst.get("l")
    res = dict(name=name, kind=kind, ok=ok, argv=argv_extra, **meta)
    if l is not None:
        res.update(functions=len(l.functions), unsupported=dict(l.unsupported),
                   insns=sum(hist.values()), hist=hist,
                   words=[list(w) for w in words])
    for line in buf.getvalue().splitlines():
        if line.startswith("Text segment:"):
            res["text"] = line
        if line.startswith("Function coverage:"):
            res["coverage"] = line
    return res




def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ps3recomp", required=True, help="patched ps3recomp tree (tools/ inside)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--elf-dir", default=os.path.join(ROOT, "work/spu"))
    ap.add_argument("--job-dir", default=os.path.join(ROOT, "work/spu-miss"))
    ap.add_argument("-j", type=int, default=4, help="lift processes (default 4: the machine is shared)")
    ap.add_argument("--only", default="", help="comma list of image names")
    ap.add_argument("--no-code-end", action="store_true", help="ELF: do not stop at .rodata (audit baseline)")
    a = ap.parse_args()
    pt = os.path.abspath(a.ps3recomp)
    out = os.path.abspath(a.out)
    sys.path.insert(0, os.path.join(pt, "tools"))
    from wrap_spu_elf import wrap
    from lift_jobmods import manual_link_targets, switch_table_targets

    jobs = []
    tmp = os.path.join(out, "elf_in")
    os.makedirs(tmp, exist_ok=True)
    elf_bytes = {}
    for fn in sorted(os.listdir(a.elf_dir)):
        if not re.fullmatch(r"spu_[0-9a-f]{8}\.elf", fn):
            continue
        p = os.path.join(a.elf_dir, fn)
        elf = open(p, "rb").read()
        off = int(fn[4:12], 16)
        elf_bytes[elf] = f"elf_{off:08x}"
        extra = []
        ce = 0 if a.no_code_end else elf_code_end(elf)
        if ce:
            extra += ["--code-end", hex(ce)]
        meta = dict(file_offset=off, size=len(elf), code_end=ce, src=os.path.relpath(p, ROOT))
        segs = exec_segments(elf)
        back = cross_segment_targets(elf, segs, 0) if len(segs) > 1 else []
        back = sorted(set(back) | set(pointer_targets(elf, segs, 0, ce)))
        if segs:
            so0, sv0, sf0 = segs[0]
            blobs = [(elf[o:o + f], v) for (o, v, f) in load_segments(elf)]
            back = sorted(set(back) | set(table_targets(blobs, (elf[so0:so0 + sf0], sv0), ce or sv0 + sf0)))
        if back:
            extra += ["--extra-funcs", ",".join(hex(x) for x in back)]
            meta["seeds"] = [hex(x) for x in back]
        jobs.append((f"elf_{off:08x}", "elf", p, extra, meta, pt, out))
        # Extra executable segments (none in Toro's 5 ELFs; kept from Killzone 3 for completeness).
        for k in range(1, len(segs)):
            so, sv, sf = segs[k]
            sp = os.path.join(tmp, f"elf_{off:08x}_x{sv:05x}.elf")
            open(sp, "wb").write(wrap(elf[so:so + sf], base=sv, entry=sv))
            seeds = sorted(set(cross_segment_targets(elf, segs, k)) | set(pointer_targets(elf, segs, k)))
            smeta = dict(file_offset=off, size=sf, base=sv, parent=f"elf_{off:08x}", seeds=[hex(x) for x in seeds])
            sx = ["--extra-funcs", ",".join(hex(x) for x in seeds)] if seeds else []
            jobs.append((f"elf_{off:08x}_x{sv:05x}", "elfseg", sp, sx, smeta, pt, out))
    skipped = {}
    for fn in sorted(os.listdir(a.job_dir)) if os.path.isdir(a.job_dir) else []:
        m = re.fullmatch(r"spujob_([0-9A-F]{16})_(\d+)\.bin", fn)
        if not m:
            continue
        p = os.path.join(a.job_dir, fn)
        raw = open(p, "rb").read()
        fp = int(m.group(1), 16)
        if len(raw) != int(m.group(2)) or fnv1a64(raw) != fp:
            sys.exit(f"{fn}: size/fingerprint do not match its name (a truncated dump?)")
        if raw[:4] == b"\x7fELF":
            if raw in elf_bytes:
                skipped[fn] = elf_bytes[raw]
                continue
            sys.exit(f"{fn}: an SPU ELF that is not one of the embedded ones in {a.elf_dir}")
        name = f"job_{m.group(1)}"
        base = JOB_BASE
        p2 = os.path.join(tmp, name + ".elf")
        open(p2, "wb").write(wrap(raw, base=base, entry=base))
        seeds = [base] + manual_link_targets(raw, base) + switch_table_targets(raw, base)
        jend = base + len(raw)
        seeds += table_targets([(raw, base)], (raw, base), jend) + ila_targets((raw, base), jend)
        seeds = sorted({s for s in seeds if base <= s < jend})
        meta = dict(file_offset=0, fp=f"0x{fp:016X}", size=len(raw), base=base, entry_off=0,
                    src=os.path.relpath(p, ROOT))
        jobs.append((name, "job", p2, ["--extra-funcs", ",".join(hex(s) for s in seeds)], meta, pt, out))
    if a.only:
        keep = set(a.only.split(","))
        jobs = [j for j in jobs if j[0] in keep]

    with ProcessPoolExecutor(max_workers=a.j) as ex:
        results = list(ex.map(lift_one, jobs))
    results.sort(key=lambda r: (r["kind"], r["name"]))
    json.dump(results, open(os.path.join(out, "spu_lift.json"), "w"), indent=1)
    bad = [r["name"] for r in results if not r["ok"]]
    tot_f = sum(r.get("functions", 0) for r in results)
    tot_u = {}
    for r in results:
        for k, v in r.get("unsupported", {}).items():
            tot_u[k] = tot_u.get(k, 0) + v
    for r in results:
        print(f"  {r['name']:24s} {r['kind']:6s} {r['size']:7d} B  functions {r.get('functions', '?'):5}  "
              f"insns {r.get('insns', '?'):6}  .word {len(r.get('words', [])):5}  {'ok' if r['ok'] else 'FAILED'}")
    print(f"dumped ELFs skipped (same bytes as an embedded ELF): {skipped}")
    print(f"images {len(results)}  failed {len(bad)} {bad}")
    print(f"functions {tot_f}  instructions {sum(r.get('insns', 0) for r in results)}")
    print("unsupported:", ", ".join(f"{k} {v}" for k, v in sorted(tot_u.items(), key=lambda kv: -kv[1])) or "none")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
