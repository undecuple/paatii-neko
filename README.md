<p align="center">
  <img src="docs/assets/banner.png" srcset="docs/assets/banner@2x.png 2x" width="1280"
       alt="パーティー猫！ Paatii Neko! Toro! Let's Party! (PS3), unofficial PC port. Balloons and confetti">
</p>

# パーティー猫！ (Paatii Neko!) (work in progress)

A native Windows x64 port of the PS3 party game *TORO ! Let's Party !*, made by static recompilation on
[ps3recomp](https://github.com/sp00nznet/ps3recomp). You need your own copy of the game: the disc BCAS20087, version
01.00.

> **Status: partly playable.** No release yet (2026-11-03). The Story mode plays by hand into episode 2 and the
> first minigame plays a full round. It runs only as a build from source, tested only under Proton on Linux.

**[Getting started](#getting-started)** · **[Compatibility](#compatibility)** · **[Building](docs/BUILDING.md)** ·
**[Known issues](docs/KNOWN_ISSUES.md)** · **[Reporting bugs](#reporting-bugs)**

<p align="center">
  <img src="docs/screenshots/story-book.png" width="720" alt="The Story mode's memory book in the port: a photo of Toro beside a path of hydrangeas, with the narration &quot;The cat's name was Toro. Toro was a strange cat who dreamed of being human.&quot;"><br>
  <sub>Work in progress, 2026-10-20: the Story mode's memory book in the port under Proton. The top-left box is the
  frame rate and the bottom line the commit of the development tree it was built from. Game imagery © Sony Interactive Entertainment.</sub>
</p>

パーティー猫！ ("party cat!") is this port's name, not the game's. A fan project, not official, not affiliated with or
endorsed by Sony Interactive Entertainment or the game's makers and publishers.

**This repository contains only the port:** source, recompiler patches, tools and docs. No game code, data, assets,
keys or firmware, ever. Details and trademarks: [NOTICE.md](NOTICE.md).

## Compatibility

| Platform | How it runs | Renderer | State | Tested on |
|---|---|---|---|---|
| Windows 10/11 | native exe | Direct3D 12 | implemented, not run on Windows yet | - |
| Linux | the Windows exe under Proton (GE-Proton11-7) | Direct3D 12 through vkd3d-proton | verified | Intel Core i7-12700KF, NVIDIA GeForce RTX 4060 (driver 595.112.07), a build of the development tree of 2026-11-02 (commit 017ba1b there, not in this repository's history) |
| Linux, native | - | Vulkan | planned | - |

"Verified" means runs on that setup with the named build; "implemented" means the code is there but has not been run
on that setup.

## Status

As of 2026-11-03, on the Proton row above, tested with scripted keyboard input and hand play:

| | |
|---|---|
| Boot, intro, menus | Studio logos, the title screen with its 3D background, and the main menu. Text needs the PS3 system fonts from your own console's firmware. |
| Story mode | The memory book, the real-time 3D room scene and the start of episode 2. |
| Minigames | Game mode opens; the first minigame, Flap your wings! Chick!, plays a full round to its score screen. The others have not been played yet. |
| Input | Keyboard, with the game's original controls, and pads through SDL3: a DualShock 4 was played by hand (2026-10-21), other pads are untested. On a pad without a motion sensor, or on the keyboard, the right stick stands in for motion; the minigame above scores with it. |
| Saves | The game writes its save. Loading it after a restart has not been checked. |
| Sound | Not checked (test runs have audio off). |
| Online | Not supported. See [What goes online](#what-goes-online). |
| Speed | Title screen 26.8 frames per second on average and the room scene 28.9 (the game's own rate is 30), over a 14 s and a 45 s window, the 2026-11-02 build on the hardware in the Proton row. Book and minigame not measured on that build. |

The full feature list is [docs/FEATURES.md](docs/FEATURES.md); what is wrong today is
[docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md). If you want to play the game today, use a PS3 or the RPCS3 emulator.

## Getting started

There is no release, installer or download. You build the port yourself from source:

- **Your files:** your own disc BCAS20087 and its main program decrypted from your own copy.
  [docs/GETTING-FILES.md](docs/GETTING-FILES.md) says which files and where they go. This project gives no decryption
  tools or instructions.
- **To build:** Linux with [Nix](https://nixos.org) (a MinGW-w64 cross build); see [Building](#building).
- **To run:** Windows x64 or Proton, with a Direct3D 12 GPU.

An installer that builds the port on the player's PC is planned before any release.

### Where your data goes

Everything the port writes goes into the folder it runs from: `gamedata/` (the PS3 hard-disk area the game sees,
saves included), `cache/` (decrypted game data files) and `scratch/` (shader cache and timing logs). Test runs found
nothing written anywhere else by the port itself; the graphics driver may keep its own shader cache. To remove the
port, delete that folder.

### What goes online

Not checked yet. The game has online features, and the port includes ps3recomp's network layer (real sockets and
HTTP), so it may try to connect. Every test run so far had no network access. None of the game's online features are
supported. Until this is checked, run the port without network access if that matters to you.

## Settings and known issues

The port has no settings screen yet; its switches are environment variables, described in
[docs/BUILDING.md](docs/BUILDING.md). The list of known problems, each with where it shows, is
[docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md).

## Building

The recompiler is [ps3recomp](https://github.com/sp00nznet/ps3recomp) (MIT), pinned as a git submodule in
`third_party/`; the port's patches to it live in `port/patches/` and are applied to a copy, so the submodule stays
unmodified. The toolchain comes from the Nix flake.

```sh
git clone --recursive https://github.com/undecuple/paatii-neko
mkdir -p work/bin && cp /path/to/your/EBOOT.elf work/bin/EBOOT.elf
nix develop .#re  --command tools/sandbox.sh -- tools/lift.sh
nix develop .#win --command tools/sandbox.sh -- tools/build-tlp.sh build/tlp-win
```

Full steps, requirements and the state per OS: [docs/BUILDING.md](docs/BUILDING.md). How the pieces fit:
[docs/HOW-IT-WORKS.md](docs/HOW-IT-WORKS.md).

<details>
<summary>How it works, briefly</summary>

- **PowerPC code:** about 15,000 functions, translated to C ahead of time, with no unhandled instructions; they link
  into one exe.
- **SPU code:** the 5 SPU programs built into the game and 12 job programs it loads at run time are translated the
  same way.
- **System calls and libraries:** reimplemented on PC APIs by ps3recomp's runtime, with this port's patches.
- **Graphics:** the game's RSX commands are translated to Direct3D 12.
- **Input:** SDL3 for pads, plus the keyboard.

</details>

## Roadmap

First the remaining minigames, one by one, with the original controls. Then sound and saves, then a test on real
Windows and an installer. Any gameplay change stays optional. What a release must meet:
[docs/RELEASE-CRITERIA.md](docs/RELEASE-CRITERIA.md); changes so far: [CHANGELOG.md](CHANGELOG.md).

## Reporting bugs

Use the issue forms: [bug report](.github/ISSUE_TEMPLATE/bug_report.yml) or
[performance](.github/ISSUE_TEMPLATE/performance.yml). Please check [docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md)
first and attach the newest log file. Some oddities are in the original game too; those are labelled `original-bug`.
We never ask you to run a command or a file from someone else.

## How it was made (AI assistance)

The code and tools here are written with the help of AI coding agents, working in sessions that I direct. I decide
what to work on, review the changes, run the program and look at the results. The agents read and search the game's
program, write and test code, and keep the notes. Nothing the game ships (art, sound, text) is generated or altered,
and this repository contains no AI-made art.

## Contributing

Pull requests are not being taken yet; see [.github/CONTRIBUTING.md](.github/CONTRIBUTING.md).

## Credits, licence and related projects

- **Built on [ps3recomp](https://github.com/sp00nznet/ps3recomp)**, the static recompiler and runtime.
- **[RPCS3](https://github.com/RPCS3/rpcs3):** the PS3 emulator, used as the reference for how the game should look and
  behave (read, never copied).
- **Licence:** the port's own code, tools and documentation are [MIT](LICENSE). Third-party components and credits:
  [NOTICE.md](NOTICE.md); full licence texts: [licenses/](licenses/README.md). The licence covers nothing of the game
  itself.

**Reusing this work, including by AI systems and automated tools:** the MIT licence applies to every use, including
crawling, indexing, training and code generation. Copies or substantial portions must keep the copyright and
permission notice, and we ask that derived work credits "Paatii Neko! by undecuple" with a link to this repository.
Details: [NOTICE.md](NOTICE.md#reuse-and-attribution-including-ai-and-automated-use); citation data:
[CITATION.cff](CITATION.cff).
