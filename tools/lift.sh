#!/usr/bin/env bash
# Reproducible PPU lift of the BCAS20087 EBOOT with ps3recomp + port/patches (after KZ3's tools/lift.sh at cb9b9486).
#
#   "$SHARED_LOCKS/lock.sh" build -- \
#     nix develop .#re --command tools/sandbox.sh -- tools/lift.sh
#
# (Shared machine: take the build lock outside the sandbox; $SHARED_LOCKS = the machine's lock tooling, see
# the private notes. A single-user machine can drop the wrapper.)
# 1. work/ps3recomp-patched = third_party/ps3recomp at its pinned commit + every port/patches/*.patch
#    (fresh each run, tools/ps3recomp-patched.sh).
# 2. ppu_loader + find_functions into work/analysis (if functions.json is missing).
# 3. ppu_lifter with --code-end 0x5c1d2c (end of the last executable section; .rodata follows), --toc 0x8790d0 (the
#    entry OPD at 0x854558 = {0x10230, 0x8790d0}), --overrides port/ppu_overrides.txt (patch 1018), --chunks 64
#    (patch 3005) into work/recomp.
# 4. lift_audit into work/analysis/lift_audit.log.
# Needs work/bin/EBOOT.elf: the game's main program as a plain ELF, made from your own copy.
set -euo pipefail
echo 1000 > /proc/self/oom_score_adj 2>/dev/null || true   # first OOM victim, not the editor
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PT=work/ps3recomp-patched
ELF=work/bin/EBOOT.elf; CODE_END=0x5c1d2c; TOC=0x8790d0; AN=work/analysis; OUT=work/recomp
OVR=port/ppu_overrides.txt
CHUNKS="${TLP_LIFT_CHUNKS:-64}"
[[ -f "$ELF" ]] || { echo "missing $ELF (put the plain ELF of your own EBOOT there first)" >&2; exit 1; }
[[ -f "$OVR" ]] || { echo "missing $OVR" >&2; exit 1; }

"$ROOT/tools/ps3recomp-patched.sh"

mkdir -p "$AN" "$OUT"
if [[ ! -f "$AN/functions.json" ]]; then
  python3 "$PT/tools/ppu_loader.py" "$ELF" -o "$AN/"
  python3 "$PT/tools/find_functions.py" "$ELF" --seed-json "$AN/EBOOT.functions.json" \
    --output "$AN/functions.json"
fi

python3 "$PT/tools/ppu_lifter.py" "$ELF" --functions "$AN/functions.json" \
  --hle-stubs "$AN/EBOOT.imports.json" --toc "$TOC" --code-end "$CODE_END" \
  --overrides "$OVR" -j 4 --chunks "$CHUNKS" --output "$OUT" > "$OUT/lift.log" 2>&1
tail -5 "$OUT/lift.log"
printf 'elf=%s overrides=%s patchset=%s chunks=%s date=%s\n' "$ELF" "$(sha256sum "$OVR" | cut -c1-16)" \
  "$(cat "$PT/.tlp-patchset" 2>/dev/null)" "$CHUNKS" "$(date -Is)" > "$OUT/.lift-stamp"

python3 "$PT/tools/lift_audit.py" --elf "$ELF" --functions "$AN/functions.json" \
  --recomp-dir "$OUT" --baseline "$AN/none.json" > "$AN/lift_audit.log" 2>&1 || true
sed -n '/=== Pass 1/,/TOTAL \/\* unresolved/p' "$AN/lift_audit.log"
