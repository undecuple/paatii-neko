# Licence texts

Full licence texts of the third-party parts this repository builds with, renders or ships subsets of, copied unchanged. The short
credits list is [NOTICE.md](../NOTICE.md). Nothing here covers the game itself, which is never in this repository.

This repository ships source only. A build made from it (`tlp.exe`) links the toolchain's runtime pieces below
statically and loads `SDL3.dll` from its own folder, so anyone who passes a build on should pass these texts with it.

- [`../LICENSE`](../LICENSE): MIT, the port's own code, tools and documentation (everything outside `third_party/`).
- [`ps3recomp-LICENSE.txt`](ps3recomp-LICENSE.txt): MIT, ps3recomp, the recompiler and runtime (submodule
  `third_party/ps3recomp`, built into the exe).
- [`SDL3-LICENSE.txt`](SDL3-LICENSE.txt): zlib, SDL3 3.4.16 (`SDL3.dll`, unmodified: pads, rumble, motion sensors).
- [`gcc/COPYING.RUNTIME.txt`](gcc/COPYING.RUNTIME.txt) and [`gcc/COPYING3.txt`](gcc/COPYING3.txt): GPL-3.0 with the GCC
  Runtime Library Exception 3.1, libgcc and libstdc++ of GCC 16.2.0 (linked statically). The exception lets a program
  compiled with GCC be passed on under its own terms.
- [`mingw-w64/COPYING.txt`](mingw-w64/COPYING.txt), [`DISCLAIMER.txt`](mingw-w64/DISCLAIMER.txt),
  [`DISCLAIMER.PD.txt`](mingw-w64/DISCLAIMER.PD.txt): MinGW-w64 14.0.0 headers and C runtime (ZPL-2.1 and public-domain
  parts).
- [`mcfgthread/LICENSE.md`](mcfgthread/LICENSE.md), [`gcc-exception-3.1.txt`](mcfgthread/gcc-exception-3.1.txt),
  [`lgpl-3.0.txt`](mcfgthread/lgpl-3.0.txt): MCF Gthread 2.4.2, the compiler's thread library (linked statically),
  LGPL-3.0 or later with the GCC Runtime Library Exception 3.1. The GPL-3.0 text it refers to is
  [`gcc/COPYING3.txt`](gcc/COPYING3.txt).
- [`fonts-lilitaone-OFL.txt`](fonts-lilitaone-OFL.txt), [`fonts-baloo2-OFL.txt`](fonts-baloo2-OFL.txt),
  [`fonts-caveat-OFL.txt`](fonts-caveat-OFL.txt), [`fonts-mplusrounded1c-OFL.txt`](fonts-mplusrounded1c-OFL.txt): SIL
  Open Font License 1.1, Lilita One, Baloo 2, Caveat and M PLUS Rounded 1c. They are rendered into the banner images in
  `docs/assets/`, and the project site ships subsets of them as woff2 files in `site/fonts/` (the subsets are
  derived files; the full font files are not in this repository).

Versions are the ones the build environment in `flake.nix` pins.
