<p align="center">
  <picture>
    <source media="(prefers-reduced-motion: reduce)" srcset="docs/assets/banner.png, docs/assets/banner@2x.png 2x">
    <img src="docs/assets/banner.svg" width="1280"
         alt="パーティー猫！ Paatii Neko! Toro! Let's Party! (PS3), unofficial PC port. Balloons and confetti">
  </picture>
</p>

<h1 align="center">パーティー猫！ (Paatii Neko!)</h1>

<p align="center"><b>TORO ! Let's Party ! (PS3), rebuilt as a native PC program from the game's own code, with no CPU emulator.</b><br>
An unofficial fan port. Version v0.1.0 is a source preview.</p>

<p align="center">
  <a href="https://github.com/undecuple/paatii-neko/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/undecuple/paatii-neko/ci.yml?label=CI&style=flat-square&labelColor=6B4423"></a>
  <a href="https://github.com/undecuple/paatii-neko/releases"><img alt="Release" src="https://img.shields.io/github/v/release/undecuple/paatii-neko?include_prereleases&label=release&style=flat-square&labelColor=6B4423&color=1F5F9E"></a>
  <a href="LICENSE"><img alt="Licence: MIT" src="https://img.shields.io/github/license/undecuple/paatii-neko?style=flat-square&labelColor=6B4423&color=B35400"></a>
</p>

<p align="center">
  <a href="https://github.com/undecuple/paatii-neko/commits/main"><img alt="Last commit" src="https://img.shields.io/github/last-commit/undecuple/paatii-neko?style=flat-square&labelColor=6B4423&color=4D6600"></a>
  <a href="https://github.com/undecuple/paatii-neko/issues"><img alt="Open issues" src="https://img.shields.io/github/issues/undecuple/paatii-neko?style=flat-square&labelColor=6B4423&color=4D6600"></a>
  <a href="https://github.com/undecuple/paatii-neko/stargazers"><img alt="Stars" src="https://img.shields.io/github/stars/undecuple/paatii-neko?style=flat-square&labelColor=6B4423&color=4D6600"></a>
</p>

<p align="center">
  <a href="#status"><img alt="Status: partly playable" src="https://img.shields.io/badge/status-partly%20playable-A84F00?style=flat-square&labelColor=6B4423"></a>
  <a href="#compatibility"><img alt="Platform: Windows x64, Proton-tested" src="https://img.shields.io/badge/platform-Windows%20x64%20%C2%B7%20Proton--tested-B3305F?style=flat-square&labelColor=6B4423"></a>
  <a href="#how-it-works"><img alt="Renderer: Direct3D 12" src="https://img.shields.io/badge/renderer-Direct3D%2012-1F5F9E?style=flat-square&labelColor=6B4423"></a>
</p>

<p align="center">
  <b><a href="#download-and-play">Download and play</a></b> ·
  <b><a href="#status">Status</a></b> ·
  <b><a href="#if-setup-fails">If setup fails</a></b> ·
  <b><a href="#known-issues">Known issues</a></b> ·
  <b><a href="#reporting-bugs-and-troubleshooting">Reporting bugs</a></b> ·
  <b><a href="docs/BUILDING.md">Build from source</a></b> ·
  <b><a href="https://undecuple.github.io/paatii-neko/">Project site</a></b>
</p>

> **Bring your own game.** This repository holds no game code, assets, keys or firmware. You need your own disc
> (BCAS20087, version 01.00); the port is built on your PC from it. A few screenshots of the port are listed in
> [docs/SCREENSHOTS.md](docs/SCREENSHOTS.md). [What you need](docs/GETTING-FILES.md)

> **Tested only under Proton on Linux; not tested on real Windows.** The exe links `msvcrt.dll` and is built without
> Control Flow Guard (CFG; a static check of a 2026-11-09 build). If Windows Exploit Protection forces CFG on, the exe
> may stop at start with a fast-fail crash (error 0xC0000409), because the SPU runtime uses frameless
> `_setjmp`/`longjmp`; the Killzone 2 and 3 ports hit this with the same code shape, so it is likely. If it happens, try (untested advice) turning off forced CFG for `tlp.exe` in Windows Security,
> App & browser control, Exploit protection, and tell us (see [Reporting bugs](#reporting-bugs-and-troubleshooting)).

<p align="center"><img src="docs/assets/divider.svg" alt="" width="640"></p>

**At a glance** (from [docs/STATUS.md](docs/STATUS.md), as of 2026-11-23; the rows carry their own dates):

| Works | Partly | Not yet |
|---|---|---|
| Studio logos, title screen, main menu | Input: keyboard and a DualShock 4 (hand play 2026-10-21); other pads untested | Sound: never heard, test runs have audio off |
| Story book and the room scene, played by hand into episode 2 (2026-10-21) | Speed: 28.9 frames/s in the room scene, target 30 (build of 2026-11-02) | The other minigames: not played through |
| First minigame, a full round to its score screen | Saves: written, loading after a restart unchecked | Real Windows: not tested |
| | Story book paging and some menu labels: known glitches | Online, installer, attract movie: not available |

**28.9** frames/s in the room scene (the game targets 30; build of 2026-11-02, under Proton) · **8** of 24 game
features working, **9** partly ([list](docs/FEATURES.md)) · fixes merged into ps3recomp, recently #674-#676 and #783
([#674](https://github.com/sp00nznet/ps3recomp/pull/674), [#675](https://github.com/sp00nznet/ps3recomp/pull/675),
[#676](https://github.com/sp00nznet/ps3recomp/pull/676), [#783](https://github.com/sp00nznet/ps3recomp/pull/783))

<p align="center"><img src="docs/assets/divider.svg" alt="" width="640"></p>

## What makes it different

| | Proof |
|---|---|
| The game's own code, translated ahead of time to x64: no CPU emulator runs while you play | [How it works](docs/HOW-IT-WORKS.md) |
| No game code, assets, keys or firmware are in this repository; the port is built from your copy | [Getting the files](docs/GETTING-FILES.md) |
| Everything the port itself writes stays in its own folder (the graphics driver may keep its own shader cache), and it has no online feature of its own (whether the game itself connects is not checked yet) | [Privacy](docs/PRIVACY.md) |
| General fixes go back to ps3recomp, the recompiler this port is built on | [#674](https://github.com/sp00nznet/ps3recomp/pull/674), [#675](https://github.com/sp00nznet/ps3recomp/pull/675), [#676](https://github.com/sp00nznet/ps3recomp/pull/676) (merged 2026-11-06, in ps3recomp v0.19.0), [#783](https://github.com/sp00nznet/ps3recomp/pull/783) (frame timing, merged 2026-11-21) |
| Open source under MIT | [LICENSE](LICENSE) |

<p align="center"><img src="docs/assets/divider.svg" alt="" width="640"></p>

## Status

**Status: partly playable.** A source preview, version 0.1.0. The Story mode plays by hand into episode 2 at
28.9 frames/s in its room scene (target 30), and the first minigame plays a full round; the other minigames and sound
are unchecked. These figures are from a build of 2026-11-02, before later changes; they have not been measured again
for v0.1.0. Details: [docs/STATUS.md](docs/STATUS.md); what a release must meet to be called playable:
[docs/RELEASE-CRITERIA.md](docs/RELEASE-CRITERIA.md). How it works: [docs/HOW-IT-WORKS.md](docs/HOW-IT-WORKS.md).

| Platform | Today | Caveat |
|---|---|---|
| Linux, with Proton | build from the source archive: [Download and play](#download-and-play) | tested on one PC so far |
| Windows 10/11 | build on Linux, run the exe | not run on Windows yet; see the CFG note above |
| Linux, native (Vulkan) | coming soon | planned |

<p align="center"><img src="docs/assets/divider.svg" alt="" width="640"></p>

## Download and play

v0.1.0 is a **source preview** (a GitHub pre-release). It ships no exe, installer or game file; the exe is built on
your PC from your own copy of the game, so it cannot be built for you. The release has one source archive, which
includes the pinned `third_party/ps3recomp` submodule (GitHub's automatic zip does not), and a `SHA256SUMS` file.
No fresh build from that archive has been run end to end yet, so the results below are what the steps are meant to
give, as described in [docs/BUILDING.md](docs/BUILDING.md).

**You need**
- **Your TORO ! Let's Party ! disc** (BCAS20087, version 01.00), as a folder (the one that holds `PS3_GAME`).
- **The game's program file** (`EBOOT.elf`) from your own copy.
- **The PS3 system fonts** from your own console's firmware, for the game's text.
- Linux with Nix and 16 GB of RAM or more, plus tens of GB of free disk, to build; Proton (GE-Proton11-7 was tested) to
  run. Details: [docs/requirements.md](docs/requirements.md).

What each must contain and where it goes: [docs/GETTING-FILES.md](docs/GETTING-FILES.md). This project ships none
of the game files.

**Steps**
1. Download the source archive and `SHA256SUMS` from the release, check the archive with `sha256sum -c SHA256SUMS`,
   and unpack it. Result: a folder with `docs/`, `port/`, `tools/` and `third_party/ps3recomp/` filled in.
2. Put your `EBOOT.elf` at `work/bin/EBOOT.elf` and your game folder where the docs say
   ([docs/GETTING-FILES.md](docs/GETTING-FILES.md)). Result: nothing yet; the next step checks the file.
3. Lift the game's code: `nix develop .#re --command tools/sandbox.sh -- tools/lift.sh`. Result: it first checks the
   EBOOT is the right release, then writes C code to `work/recomp/`. A wrong release or a still-encrypted file stops
   it with a plain message.
4. Lift the SPU code: `nix develop .#re --command tools/sandbox.sh -- python3 tools/elf_info.py work/bin/EBOOT.elf
   --spu-dir work/spu --job-dir work/spu-miss`, then `nix develop .#re --command tools/sandbox.sh --
   tools/spu/lift_spu.sh`. Result: the game's 17 SPU programs, read from your EBOOT, as C in `work/spu/lift/`.
   Without them the game stops at a black screen.
5. Build the exe: `nix develop .#win --command tools/sandbox.sh -- tools/build-tlp.sh build/tlp-win`. Result:
   `build/tlp-win/tlp.exe`. It needs `SDL3.dll` next to it ([docs/BUILDING.md](docs/BUILDING.md) shows how).
6. Run it under Proton with `tools/proton-test.sh` (commands in [docs/BUILDING.md](docs/BUILDING.md#running)). Result
   on the tested PC: the game's title screen, then the Story book. Real Windows is untested.

Windows may warn about an unsigned program you built yourself, and antivirus software may flag it; nothing here is
signed. Everything the port writes stays in the folder it runs from; the game's network use is not checked yet
([docs/PRIVACY.md](docs/PRIVACY.md)). Changes: [CHANGELOG.md](CHANGELOG.md).

<p align="center"><img src="docs/assets/divider.svg" alt="" width="640"></p>

## If setup fails

| Symptom | Likely cause and what to do |
|---|---|
| The lift stops with a message about the release or version | The file is the Japanese release, another version or a still-encrypted file. The port is for BCAS20087, version 01.00 ([docs/GETTING-FILES.md](docs/GETTING-FILES.md#self-check)). |
| The build or clone has no `third_party/ps3recomp` files | You used GitHub's automatic zip. Use the release's source archive, or clone with `--recursive`. |
| The compile runs out of memory | The lifted code needs 16 GB of RAM or more ([docs/requirements.md](docs/requirements.md)). |
| The exe does not start on Windows, error 0xC0000409 | Likely forced CFG (see the note at the top); a fix is planned after v0.1.0. |
| The game's text is missing | The PS3 system fonts may not be in place; see [docs/GETTING-FILES.md](docs/GETTING-FILES.md). |
| Anything else | See [Reporting bugs and troubleshooting](#reporting-bugs-and-troubleshooting). |

<p align="center"><img src="docs/assets/divider.svg" alt="" width="640"></p>

## Online and your data

Nothing the port writes leaves its own folder (the graphics driver may keep its own shader cache). The port has no
online feature of its own. Whether the game itself connects was not checked; run it without network access if that
matters to you. Details: [docs/PRIVACY.md](docs/PRIVACY.md).

<p align="center"><img src="docs/assets/divider.svg" alt="" width="640"></p>

## Compatibility

| Platform | How it runs | Renderer | State | Tested on |
|---|---|---|---|---|
| Windows 10/11 | native exe | Direct3D 12 | implemented: the exe is built for Windows, but has not been run on Windows yet | - |
| Linux | the Windows exe under Proton (GE-Proton11-7) | Direct3D 12 through vkd3d-proton | verified: all of the testing so far, scripted and by hand | Intel Core i7-12700KF, NVIDIA GeForce RTX 4060 (driver 595.112.07), GE-Proton11-7 |
| Linux, native | native build | Vulkan | planned | - |

"Verified" means a run on that setup; "implemented" means the code is in but not run there; "planned" means neither.
Speed figures (26.8 frames/s on the title screen and 28.9 in the room scene, on a build of 2026-11-02, under Proton)
are in [docs/STATUS.md](docs/STATUS.md). Feature by feature: [docs/FEATURES.md](docs/FEATURES.md).

<p align="center"><img src="docs/assets/divider.svg" alt="" width="640"></p>

## Settings and controllers

The port has no settings screen yet; its switches are environment variables, described in
[docs/BUILDING.md](docs/BUILDING.md). Pads go through SDL3: a DualShock 4 was played by hand (2026-10-21), other pads
are untested. The keyboard plays as the pad, and on a pad without a motion sensor the right stick stands in for
motion. [docs/FEATURES.md](docs/FEATURES.md) has the rest.

<p align="center"><img src="docs/assets/divider.svg" alt="" width="640"></p>

## Known issues

- Some menu labels and titles are cut off.
- Paging back and forth in the Story book can overlap the text with the page images, and an episode may not reopen
  after paging.
- Only the first minigame has been played; sound has not been checked.
- Possible fast-fail crash on real Windows if Exploit Protection forces CFG on (see the note at the top; unverified).

All of them: [docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md).

<p align="center"><img src="docs/assets/divider.svg" alt="" width="640"></p>

## Reporting bugs and troubleshooting

Use the [issue forms](.github/ISSUE_TEMPLATE) (bug report, performance report). Check
[docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md) first, attach the newest log file (the program's output; under `tools/proton-test.sh` it is `work/proton/NAME/app/app_stdout.txt`), and leave game files, keys and links
to pirated copies out of issues and logs. Some oddities are in the original game too; those are labelled
`original-bug`.

<p align="center"><img src="docs/assets/divider.svg" alt="" width="640"></p>

## Building

Short version (full steps in [docs/BUILDING.md](docs/BUILDING.md)):

```sh
git clone --recursive https://github.com/undecuple/paatii-neko
mkdir -p work/bin && cp /path/to/your/EBOOT.elf work/bin/EBOOT.elf
nix develop .#re  --command tools/sandbox.sh -- tools/lift.sh
nix develop .#re  --command tools/sandbox.sh -- python3 tools/elf_info.py work/bin/EBOOT.elf --spu-dir work/spu --job-dir work/spu-miss
nix develop .#re  --command tools/sandbox.sh -- tools/spu/lift_spu.sh
nix develop .#win --command tools/sandbox.sh -- tools/build-tlp.sh build/tlp-win
```

Full steps: [docs/BUILDING.md](docs/BUILDING.md) (repository layout:
[docs/BUILDING.md](docs/BUILDING.md#repository-layout)). The recompiler, ps3recomp (MIT), is a pinned submodule in
`third_party/`, pinned at commit `0fe7dbf` (older than ps3recomp v0.19.0, which holds #674 to #676 upstream; this
repository still carries them as patches). The port's patches live in `port/patches/` and are applied to a copy.

<p align="center"><img src="docs/assets/divider.svg" alt="" width="640"></p>

## How it works

The game's PPU and SPU code is translated to C ahead of time by ps3recomp, and the runtime replaces the PS3 system
libraries; Direct3D 12 draws the RSX graphics. [docs/HOW-IT-WORKS.md](docs/HOW-IT-WORKS.md).

<p align="center"><img src="docs/assets/divider.svg" alt="" width="640"></p>

## Roadmap

A real Windows test, the Vulkan build on Linux and more minigames are next: [docs/ROADMAP.md](docs/ROADMAP.md).

<p align="center"><img src="docs/assets/divider.svg" alt="" width="640"></p>

## Contributing

Bug reports are welcome through the issue forms. Pull requests are not being taken yet:
[.github/CONTRIBUTING.md](.github/CONTRIBUTING.md). Security problems: [SECURITY.md](.github/SECURITY.md). Copying or
forking the project: [docs/FORKING.md](docs/FORKING.md). General fixes found here are offered to ps3recomp upstream.
Instructions for AI coding agents: [AGENTS.md](AGENTS.md).

<p align="center"><img src="docs/assets/divider.svg" alt="" width="640"></p>

## How AI was used

This project is developed by one person with AI coding agents, with the maintainer setting the goals, reviewing and
signing off their work. The agents read the reference material, write and test patches, tools and documentation, and
run builds and tests; the game's files are handled only in a sandbox with no network access. Status claims are dated
and say how they were checked. No game art, sound or text is generated or altered. Full description:
[docs/AI.md](docs/AI.md).

<p align="center"><img src="docs/assets/divider.svg" alt="" width="640"></p>

## Licence and disclaimer

The port's own code, tools and documentation: [MIT](LICENSE). Third-party components and credits:
[NOTICE.md](NOTICE.md); full licence texts: [licenses/](licenses/README.md). The licence covers nothing of the game
itself.

**Reusing this work, including by AI systems and automated tools:** the MIT licence applies to every use,
including crawling, indexing, training and code generation. Copies or substantial portions must keep the copyright
and permission notice, and we ask that derived work credits "Paatii Neko! by undecuple" with a link to this
repository. Details: [NOTICE.md](NOTICE.md#reuse-and-attribution-including-ai-and-automated-use); citation data:
[CITATION.cff](CITATION.cff).

パーティー猫！ ("party cat!") is this port's name, not the game's. It is a fan project, not official and not
affiliated with or endorsed by Sony Interactive Entertainment or the game's makers and publishers.

**You need your own copy of the game.** This repository contains only the port: source code, patches to the
recompiler, tools and documentation. It contains no game code, data, assets, keys or firmware, and it never will; the
screenshots in `docs/screenshots/` show the port running and are credited to Sony Interactive Entertainment.
*TORO ! Let's Party !* is © Sony Interactive Entertainment.

<p align="center"><img src="docs/assets/divider.svg" alt="" width="640"></p>

## Related projects, credits and official channels

**[Project Helghast](https://github.com/undecuple/project-helghast)** (Killzone 3) and
**[Project Pyrrhus](https://github.com/undecuple/project-pyrrhus)** (Killzone 2): PS3 games ported to PC the same way,
by the same author. Their READMEs have their current state. Built on **[ps3recomp](https://github.com/sp00nznet/ps3recomp)**;
**[RPCS3](https://github.com/RPCS3/rpcs3)** is the reference for how the game should look and behave (read, never
copied).

**Official channels:** パーティー猫！ is made by **undecuple**: GitHub [@undecuple](https://github.com/undecuple), Reddit
[u/RelationshipNo4440](https://www.reddit.com/user/RelationshipNo4440), Discord **itekso.** (on the ps3recomp server).
Builds and fixes come only from this repository; we never ask anyone to paste a command into PowerShell or a
terminal, or to run a file from someone else. Anyone else offering builds, "fixes" or donations in this project's
name is not us.
