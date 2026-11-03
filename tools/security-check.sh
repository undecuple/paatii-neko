#!/usr/bin/env bash
# Mechanical security checks (PM's security review, shared-intake security-review-brief.md layer 1, 2026-10-19).
#   tools/security-check.sh          check what is staged (called by .githooks/pre-commit)
#   tools/security-check.sh --all    check every tracked file (a full-tree audit; added-line checks are skipped)
# Blocks: secrets and key patterns, PS3 keys or key/licence files, game-derived files (path, extension, contents),
# any new binary or archive, submodule moves, new download/install commands, unpinned package installs.
# Allowed: checkpoint screenshots under docs/checkpoints/ (committed on purpose) and the README shots in
# docs/screenshots/ (picked by hand) and the banner/social preview in docs/assets/ (tools/release/repo_art.py).
# SECURITY_OK=1 git commit ... overrides a block; say why in the message.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)" || exit 2
ALL=0; [[ "${1:-}" == --all ]] && ALL=1
fail=0
say() { echo "security-check: $*" >&2; fail=1; }
# Blob content: staged index version, or the committed one in --all mode.
blob() { if (( ALL )); then git show "HEAD:$1" 2>/dev/null; else git show ":$1" 2>/dev/null; fi; }

if (( ALL )); then files="$(git ls-files)"; added="$files"
else
  files="$(git diff --cached --name-only --diff-filter=ACMR)"
  added="$(git diff --cached --name-only --diff-filter=A)"
fi
[[ -z "$files" ]] && exit 0

# 1. Secrets and key patterns (contents of every text file checked).
secret_re='sk-ant-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[0-9A-Z]{16}|xox[abposr]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|discord(app)?\.com/api/webhooks/[0-9]+/[A-Za-z0-9_-]+|tvly-[A-Za-z0-9]{20,}'
# PS3 key material: erk/riv/klicensee/idps assignments with a 32+ hex value.
ps3key_re='(erk|riv|klic(ensee)?|idps|psid|rap|dev_klic)[^A-Za-z0-9]{1,6}(0x)?[0-9A-Fa-f]{32,}'
while IFS= read -r f; do
  [[ -z "$f" || "$f" == tools/security-check.sh ]] && continue
  if blob "$f" | grep -qIE "$secret_re"; then say "secret or token pattern in $f"; fi
  if blob "$f" | grep -qIiE "$ps3key_re"; then say "PS3 key material pattern in $f"; fi
done <<<"$files"

# 2. Game-derived files by path, name and extension (disc, update, decrypted binaries, dumps, licences, media).
game_path_re='^(Game|Game-JP|GameUpdate|assets|work|build)/|(^|/)(EBOOT\.(BIN|elf)|PARAM\.SFO|PS3_DISC\.SFB|act\.dat|idps|keys\.txt)$'
game_ext_re='\.(self|sprx|prx|elf|pup|pkg|psarc|sdat|edat|rap|pam|pamf|bik|at3|vag|gtf|core|corestream|iso|dmp|sav)$'
while IFS= read -r f; do
  [[ -z "$f" ]] && continue
  if grep -qiE "$game_path_re|$game_ext_re" <<<"$f"; then say "game-derived path/extension: $f"; fi
done <<<"$files"

# 3. Contents: file signatures of SELF/SCE, PPU/SPU ELFs, SDAT/EDAT (NPD), PARAM.SFO (PSF), PAMF, PUP.
while IFS= read -r f; do
  [[ -z "$f" ]] && continue
  head="$(blob "$f" | head -c 20 | od -An -tx1 | tr -d ' \n')"
  case "$head" in
    53434500*) say "SCE/SELF header in $f" ;;
    4e504400*) say "NPD (SDAT/EDAT) header in $f" ;;
    00505346*) say "PSF (PARAM.SFO) header in $f" ;;
    50414d46*) say "PAMF video header in $f" ;;
    53434555*) say "PUP header in $f" ;;
    7f454c460202*)  # 64/32-bit big-endian ELF: e_machine at byte 18 (0x15 PPC64, 0x17 SPU)
      m="${head:36:4}"; [[ "$m" == 0015 || "$m" == 0017 ]] && say "PS3 PPU/SPU ELF in $f" ;;
  esac
done <<<"$files"

# 4. New binaries or archives (added files only). Checkpoint PNGs and the README screenshots are allowed.
archive_re='\.(zip|7z|rar|tar|gz|tgz|xz|zst|bz2|cab|msi|exe|dll|so|dylib|a|lib|bin|img|dat)$'
if [[ -n "$added" ]]; then
  while IFS= read -r f; do
    [[ -z "$f" || "$f" =~ ^docs/(checkpoints|screenshots|assets)/[^/]+\.png$ ]] && continue
    if grep -qiE "$archive_re" <<<"$f"; then say "new archive/executable: $f"; continue; fi
    if (( ALL )); then num="$(git diff --numstat 4b825dc642cb6eb9a060e54bf8d69288fbee4904 HEAD -- "$f" | cut -f1)"
    else num="$(git diff --cached --numstat -- "$f" | cut -f1)"; fi
    # git calls a file binary only when it has a NUL byte; a file that is not valid UTF-8 counts as binary too.
    if [[ "$num" == "-" ]] || blob "$f" | LC_ALL=C.UTF-8 grep -qaxv '.*'; then say "new binary file: $f"; fi
  done <<<"$added"
fi

# 5. Submodule moves and .gitmodules changes (staged mode only; --all lists the current pins instead).
if (( ! ALL )); then
  if git diff --cached --raw | awk '$1 ~ /^:160000/ || $2 == "160000"' | grep -q .; then
    say "submodule pointer moved: $(git diff --cached --raw | awk '$1 ~ /^:160000/ || $2 == "160000" {print $NF}' | tr '\n' ' ')"
  fi
  grep -qx '.gitmodules' <<<"$files" && say ".gitmodules changed (submodule URL/branch)"
fi

# 6. Added lines that download, install or fetch (code files; docs may describe commands).
if (( ! ALL )); then
  dl_re='\b(curl|wget|aria2c|Invoke-WebRequest|iwr|Start-BitsTransfer|certutil[^\n]*-urlcache)\b|fetchurl|fetchFromGitHub|fetchTarball|builtins\.fetch|pip3? install|npm (i|install)|cargo install|go install|git clone|nix profile install|https?://[^ "'"'"')>]+\.(exe|msi|zip|7z|tar|gz|xz|sh|ps1|dll)\b'
  # This script is left out: its own patterns name the commands it looks for.
  mapfile -t code_files < <(grep -vE '^(docs/|[A-Z]+\.md$|tools/security-check\.sh$)' <<<"$files" || true)
  if [[ ${#code_files[@]} -gt 0 && -n "${code_files[0]}" ]]; then
    hits="$(git diff --cached -U0 -- "${code_files[@]}" 2>/dev/null | grep -E '^\+[^+]' | grep -E "$dl_re" || true)"
    [[ -n "$hits" ]] && say "new download/install/fetch lines:"$'\n'"$(sed 's/^/    /' <<<"$hits" | head -20)"
    # Unpinned installs: pip without ==.
    unp="$(git diff --cached -U0 -- "${code_files[@]}" 2>/dev/null | grep -E '^\+[^+]' \
      | grep -E 'pip3? install [^-]' | grep -vE '==|-r |--requirement' || true)"
    [[ -n "$unp" ]] && say "unpinned pip install:"$'\n'"$(sed 's/^/    /' <<<"$unp")"
  fi
  # flake.nix inputs changed without flake.lock (unpinned dependency move).
  if grep -qx 'flake.nix' <<<"$files" && git diff --cached -U0 -- flake.nix | grep -qE '^\+.*\binputs\b|^\+.*\burl *='; then
    grep -qx 'flake.lock' <<<"$files" || say "flake.nix inputs changed without flake.lock"
  fi
fi

if (( fail )); then
  if [[ "${SECURITY_OK:-0}" == 1 ]]; then echo "security-check: overridden by SECURITY_OK=1 (say why in the commit message)" >&2; exit 0; fi
  echo "security-check: blocked. Fix it, or SECURITY_OK=1 with the reason in the commit message." >&2; exit 1
fi
exit 0
