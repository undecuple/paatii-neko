# Building the port

The port's executable is generated from **your own copy** of the game. The game's code is lifted to C from your
decrypted executable and compiled on your machine. Nothing of the game is in this repository, and nothing is
downloaded.

**v0.1.0 is a source preview.** You get the source, with the pinned ps3recomp submodule, and build the exe yourself.
There is no installer, no portable zip and no exe to download: the exe contains code lifted from your copy of the game,
so it cannot be shared. The release attaches one source archive that includes `third_party/ps3recomp`, and a
`SHA256SUMS` file for it. A plain "download ZIP" of the repository lacks the submodule and cannot build; use the
attached archive or `git clone --recursive`.

**Only tested under Proton on Linux.** The exe has never been run on real Windows.

**ps3recomp pin:** submodule commit `0fe7dbf5` (`git submodule status` shows it), with 218 patch files from
`port/patches/` applied on top. Upstream ps3recomp has newer releases (v0.19.0, v0.20.0); this pin does not have them.

## What is tested

| Where | Status |
|---|---|
| Linux with Nix (developed on NixOS): lift, MinGW-w64 cross-build to a Windows x64 exe, run under Proton | **Tested** in the development tree; this is the only path that has been run. A fresh clone of this repository (or of the source archive) has **not** been built end to end, and neither has a build that starts from nothing but the steps below. |
| Other Linux distributions with Nix installed | Not tested. The steps should be the same. |
| Windows (native build, or WSL2 build) | **Not tested.** The exe has never been run on real Windows. |
| macOS (build or run) | **Not tested.** The macOS shells exist in the flake, but no build has been run on a Mac. |

## What you need

From your own copy of the game:

| Item | Notes |
|---|---|
| The game's executable for disc **BCAS20087** ("TORO ! Let's Party !"), decrypted to a plain ELF | Your own legally dumped copy. This project does not provide it, keys, or instructions for decrypting it. |
| The rest of the disc's files | Only needed to run the game, not to build. The exe expects them laid out as on the disc (`PS3_GAME/USRDIR/...`). |

To build: Linux with [Nix](https://nixos.org/) (flakes enabled), plenty of RAM (16 GB or more; the lifted source is
compiled in 64 chunks, each needing roughly 1 to 2 GB) and tens of GB of free disk. To run: a GPU and driver with
Direct3D 12 (on Linux, through Proton). Only one PC has been used (NixOS, NVIDIA RTX 4060, GE-Proton11-7); AMD and Intel GPUs have not been tried.

## Toolchain

Everything comes from the Nix flake; nothing needs to be installed system-wide.

```sh
nix develop .#re     # lifting and analysis: Python with capstone/pyelftools, bubblewrap
nix develop .#win    # Windows x64 cross build: MinGW-w64, CMake, Ninja, SDL3 for Windows
nix develop .#run    # test runs under Proton: steam-run, Xvfb, ImageMagick
nix develop          # everything above plus the reference tools
```

`tools/sandbox.sh [--gpu] -- CMD` runs a command with the repository read-only and only `work/` and `build/`
writable, with no network. The steps below run inside it. It needs bubblewrap, which `nix develop` provides on Linux.

## Steps

```sh
git clone --recursive https://github.com/undecuple/paatii-neko
cd paatii-neko
git submodule update --init                    # third_party/ps3recomp, pinned

# 1. Put your decrypted executable where the scripts look for it (it stays out of git)
mkdir -p work/bin && cp /path/to/your/EBOOT.elf work/bin/EBOOT.elf

# 2. Patched recompiler: a fresh copy of the pinned ps3recomp with port/patches/*.patch applied
nix develop .#re --command tools/sandbox.sh -- tools/ps3recomp-patched.sh

# 3. Lift the PPU code to C (writes work/recomp/)
nix develop .#re --command tools/sandbox.sh -- tools/lift.sh

# 4. Read the SPU programs out of your EBOOT and lift them (see "Lifting the SPU code" below)
nix develop .#re --command tools/sandbox.sh -- python3 tools/elf_info.py work/bin/EBOOT.elf --spu-dir work/spu --job-dir work/spu-miss
nix develop .#re --command tools/sandbox.sh -- tools/spu/lift_spu.sh

# 5. Compile the exe (configures build/tlp-win on the first run)
nix develop .#win --command tools/sandbox.sh -- tools/build-tlp.sh build/tlp-win
```

`tools/lift.sh` runs step 2 itself, so step 2 on its own is only a check that the patches apply.

Before it lifts anything, `tools/lift.sh` checks that `work/bin/EBOOT.elf` is the build the port is made from
(`tools/release/eboot_ids.py`, table `tools/release/eboot_ids.json`: TORO ! Let's Party ! BCAS20087, version 01.00). The
Japanese release, another version or a still-encrypted file stops it with a plain message; a copy of the right release
that is not a known one only warns. With the disc folder at `Game/` (or `TLP_DISC=<folder that holds PS3_GAME>`) its
`PARAM.SFO` is checked too. The same check on its own: `python3 tools/release/eboot_ids.py --eboot work/bin/EBOOT.elf`.

The result is `build/tlp-win/tlp.exe`, a Windows x64 program. It needs `SDL3.dll` next to it:

```sh
nix develop .#win --command python3 tools/release/stage_sdl3.py --out work/stage/tlp
cp build/tlp-win/tlp.exe work/stage/tlp/
```

After a change to a file in `port/patches/` or to `port/ppu_overrides.txt`, rerun steps 2 to 5. The build refuses
a patched tree or a lift that no longer matches them.

### Lifting the SPU code

The game's SPU programs are lifted separately, with `tools/spu/lift_spu.sh`, before the build. `tools/build-tlp.sh`
picks up the result (in `work/spu/lift`) when it exists. Both kinds of SPU program are read straight out of your
`EBOOT.elf`: the 5 SPU programs built into it go to `work/spu/`, and the 12 SPURS job programs (listed in a table in
the executable) go to `work/spu-miss/`, which is where `lift_spu.sh` reads them.

```sh
nix develop .#re --command tools/sandbox.sh -- python3 tools/elf_info.py work/bin/EBOOT.elf --spu-dir work/spu --job-dir work/spu-miss
nix develop .#re --command tools/sandbox.sh -- tools/spu/lift_spu.sh
```

This is step 4 of [Steps](#steps): do it before `tools/build-tlp.sh`. Without the lifted SPU code the game stops at a black screen at boot: it waits
for an SPU job that the port cannot run. Nothing in this repository downloads or ships the SPU programs.

If a run ever logs `[spurs-job] dispatch MISS`, the game asked for a job that is not in the table: run it once with
`SPU_DUMP_MISS=work/spu-miss` set (the runtime then writes that job there), then run `lift_spu.sh` and the build
again, and please open an issue with the line.

## Running

Windows risk: the exe links `msvcrt.dll` and is built without Control Flow Guard (checked statically on a 2026-11-09
build). The SPU code uses `_setjmp` and `longjmp` without a stack frame. On real Windows with Exploit Protection
forcing Control Flow Guard on, this may end the process with error 0xC0000409; the Killzone 2 and 3 ports hit it with
the same code shape. Wine and Proton do not show it. See [KNOWN_ISSUES.md](KNOWN_ISSUES.md).

The exe takes the path of the decrypted EBOOT as its one argument. The game's folder is found by going up three
levels from it, so the layout must be `<game folder>/PS3_GAME/USRDIR/EBOOT.elf`. Set `PS3_VFS_ROOT` to use a
different game folder.

On Linux with Proton (tested), from the repository:

```sh
nix develop .#run --command tools/proton-test.sh --seconds 60 --name boot \
    work/stage/tlp/tlp.exe /path/to/game-folder/PS3_GAME/USRDIR/EBOOT.elf
```

`tools/proton-test.sh` runs the exe in a hidden Xvfb display with audio drivers off, in its own Wine prefix. It uses
a GE-Proton install from Steam's `compatibilitytools.d` folder by default (`--proton DIR` picks another). The
program's output goes to `work/proton/NAME/app/app_stdout.txt` and a screenshot to `work/shots/NAME.png`.

## Building on macOS

**Status: not tested.** The flake defines macOS shells (`.#re`, `.#win`, default, `.#ci`) for Apple silicon, but
no build has been run on a Mac. The steps below follow from the scripts and may need changes.

- **Likely route:** install [Nix](https://nixos.org/download/) with flakes enabled on a Mac with Apple silicon, then
  follow [Steps](#steps) 1 to 5 with `nix develop .#re` and `nix develop .#win` as written. On macOS
  `tools/sandbox.sh` runs the command directly, with no sandbox (bubblewrap is Linux-only), and says so.
- **Running:** `tlp.exe` is a Windows program, and Proton does not run on macOS. The likely route is to copy the exe
  and the game folder to a Windows PC. Windows compatibility layers for macOS have not been tried.

## Building on Windows

**Status: not tested.** Neither a build on Windows nor running the exe on real Windows has been done. The exe has
only been run under Proton on Linux.

- **Likely route:** Nix does not run on Windows itself, so build inside WSL2 (Linux on Windows) with Nix
  installed, and follow [Steps](#steps) 1 to 5. Keep the repository inside the Linux file system, not on the
  Windows drive, and give WSL2 enough memory (see [What you need](#what-you-need)). The sandbox script has not been
  tried inside WSL2.
- **Running:** copy `tlp.exe` and `SDL3.dll` into a folder, and run
  `tlp.exe path\to\PS3_GAME\USRDIR\EBOOT.elf` in a terminal. Untested.
- A native Windows build without WSL2 is not set up. The build scripts are written for Linux shells.

## Other Linux distributions

Install Nix with flakes enabled and follow [Steps](#steps). Not tested outside NixOS. The Proton runner points
Vulkan at an NVIDIA file in a NixOS location (`/run/opengl-driver/share/vulkan/icd.d/nvidia_icd.json`); adjust
`VK_ICD_FILENAMES` in `tools/proton-inner.sh` for your distribution (path of your GPU's Vulkan ICD `.json` file).

## Repository layout

```
.github/              CI, the secrets scan, issue forms, contributing and security pages
cmake/                the MinGW-w64 cross toolchain file
docs/                 status, features, known issues, building, how it works and the other pages
licenses/             full licence texts of the third-party parts (index: licenses/README.md)
port/patches/         this port's changes to ps3recomp, applied in order to a copy of the submodule
port/tlp/             the port's own host code: main, system-function replacements, defaults
third_party/ps3recomp the recompiler and runtime (git submodule, pinned, unmodified)
tools/                lift, build, sandbox and Proton test scripts; release tools in tools/release/
work/, build/         made by the scripts on your PC (lifted code, the exe); never in git
```
