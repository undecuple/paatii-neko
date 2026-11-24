# How AI was used

The port is developed by one person with AI coding agents, working in sessions the maintainer directs. This page says
what is translated, what is reimplemented, what is native and how AI was used.

## What is translated, reimplemented and native

- **Translated:** the game's own PPU and SPU code is translated to C ahead of time by the recompiler ps3recomp, from
  your own copy of the game, and compiled on your machine. This is the original logic, not rewritten source, and it is
  not in this repository. The game's graphics commands are translated at run time and replayed on Direct3D 12.
- **Reimplemented:** the PS3's system calls and libraries (threads, locks, files, SPURS job scheduling, audio, pads,
  fonts and so on) are reimplemented on PC APIs by the ps3recomp runtime and by this port's patches to it.
- **Native:** the host program (`port/tlp/`), the keyboard and pad input through SDL3, the build and test scripts and
  the documentation are ordinary new code written for this project.

## How AI was used

The agents do most of the hands-on work: reading the game's program and the reference material, writing and testing
patches, tools and documentation, and running the builds and test runs. The maintainer sets the goals and priorities,
plays the builds, reviews and signs off everything that is published, and is responsible for it.

- The game and its files are only handled inside a sandbox, with the game files read-only and no network access.
- Status claims are dated and say how they were checked. Guesses are marked `ASSUMPTION:` in the code until they are
  confirmed in the game's program.
- The PS3 emulator RPCS3 is read as a reference, never copied.
- Nothing the game ships (art, sound, text) is generated or altered, and this repository contains no AI-made art.
- AI makes mistakes. A statement here, in the docs or in a commit may be wrong; a run that was not made is not claimed.

If you find a statement here that was not verified, please open an issue.
