#!/usr/bin/env python3
# From Killzone 3 95b4038a tools/spu/gen_spu_register.py, by way of Killzone 2's adaptation (output is the
# spu_workloads.c port/tlp/CMakeLists.txt compiles from SPU_DIR; no KZ3 skip/cull tables, no WWS policy or job
# modules). Toro adds the SPURS jobchain jobs, registered by fingerprint like an ELF.
"""Generate Toro Lets Party's SPU registration TU for ps3recomp's runtime from the lift in <lift>/lift.

    gen_spu_register.py [--lift work/spu] [--elf-dir work/spu] [--job-dir work/spu-miss] [--only NAME,...]

Writes (derived from game code, never committed):
  <lift>/lift/spu_workloads.c   tlp_spu_register_all() + a constructor that calls it
  <lift>/tlp_spu_manifest.json  image ids, names, fingerprints, entry symbols

How each kind is found at run time (runtime/spu/ and libs/spurs/ of work/ps3recomp-patched):
  * SPU ELFs (elf_*): SPURS tasks are dispatched by spu_workload_dispatch*() with the fingerprint over
    spu_elf_image_size() bytes; also registered under the fingerprint of the executable PT_LOAD (raw SPU proxy-DMA
    loads). Image ids 30+.
  * SPURS jobchain jobs (job_<FP>): cellSpurs.c jc_run_one_job() -> spu_workload_dispatch_job() fingerprints the
    sizeBinary bytes at the job header's eaBinary (FNV-1a-64) and looks the fingerprint up in the same registry;
    spu_run_spurs_job() (spurs_job.c) then loads the binary at LS 0 and calls the registered entry function, the
    lifted function at LS 0. Registered with spu_workload_register_img(fp, <job>_spu_func_00000000, id). Ids 40+.
Ids stay clear of the ones the runtime special-cases (1, 2, 3, 6, 22, 23, 60-65, 100, 200+).
"""
import argparse, json, os, re, struct, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

ELF_IMAGE_BASE = 30
JOB_IMAGE_BASE = 40
RESERVED = {1, 2, 3, 6, 22, 23, 100} | set(range(60, 66))


def be16(b, o): return (b[o] << 8) | b[o + 1]
def be32(b, o): return struct.unpack_from(">I", b, o)[0]


def fnv1a64(b):
    """runtime/spu/spu_workload.c spu_workload_fingerprint (FNV-1a 64)."""
    h = 1469598103934665603
    for x in b:
        h = ((h ^ x) * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return h


def elf_image_size(b):
    """runtime/spu/spu_workload.c spu_elf_image_size (same as build_spu_workloads.py img_size)."""
    e_phoff, e_shoff = be32(b, 0x1C), be32(b, 0x20)
    e_phentsize, e_phnum = be16(b, 0x2A), be16(b, 0x2C)
    e_shentsize, e_shnum = be16(b, 0x2E), be16(b, 0x30)
    end = e_shoff + e_shnum * e_shentsize
    for k in range(e_phnum):
        po = e_phoff + k * e_phentsize
        if po + 0x14 > len(b):
            break
        end = max(end, be32(b, po + 4) + be32(b, po + 0x10))
    for k in range(e_shnum):
        so = e_shoff + k * e_shentsize
        if so + 0x18 > len(b):
            break
        if be32(b, so + 4) != 8:
            end = max(end, be32(b, so + 0x10) + be32(b, so + 0x14))
    return min(end, len(b))


def text_fp(b):
    """Fingerprint of the executable PT_LOAD's file bytes (build_spu_workloads.py text_fp)."""
    phoff, phes, phn = be32(b, 0x1C), be16(b, 0x2A), be16(b, 0x2C)
    for i in range(phn):
        o = phoff + i * phes
        if be32(b, o) == 1 and be32(b, o + 0x18) & 1:
            off, fsz = be32(b, o + 4), be32(b, o + 0x10)
            return fnv1a64(b[off:off + fsz])
    return None


def label_of(b):
    """A readable label from the image's own strings: the SCEJ sound module name ("name = socelverb", or the first
    soc* word) or the ELF's build path ("PS3_Release/water.spu.elf"). Empty when none is found."""
    m = re.search(rb"name = ([a-z0-9_]+)", b) or re.search(rb"(?<![A-Za-z0-9])(soc[a-z0-9]{2,12})(?![A-Za-z0-9])", b) \
        or re.search(rb"PS3_Release/([A-Za-z0-9_]+)\.spu\.elf", b) or re.search(rb"(hkpSpurs[A-Za-z]+)", b) \
        or re.search(rb"(TtCollQuery)[A-Za-z]+", b)
    return ("havok " if m and m.group(1).startswith((b"hkp", b"TtColl")) else "") + m.group(1).decode() if m else ""


def has_symbol(lift, name, sym):
    h = os.path.join(lift, "lift", name, "spu_recomp.h")
    return os.path.exists(h) and f"{sym}(" in open(h).read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lift", default=os.path.join(ROOT, "work/spu"), help="lift_spu.py --out directory")
    ap.add_argument("--elf-dir", default=os.path.join(ROOT, "work/spu"))
    ap.add_argument("--job-dir", default=os.path.join(ROOT, "work/spu-miss"))
    ap.add_argument("--only", default="", help="comma list of image names to register (default: all)")
    a = ap.parse_args()
    out = os.path.join(a.lift, "lift")
    R = json.load(open(os.path.join(a.lift, "spu_lift.json")))
    bad = [r["name"] for r in R if not r["ok"]]
    if bad:
        sys.exit(f"lift failed for {bad}; rerun tools/spu/lift_spu.sh")
    images, problems = [], []

    elfs = sorted((r for r in R if r["kind"] == "elf"), key=lambda r: r["file_offset"])
    jobs = sorted((r for r in R if r["kind"] == "job"), key=lambda r: r["name"])

    for i, r in enumerate(elfs):
        b = open(os.path.join(a.elf_dir, f"spu_{r['file_offset']:08x}.elf"), "rb").read()
        if b[:4] != b"\x7fELF" or be16(b, 0x12) != 0x17:
            problems.append(f"{r['name']}: not an SPU ELF")
            continue
        ent = be32(b, 0x18)
        sz = elf_image_size(b)
        images.append(dict(name=r["name"], kind="elf", image_id=ELF_IMAGE_BASE + i, fp=fnv1a64(b[:sz]),
                           size=sz, text_fp=text_fp(b), ea=r["file_offset"] + 0x10000, entry=ent,
                           label=label_of(b), entry_sym=f"{r['name']}_spu_func_{ent:08X}"))

    elf_id = {m["name"]: m["image_id"] for m in images if m["kind"] == "elf"}
    for r in sorted((r for r in R if r["kind"] == "elfseg"), key=lambda r: r["name"]):
        if r["parent"] not in elf_id:
            problems.append(f"{r['name']}: parent {r['parent']} not registered")
            continue
        images.append(dict(name=r["name"], kind="elfseg", image_id=elf_id[r["parent"]], parent=r["parent"],
                           size=r["size"], ea=r["file_offset"] + 0x10000, entry=r["base"], label="",
                           entry_sym=f"{r['name']}_spu_func_{r['base']:08X}"))

    for i, r in enumerate(jobs):
        fp = int(r["fp"], 16)
        raw = open(os.path.join(a.job_dir, f"spujob_{fp:016X}_{r['size']}.bin"), "rb").read()
        if fnv1a64(raw) != fp:   # the runtime's key: FNV-1a-64 over exactly sizeBinary bytes
            problems.append(f"{r['name']}: dump does not hash to its fingerprint")
            continue
        images.append(dict(name=r["name"], kind="job", image_id=JOB_IMAGE_BASE + i, fp=fp, size=len(raw), ea=0,
                           entry=r["base"], label=label_of(raw),
                           entry_sym=f"{r['name']}_spu_func_{r['base']:08X}"))

    order = {"elf": 0, "job": 1}
    images.sort(key=lambda m: order.get(m["kind"], 2))   # stable: ELF segments after every primary image
    if a.only:
        keep = set(a.only.split(","))
        images = [m for m in images if m["name"] in keep]

    # Checks: entry symbols exist, ids unique and not reserved, fingerprints unique.
    for m in images:
        if not has_symbol(a.lift, m["name"], m["entry_sym"]):
            problems.append(f"{m['name']}: entry symbol {m['entry_sym']} not in the lift")
    ids = [m["image_id"] for m in images if m["kind"] != "elfseg"]
    if len(set(ids)) != len(ids):
        problems.append("duplicate image ids")
    for m in images:
        if m["image_id"] in RESERVED:
            problems.append(f"{m['name']}: image id {m['image_id']} is special-cased by the runtime")
    fps = {}
    for m in images:
        for k in ("fp", "text_fp"):
            if m.get(k) is not None:
                fps.setdefault(m[k], set()).add(m["name"])
    dup_fps = {f"{k:016X}": sorted(v) for k, v in fps.items() if len(v) > 1}
    if dup_fps:
        problems.append(f"fingerprint collisions: {dup_fps}")
    if problems:
        sys.exit("\n".join(problems))

    L = ["/* spu_workloads.c -- GENERATED by tools/spu/gen_spu_register.py from the Toro Lets Party SPU lift.",
         " * Do not edit; derived from game code, never committed. Registers every lifted SPU image with ps3recomp's",
         " * runtime by FNV-1a-64 image fingerprint (spu_workload_register_img): the SPU ELFs (taskset tasks) and the",
         " * SPURS jobchain job binaries (spu_workload_dispatch_job). Each image's functions go in under its own image",
         " * id (spu_begin_image before its spu_recomp_register). */",
         "#include <stdint.h>",
         '#include "spu_workload.h"',
         "",
         "#ifndef SPU_ABI   /* patch 1099: lifted SPU functions' calling convention (spu_context.h) */",
         "#define SPU_ABI",
         "#endif",
         "extern void spu_begin_image(int image_id);",
         ""]
    for m in images:
        L.append(f"extern void {m['name']}_spu_recomp_register(void);")
        if m["kind"] in ("elf", "job"):
            L.append(f"extern SPU_ABI void {m['entry_sym']}(spu_context*);")
    L += ["", "unsigned tlp_spu_image_count = %du;" % sum(m["kind"] != "elfseg" for m in images), "",
          "void tlp_spu_register_all(void)", "{",
          "    static int done;", "    if (done) return;", "    done = 1;"]
    for m in images:
        where = f"EA 0x{m['ea']:08X}" if m["kind"] != "job" else "game data (SPU_DUMP_MISS)"
        L.append(f"    /* {m['name']}: {m['kind']} {where}, {m['size']} bytes, {m['label'] or '?'} */")
        L.append(f"    spu_begin_image({m['image_id']}); {m['name']}_spu_recomp_register();")
        if m["kind"] in ("elf", "job"):
            L.append(f"    spu_workload_register_img(0x{m['fp']:016X}ULL, {m['entry_sym']}, {m['image_id']}, "
                     f"\"{m['name']}\");")
        if m.get("text_fp") is not None:
            L.append(f"    spu_workload_register_img(0x{m['text_fp']:016X}ULL, {m['entry_sym']}, "
                     f"{m['image_id']}, \"{m['name']}.text\");")
    L += ["    spu_begin_image(0);", "}", "",
          "/* Registers before main(), i.e. before the game adds any SPURS workload or job chain. */",
          "__attribute__((constructor)) static void tlp_spu_register_ctor(void)", "{",
          "    tlp_spu_register_all();", "}", ""]
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, "spu_workloads.c"), "w").write("\n".join(L))
    for m in images:
        for k in ("fp", "text_fp"):
            if m.get(k) is not None:
                m[k] = f"0x{m[k]:016X}"
    json.dump(images, open(os.path.join(a.lift, "tlp_spu_manifest.json"), "w"), indent=1)
    n = {k: sum(1 for m in images if m["kind"] == k) for k in ("elf", "job", "elfseg")}
    print(f"registered {len(images) - n['elfseg']} images: {n['elf']} ELFs, {n['job']} jobchain jobs; "
          f"{n['elfseg']} extra ELF code segment(s)")
    for m in images:
        if m["kind"] != "elfseg":
            print(f"  id {m['image_id']:3d} {m['name']:24s} fp {m['fp']} {m['size']:7d} B  {m['label']}")
    print(f"wrote {out}/spu_workloads.c, {a.lift}/tlp_spu_manifest.json")


if __name__ == "__main__":
    main()
