#!/usr/bin/env bash
# From Killzone 3 95b4038a tools/spu/lift_spu.sh, by way of Killzone 2's adaptation (uses the patched tree
# tools/ps3recomp-patched.sh made, output under $TLP_OUT/spu where tools/build-tlp.sh looks for it).
# Lift Toro Lets Party's SPU code (the 5 SPU ELFs embedded in the EBOOT and the SPURS jobchain job binaries the
# runtime dumped with SPU_DUMP_MISS) and write the registration TU the port build picks up.
#
#   nix develop .#re --command tools/sandbox.sh -- tools/spu/lift_spu.sh [-j N] [--only NAME,...]
#
# Needs $TLP_OUT/ps3recomp-patched (tools/ps3recomp-patched.sh), work/spu/spu_<fo>.elf (tools/elf_info.py dump) and
# work/spu-miss/spujob_<FP>_<N>.bin (a run with SPU_DUMP_MISS=work/spu-miss). Outputs (derived from game code, never
# committed; TLP_OUT defaults to work):
#   $TLP_OUT/spu/lift/<image>/spu_recomp.{c,h}, lift.log   one dir per image (elf_<fo>, job_<FP>)
#   $TLP_OUT/spu/lift/spu_workloads.c                       tlp_spu_register_all() (tools/spu/gen_spu_register.py)
#   $TLP_OUT/spu/spu_lift.json, tlp_spu_manifest.json, elf_in/ (wrapped inputs)
# Then build: tools/build-tlp.sh passes -DSPU_DIR=$TLP_OUT/spu/lift when that directory has a spu_workloads.c.
set -euo pipefail
echo 1000 > /proc/self/oom_score_adj 2>/dev/null || true
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
OUT="${TLP_OUT:-work}"
PT="$OUT/ps3recomp-patched"
[[ -f "$PT/tools/spu_lifter.py" ]] || { echo "no $PT: run tools/ps3recomp-patched.sh first" >&2; exit 3; }
S="$OUT/spu"
# A build re-globs SPU_DIR, so a lift replacing it mid-build breaks that build: hold every build
# slot when the slot tooling exists (tools/agents/slotlock.sh, as tools/build-tlp.sh).
if [[ -f "$ROOT/tools/agents/slotlock.sh" ]]; then
  MAINC="$ROOT"; [[ -f "$ROOT/.tlp-main" ]] && MAINC="$(cat "$ROOT/.tlp-main")"
  LOCKS="${TLP_LOCK_DIR:-$(cat "$MAINC/.tlp-lockdir" 2>/dev/null || echo "$MAINC/work/locks")}"
  # shellcheck source=../agents/slotlock.sh
  source "$ROOT/tools/agents/slotlock.sh"; slot_take_all "$LOCKS" build "${TLP_BUILD_SLOTS:-1}"
fi
for d in "$S/lift" "$S/elf_in"; do [[ -e "$d" ]] && "$ROOT/tools/safe_rm.sh" "$d"; done
mkdir -p "$S"
python3 tools/spu/lift_spu.py --ps3recomp "$PT" --out "$S" --elf-dir work/spu --job-dir work/spu-miss "$@"
python3 tools/spu/gen_spu_register.py --lift "$S" --elf-dir work/spu --job-dir work/spu-miss
