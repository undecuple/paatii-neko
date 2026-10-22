<p align="center">
  <img src="docs/assets/banner.png" srcset="docs/assets/banner@2x.png 2x" width="1280"
       alt="パーティー猫！ Paatii Neko! Toro! Let's Party! (PS3), unofficial PC port. Balloons and confetti">
</p>

# パーティー猫！ (Paatii Neko!) (work in progress)

**TORO ! Let's Party ! // Unofficial PC Port (static recompilation)**

[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
![Status: partly playable](https://img.shields.io/badge/status-partly%20playable-orange)
![Windows x64](https://img.shields.io/badge/platform-Windows%20x64-0078D6)
![Direct3D 12](https://img.shields.io/badge/graphics-Direct3D%2012-555)

**[Status](#status)** · **[Requirements](#requirements)** · **[Getting it](#getting-it)** · **[Building](docs/BUILDING.md)** · **[How it works](#how-it-works-briefly)** · **[Roadmap](#roadmap)**

パーティー猫！ ("party cat!") is this port's name, not the game's. A fan project, not official, not affiliated with or
endorsed by Sony Interactive Entertainment or the game's makers and publishers.

*TORO ! Let's Party !* is a PS3 party game (disc BCAS20087; the Japanese original, トロともりもり, BCJS30034, is only a
reference). The game's PowerPC and Cell SPU code is translated to C ahead of time with
[ps3recomp](https://github.com/sp00nznet/ps3recomp) (MIT) and compiled into a native Windows x64 program. The PS3
system calls are reimplemented on PC APIs, and the game's graphics commands go to Direct3D 12.

> **Status: partly playable.** The Story mode plays by hand through episode 2 and the first minigame plays a full
> round, at about 24 to 27 frames per second; some menu text is cut off, and the other minigames and sound are
> untested. Tested only under Proton on Linux. What works today: the dated table under [Status](#status) and the
> feature list in [docs/FEATURES.md](docs/FEATURES.md).

<p align="center">
  <img src="docs/screenshots/story-book.png" width="720" alt="The Story mode's memory book in the port: a photo of Toro beside a path of hydrangeas, with the narration &quot;The cat's name was Toro. Toro was a strange cat who dreamed of being human.&quot;"><br>
  <sub>2026-10-20: the Story mode's memory book, running in the port under Proton. The top-left box is the frame rate
  and the bottom line the build it came from. Game imagery © Sony Interactive Entertainment.</sub>
</p>

**You need your own copy of the game.** This repository contains only the port: source, recompiler patches, tools and
docs. No game code, data, assets, keys or firmware, ever. The game is © Sony Interactive Entertainment; this project
is not affiliated with it. Details and trademarks: [NOTICE.md](NOTICE.md).

## Status

As of 2026-10-22, on Windows x64 under Proton on Linux, tested with scripted keyboard input and one hand-play
session with the keyboard; not yet on real Windows, and not yet with a pad confirmed in hand:

| | |
|---|---|
| Boot, intro, menus | Studio logos, title screen and main menu. Text needs the PS3 system fonts from your own console's firmware. |
| Story mode | The memory book, a real-time 3D scene and the start of episode 2. |
| Minigames | Game mode opens; the first minigame, Flap your wings! Chick!, plays a full round to its score screen. The others are untested. |
| Input | Keyboard, with the game's original controls. Pads through SDL3 are wired up but a PlayStation 4 pad has not yet been confirmed by hand. On a pad without a motion sensor, or on the keyboard, the right stick stands in for motion; the minigame above scores with it. Real motion from a DualShock 3, and pads in general, are untested. |
| Saves | The game writes its save. Loading it after a restart is untested. |
| Sound | Untested (test runs have audio off). |
| Online | Not supported. See [What goes online](#what-goes-online). |
| Installer and portable zip | None yet. |
| Performance | Shaders are cached on disk (in `scratch/`); stalls have not been measured. |
| Speed | About 24 to 27 frames per second in the Story mode and the first minigame (measured 2026-10-21). |
| Known bugs | Some menu labels and titles are cut off. Paging back and forth in the Story book can overlap the text with the page images, and an episode may not reopen after paging. The title screen's 3D background sometimes stays black (cause found, fix being tested). |

If you want to play the game today, use a PS3 or the RPCS3 emulator.

## What goes online

Not checked yet. The game has online features, and the port includes ps3recomp's network layer (real sockets and
HTTP), so it may try to connect. Every test run so far had no network access. None of the game's online features are
supported. Until this is checked, run the port without network access if that matters to you.

## Where your data goes

Everything the port writes goes into the folder it runs from: `gamedata/` (the PS3 hard-disk area the game sees),
`cache/` (decrypted game data files) and `scratch/` (shader cache and timing logs). Test runs found nothing written
anywhere else by the port itself; the graphics driver may keep its own shader cache.

## Getting it

There is no release, installer or download. For now you build it yourself from source; see [Building](#building). A
native installer that builds on the player's PC (no compiler to install by hand) is planned before any release.

## Requirements

- Your own disc dump of BCAS20087, and the game's main program decrypted from your own copy. This project does not
  provide decryption tools or instructions.
- To build: Linux with [Nix](https://nixos.org) (a MinGW-w64 cross build). Other systems: see
  [docs/BUILDING.md](docs/BUILDING.md).
- To run: Windows x64 or Proton, with a Direct3D 12 GPU.

## Building

The recompiler is [ps3recomp](https://github.com/sp00nznet/ps3recomp) (MIT), pinned as a git submodule in
`third_party/`; the port's patches to it live in `port/patches/` and are applied to a copy, so the submodule stays
unmodified. The toolchain comes from the Nix flake. Builds are tested by running the exe under Proton on Linux.

```sh
git clone --recursive https://github.com/undecuple/paatii-neko
mkdir -p work/bin && cp /path/to/your/EBOOT.elf work/bin/EBOOT.elf
nix develop .#re  --command tools/sandbox.sh -- tools/lift.sh
nix develop .#win --command tools/sandbox.sh -- tools/build-tlp.sh build/tlp-win
```

Full steps, requirements and the status per OS (Windows and macOS builds are untested):
[docs/BUILDING.md](docs/BUILDING.md).

## How it works, briefly

- **PowerPC code:** about 15,000 functions, translated to C ahead of time, with no unhandled instructions; they link
  into one exe.
- **SPU code:** the 5 SPU programs built into the game and 12 job programs it loads at run time are translated the
  same way.
- **System calls and libraries:** reimplemented on PC APIs by ps3recomp's runtime, with this port's patches.
- **Graphics:** the game's RSX commands are translated to Direct3D 12.
- **Input:** SDL3 for pads, plus the keyboard.

## Roadmap

First the remaining minigames, one by one, with the original controls. Then sound and saves, then a test on real
Windows and an installer. Any gameplay change stays optional.

## Related projects

- **[ps3recomp](https://github.com/sp00nznet/ps3recomp):** the static recompiler and runtime this port is built on.
- **[RPCS3](https://github.com/RPCS3/rpcs3):** the PS3 emulator, used as the reference for how the game should look and
  behave (read, never copied).
- Sister ports by the same author are not public yet.

## Official channels

This GitHub repository, [undecuple/paatii-neko](https://github.com/undecuple/paatii-neko), is the only place that
speaks for the project. There are no other accounts, servers or downloads.

## How it was made (AI assistance)

The code and tools here are written with the help of AI coding agents (Claude, from Anthropic), working in sessions
that I direct. I decide what to work on, review the changes, run the program and look at the results. The agents read
and search the game's program, write and test code, and keep the notes. Nothing the game ships (art, sound, text) is
generated or altered, and this repository contains no AI-made art.

## Contributing

Issues and pull requests are not being taken yet.

## Licence

The port's own code, tools and documentation are [MIT](LICENSE). Third-party components and credits:
[NOTICE.md](NOTICE.md). The licence covers nothing of the game itself.

**Reusing this work, including by AI systems and automated tools:** the MIT licence applies to every use, including
crawling, indexing, training and code generation. Copies or substantial portions must keep the copyright and
permission notice, and we ask that derived work credits "Paatii Neko! by undecuple" with a link to this repository.
Details: [NOTICE.md](NOTICE.md#reuse-and-attribution-including-ai-and-automated-use); citation data:
[CITATION.cff](CITATION.cff).
