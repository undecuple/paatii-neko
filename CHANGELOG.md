# Changelog

All notable user-facing changes, newest first, in the style of [Keep a Changelog](https://keepachangelog.com/). Versions
below 1.0.0 are previews. The first one, v0.1.0, is a **source preview**: you build the exe yourself from your own copy of
the game, and no exe, game file or installer is shipped. It has been run only under Proton on Linux, never on real
Windows. See [docs/BUILDING.md](docs/BUILDING.md) and [RELEASE-CRITERIA.md](docs/RELEASE-CRITERIA.md).

## [0.1.0] - 2026-11-24

### Added
- The recompiled game starts under Proton on Linux, opens a Direct3D 12 window and runs from the studio logos to the title screen and the main menu (Story, Game, Gallery, Extras, Options).
- Story mode: the memory book with photos, narration and speech bubbles, a real-time 3D room scene and the start of episode 2.
- Game mode opens, and the first minigame, Flap your wings! Chick!, plays a full round to its score screen.
- The build checks the game's program file first: the Japanese release, another version or a still-encrypted file stops it with a plain message, and an unrecognised copy of the right release only warns.
- Keyboard input with the game's original controls, and pads through SDL3 (a DualShock 4 played by hand; other pads untested). On a pad without a motion sensor, or on the keyboard, the right stick stands in for motion.
- The game writes its save. Loading it after a restart is not checked.
- The PPU code (about 15,000 functions) and 17 SPU programs are translated to C ahead of time and built into one Windows x64 exe from your own copy of the game; see [docs/BUILDING.md](docs/BUILDING.md).
- The port builds on ps3recomp (an MIT-licensed PS3 recompiler and runtime) pinned at submodule commit `0fe7dbf5`, plus 218 patch files in `port/patches/`. Several of this project's fixes are merged upstream (ps3recomp #674, #675 and #676 in v0.19.0, and #783 on 2026-11-21); this pin is older and still carries them as patches.
- A project site, https://undecuple.github.io/paatii-neko/, generated from the same pages as the repository.

### Changed
- Frame timing: the time the game reads for its last display flip now comes from the same clock as its other timers (patch 7027). The gain in speed on this build has not been measured.
- The README leads with what the port is, what you need and its key numbers, each with its proof; the README and the project site no longer show game screenshots.

### Fixed
- A Game mode category label that was too long for its button is now narrowed to fit, as the game asks, instead of being cut off.

- The Direct3D 12 backend wrote the blend colour to the wrong register (0x0368, the shade mode); it now uses 0x037C (patch 2006). Whether this changes anything on screen has not been checked.

### Known gaps
- Sound, the other minigames, Gallery text, Extras, Options, Japanese text, trophies and online features are untested or not implemented; see [docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md) and [docs/FEATURES.md](docs/FEATURES.md).
- No installer or portable zip: the port is built from source. It has been run only under Proton on Linux, not on real Windows. The exe links `msvcrt.dll` and is built without Control Flow Guard; if Windows Exploit Protection forces it on, the exe may stop with error 0xC0000409 (likely: the Killzone 2 and 3 ports hit it with the same code shape; a fix is planned after v0.1.0).
- The v0.1.0 source archive was unpacked and built end to end following [docs/BUILDING.md](docs/BUILDING.md) (2026-11-24); that build boots to the Story book under Proton. The speed figures in [docs/STATUS.md](docs/STATUS.md) are from an earlier build.
