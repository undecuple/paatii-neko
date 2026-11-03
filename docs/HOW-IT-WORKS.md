# How the port works

*TORO ! Let's Party !* runs on the PS3's Cell processor: one PowerPC core (the PPU) runs the game, SPU co-processors
run jobs, and the RSX GPU draws. The port translates the game's PPU and SPU code to C ahead of time, compiles it into
a Windows x64 program, and links it against a runtime that answers the PS3 system calls and libraries on the PC.
No CPU emulator runs at play time. The GPU side is still reproduced by the runtime (see Graphics below).

## What kind of port is this?

This is a static recompilation with a runtime layer. By part, today:

| Part | How it runs today |
|---|---|
| PPU game code | translated ahead of time to C, then compiled for x64 |
| SPU programs and jobs | translated ahead of time the same way; the runtime reproduces the SPURS job scheduling and DMA |
| Graphics | translated at run time: the game's RSX command stream is replayed on Direct3D 12 |
| System libraries | reimplemented on PC APIs by the runtime |
| Input | SDL3 for pads, plus the keyboard |

It is not a decompilation. The game's logic is the translated original, not rewritten source, and this repository
holds none of it: everything is built on your PC from your own copy of the game.

## The pieces

- **[ps3recomp](https://github.com/sp00nznet/ps3recomp)** (MIT) is the recompiler and the runtime. It is pinned as a
  git submodule in `third_party/ps3recomp`, and the submodule itself stays unmodified.
- **`port/patches/`** holds this port's changes to ps3recomp as numbered patch files. `tools/ps3recomp-patched.sh`
  makes a fresh copy of the pinned ps3recomp in `work/ps3recomp-patched` and applies every patch in order. It only
  rewrites files whose content changed, so a build recompiles only what a patch really changed. Both the lift and
  the build use that copy.
- **`port/tlp/`** is the port's own glue: the program's `main`, the replacements for system functions the game needs,
  and the settings the port turns on by default.
- **`port/ppu_overrides.txt`** lists PPU functions that the host replaces; it is empty today.
- **`tools/`** has the lift, build, sandbox and Proton test scripts, and the two inspection tools for your own files
  (`tools/disc_info.py`, `tools/elf_info.py`).

## Pipeline

1. **Inputs.** Your own copy of the game and its decrypted main program. See [GETTING-FILES.md](GETTING-FILES.md).
2. **PPU lift.** `tools/lift.sh` runs ps3recomp's loader, function finder and lifter on the decrypted EBOOT. About
   15,000 functions become C functions that work on a modelled register file and the guest's big-endian memory. The
   output is cut into 64 source files by address.
3. **SPU lift.** The 5 SPU programs built into the game and 12 job programs that it loads from its data files are
   translated the same way by `tools/spu/lift_spu.sh`.
4. **Build.** `tools/build-tlp.sh` compiles the lifted C, the port's glue and the patched runtime into one Windows
   x64 exe with a MinGW-w64 cross toolchain from the Nix flake.
5. **Run.** The exe reads the game's data from your disc folder at run time. Compressed and encrypted game data files
   are decoded as they are read and cached next to the exe.

## Runtime

The runtime reimplements the PS3's system calls and libraries (threads, locks, files, SPURS, audio, pads and so on)
on PC APIs. It keeps the PS3's memory layout, so the translated code finds its data where it expects it. The game's
scheduler for its SPU jobs is reproduced there too, so the translated SPU code runs on host threads.

## Graphics

The game draws through the RSX GPU with a stream of commands. The runtime walks that stream and replays it on a
Direct3D 12 backend: shaders are translated from RSX microcode and cached on disk. Direct3D 12 is also what Proton
translates on Linux.

## Where the port stands

[FEATURES.md](FEATURES.md) lists what works today and [KNOWN_ISSUES.md](KNOWN_ISSUES.md) what does not. The port has
been run only under Proton on Linux.
