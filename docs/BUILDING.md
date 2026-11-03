# Building the port

The port's executable is generated from **your own copy** of the game. The game's code is lifted to C from your
decrypted executable and compiled on your machine. Nothing of the game is in this repository, and nothing is
downloaded.

There is no installer or release yet. The only way to get a build today is a developer build from source with Nix,
described below.

## What is tested

| Where | Status |
|---|---|
| Linux with Nix (developed on NixOS): lift, MinGW-w64 cross-build to a Windows x64 exe, run under Proton | **Tested** in the development tree; this is the only path that has been run. A fresh clone of this repository has not yet been built end to end. |
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
Direct3D 12 (on Linux, through Proton). Only an NVIDIA GPU has been tried.

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

# 4. Compile the exe (configures build/tlp-win on the first run)
nix develop .#win --command tools/sandbox.sh -- tools/build-tlp.sh build/tlp-win
```

`tools/lift.sh` runs step 2 itself, so step 2 on its own is only a check that the patches apply.

The result is `build/tlp-win/tlp.exe`, a Windows x64 program. It needs `SDL3.dll` next to it:

```sh
nix develop .#win --command python3 tools/release/stage_sdl3.py --out work/stage/tlp
cp build/tlp-win/tlp.exe work/stage/tlp/
```

After a change to a file in `port/patches/` or to `port/ppu_overrides.txt`, rerun steps 2 to 4. The build refuses
a patched tree or a lift that no longer matches them.

### Lifting the SPU code

The game's SPU programs are lifted separately, with `tools/spu/lift_spu.sh`. `tools/build-tlp.sh` picks up the
result (in `work/spu/lift`) when it exists. The script reads the 5 SPU programs built into the executable from
`work/spu/`, and the job programs the game loads from its data files from `work/spu-miss/` (collected by running the
game once with `SPU_DUMP_MISS=work/spu-miss` set).

```sh
nix develop .#re --command tools/sandbox.sh -- python3 tools/elf_info.py work/bin/EBOOT.elf --spu-dir work/spu
nix develop .#re --command tools/sandbox.sh -- tools/spu/lift_spu.sh
```

Without this step the build still links (`TLP_SPU=0` skips it on purpose), but the game's SPU work is then not
available. The repository's scripts do not yet automate collecting the job programs, so this part has the most rough
edges.

## Running

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
  follow [Steps](#steps) 1 to 4 with `nix develop .#re` and `nix develop .#win` as written. On macOS
  `tools/sandbox.sh` runs the command directly, with no sandbox (bubblewrap is Linux-only), and says so.
- **Running:** `tlp.exe` is a Windows program, and Proton does not run on macOS. The likely route is to copy the exe
  and the game folder to a Windows PC. Windows compatibility layers for macOS have not been tried.

## Building on Windows

**Status: not tested.** Neither a build on Windows nor running the exe on real Windows has been done. The exe has
only been run under Proton on Linux.

- **Likely route:** Nix does not run on Windows itself, so build inside WSL2 (Linux on Windows) with Nix
  installed, and follow [Steps](#steps) 1 to 4. Keep the repository inside the Linux file system, not on the
  Windows drive, and give WSL2 enough memory (see [What you need](#what-you-need)). The sandbox script has not been
  tried inside WSL2.
- **Running:** copy `tlp.exe` and `SDL3.dll` into a folder, and run
  `tlp.exe path\to\PS3_GAME\USRDIR\EBOOT.elf` in a terminal. Untested.
- A native Windows build without WSL2 is not set up. The build scripts are written for Linux shells.

## Other Linux distributions

Install Nix with flakes enabled and follow [Steps](#steps). Not tested outside NixOS. The Proton runner points
Vulkan at an NVIDIA file in a NixOS location (`/run/opengl-driver/share/vulkan/icd.d/nvidia_icd.json`); adjust
`VK_ICD_FILENAMES` in `tools/proton-inner.sh` for your distribution.

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
