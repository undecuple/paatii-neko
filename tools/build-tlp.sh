#!/usr/bin/env bash
# Toro Lets Party: from an earlier port by the same author (names swapped).
# Memory-safe Windows build of port/tlp, one build at a time on the machine shared with the Killzone 3 port.
# From KZ3 78bf574 tools/build-kz3.sh (KZ3_* -> TLP_*; configures the build dir itself when it has no CMakeCache.txt;
# no SPU registration step yet). Run inside the sandbox:
#   nix develop .#win --command tools/sandbox.sh -- tools/build-tlp.sh build/tlp-win [extra cmake --build args]
#   (a lane: ... tools/sandbox.sh -- env TLP_OUT=work/runtime tools/build-tlp.sh build/tlp-win)
# Inputs: $TLP_OUT/ps3recomp-patched (tools/ps3recomp-patched.sh) and $TLP_OUT/recomp (tools/lift.sh); TLP_OUT
# defaults to work.
# Memory (KZ3's measurements, 2026-10-08..11): a cc1plus on a 64-chunk lifted file peaks at 0.7-1.3 GB (KZ3 saw up to
# 5.3 GB on some), an old 600k-line chunk 6.7 GB; -j8/-j20 next to Proton ran the 31 GB machine out of memory three
# times. So: jobs = (MemAvailable - 8 GB reserve) / TLP_BUILD_JOB_MB (default 2048: the brief's 1.5-2.5 GB per lifted
# chunk) / build slots in use, 1..TLP_BUILD_JOBS_MAX (default 6); oom_score_adj 1000 (this build dies first, not the
# editor); one build slot of KZ3's lock directory (shared: KZ3's builds and ours queue together; a lift takes them all).
set -euo pipefail
DIR="${1:?usage: build-tlp.sh BUILD_DIR [cmake --build args]}"; shift
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${TLP_OUT:-work}"; case "$OUT" in /*) ;; *) OUT="$ROOT/$OUT" ;; esac
PT="$OUT/ps3recomp-patched"
MAINC="$ROOT"; [[ -f "$ROOT/.tlp-main" ]] && MAINC="$(cat "$ROOT/.tlp-main")"
LOCKS="${TLP_LOCK_DIR:-$(cat "$MAINC/.tlp-lockdir" 2>/dev/null || echo "$MAINC/work/locks")}"
[[ "$LOCKS" == "$MAINC/work/locks" ]] && mkdir -p "$LOCKS"   # only the repo's own lock dir is created
[[ -d "$LOCKS" ]] || { echo "build-tlp: $LOCKS missing (lock directory from .tlp-lockdir)" >&2; exit 2; }
# Refuse a patched toolkit older than the patch set (TLP_ALLOW_STALE_PATCHES=1 overrides).
[[ -f "$PT/CMakeLists.txt" ]] || { echo "build-tlp: no $PT: run tools/ps3recomp-patched.sh first" >&2; exit 3; }
if [[ "${TLP_ALLOW_STALE_PATCHES:-0}" != 1 ]]; then
  want="$(cat "$ROOT"/port/patches/*.patch | sha256sum | cut -c1-16)-$(git -C "$ROOT/third_party/ps3recomp" rev-parse --short HEAD 2>/dev/null)"
  have="$(cat "$PT/.tlp-patchset" 2>/dev/null || true)"
  [[ "$have" == "$want" ]] || { echo "build-tlp: $PT is stale ($have, want $want): run tools/ps3recomp-patched.sh first" >&2; exit 3; }
fi
# Configure once: MinGW toolchain (port/cmake), the patched toolkit, the lift.
GO="${TLP_BUILD_GUARDS_ONLY:-0}"   # guards only: check, never configure (the remote client runs this outside the nix shell)
if [[ "$GO" != 1 && ! -f "$DIR/CMakeCache.txt" ]]; then
  cmake -S "$ROOT/port/tlp" -B "$DIR" -G Ninja -DCMAKE_TOOLCHAIN_FILE="$ROOT/cmake/mingw-w64.cmake" \
    -DCMAKE_BUILD_TYPE=RelWithDebInfo -DPython3_EXECUTABLE="$(command -v python3)" \
    -DPS3RECOMP_DIR="$PT" -DRECOMP_DIR="$OUT/recomp" >"$DIR.configure.log" 2>&1 \
    || { tail -20 "$DIR.configure.log" >&2; exit 4; }
fi
# Re-configure when the patched toolkit changed: ps3recomp collects its sources with file(GLOB_RECURSE) without
# CONFIGURE_DEPENDS, so a patch that adds a source file (6003's cellSpursLFQueue.c) is not linked from an old cache
# (the link then fails with undefined _cellSpursLFQueuePushBody).
pt_stamp="$(cat "$PT/.tlp-patchset" 2>/dev/null || true)"
if [[ "$GO" != 1 && "$(cat "$DIR/.tlp-toolkit-stamp" 2>/dev/null || true)" != "$pt_stamp" ]]; then
  cmake -S "$ROOT/port/tlp" -B "$DIR" >>"$DIR.configure.log" 2>&1 || { tail -20 "$DIR.configure.log" >&2; exit 4; }
  echo "$pt_stamp" > "$DIR/.tlp-toolkit-stamp"
fi
# Lifted SPU images (tools/spu/lift_spu.sh): point the cache at $OUT/spu/lift when it has a registration TU
# (the CMake default port/tlp/spu does not exist). TLP_SPU=0 builds without them.
SPU_LIFT="$OUT/spu/lift"
if [[ "${TLP_SPU:-1}" != 0 && -f "$SPU_LIFT/spu_workloads.c" ]]; then want_spu="$SPU_LIFT"; else want_spu="$ROOT/port/tlp/spu"; fi
if [[ "$GO" != 1 && "$(sed -n 's/^SPU_DIR:[A-Z]*=//p' "$DIR/CMakeCache.txt" 2>/dev/null)" != "$want_spu" ]]; then
  cmake -S "$ROOT/port/tlp" -B "$DIR" -DSPU_DIR="$want_spu" >>"$DIR.configure.log" 2>&1 || { tail -20 "$DIR.configure.log" >&2; exit 4; }
fi
# The lift must announce exactly the overrides of its EBOOT's list (a host override is compiled only when the lift
# announced PPU_OVERRIDE_<addr>): port/ppu_overrides.txt for 1.29, ppu_overrides-101.txt for v1.01, by the ver=
# of the lift's .lift-stamp (tools/lift.sh; a stamp without ver= is a v1.01 lift); TLP_ALLOW_STALE_LIFT=1 overrides.
recomp_l="$(sed -n 's/^RECOMP_DIR:[A-Z]*=//p' "$DIR/CMakeCache.txt" 2>/dev/null || true)"; recomp_l="${recomp_l:-$OUT/recomp}"
ann="$recomp_l/ppu_overrides.h"; [[ -f "$ann" ]] || ann="$recomp_l/ppu_recomp.h"
ovr_list="$ROOT/port/ppu_overrides.txt"   # one EBOOT version (BCAS20087)
if [[ -f "$ann" && "${TLP_ALLOW_STALE_LIFT:-0}" != 1 ]]; then
  want="$( (grep -oE '^[[:space:]]*[0-9A-Fa-f]{8}' "$ovr_list" || true) | tr -d ' \t' | tr a-f A-F | sort -u)"
  have="$( (grep -oE 'PPU_OVERRIDE_[0-9A-Fa-f]{8}' "$ann" || true) | cut -c14- | tr a-f A-F | sort -u)"
  [[ "$want" == "$have" ]] || { echo "build-tlp: the lift in $recomp_l does not match ${ovr_list#$ROOT/}: run tools/lift.sh" >&2; exit 3; }
fi
# Guards only (the remote build client, tools/remote/tlpremote.py): the checks above passed, build nothing here.
[[ "${TLP_BUILD_GUARDS_ONLY:-0}" == 1 ]] && { echo "build-tlp: guards ok" >&2; exit 0; }
# Build slots across checkouts (tools/agents/slotlock.sh, private tooling): skipped when it is not there.
SLOTS="${TLP_BUILD_SLOTS:-1}"; [[ "$SLOTS" =~ ^[1-9][0-9]*$ ]] || SLOTS=1; SLOT=none; in_use=1
if [[ -f "$ROOT/tools/agents/slotlock.sh" ]]; then
  # shellcheck source=agents/slotlock.sh
  source "$ROOT/tools/agents/slotlock.sh"
  if [[ " ${TLP_HELD_LOCKS:-} " == *" build "* ]]; then SLOT=held   # run under the build lock
  else slot_take "$LOCKS" build "$SLOTS"; fi
  in_use=$(slot_held "$LOCKS" build "$SLOTS"); (( in_use < 1 )) && in_use=1
elif [[ " ${TLP_HELD_LOCKS:-} " != *" build "* ]]; then
  # Toro has no slotlock.sh, and KZ3's shared lock dir is not mounted in the sandbox: the slot must be taken outside
  # it (2026-10-19: builds ran without one, unseen). Wrap the whole command, as KZ3's guide says:
  #   "<KZ3>/tools/agents/lock.sh" build -- nix develop .#win --command tools/sandbox.sh -- \
  #     env TLP_HELD_LOCKS=build tools/build-tlp.sh build/tlp-win
  echo "build-tlp: WARNING: no shared build slot held (run under KZ3's tools/agents/lock.sh build, see header)" >&2
fi
echo 1000 > /proc/self/oom_score_adj 2>/dev/null || true
avail_mb=$(( $(awk '/MemAvailable/{print $2}' /proc/meminfo) / 1024 ))
job_mb="${TLP_BUILD_JOB_MB:-2048}"; jobs_max="${TLP_BUILD_JOBS_MAX:-6}"
jobs=$(( (avail_mb - 8192) / job_mb / in_use )); (( jobs < 1 )) && jobs=1; (( jobs > jobs_max )) && jobs=$jobs_max
# Optional temporary cap in the lock directory (build-cap = "EXPIRY_EPOCH MAXJOBS").
if read -r cap_until cap_jobs < "$LOCKS/build-cap" 2>/dev/null && (( $(date +%s) < cap_until )); then
  (( jobs > cap_jobs )) && jobs=$cap_jobs; renice -n 10 -p $$ >/dev/null 2>&1 || true
fi
echo "build-tlp: $DIR with -j$jobs ($(( avail_mb / 1024 )) GB available; build slot $SLOT)" >&2
if command -v ccache >/dev/null && [[ "${TLP_CCACHE:-1}" != 0 ]]; then
  export CCACHE_DIR="$OUT/ccache" CCACHE_BASEDIR="$ROOT" CCACHE_MAXSIZE=20G CCACHE_COMPRESS=1
  grep -q '^CMAKE_CXX_COMPILER_LAUNCHER:.*=ccache' "$DIR/CMakeCache.txt" 2>/dev/null \
    || cmake -DCMAKE_C_COMPILER_LAUNCHER=ccache -DCMAKE_CXX_COMPILER_LAUNCHER=ccache "$DIR" >/dev/null
fi
t0=$(date +%s); rc=0
cmake --build "$DIR" -j"$jobs" "$@" || rc=$?
echo "build-tlp: done in $(( $(date +%s) - t0 )) s (-j$jobs, exit $rc)" >&2
exit $rc
