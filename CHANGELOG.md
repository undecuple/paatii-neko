# Changelog

All notable user-facing changes, newest first, in the style of [Keep a Changelog](https://keepachangelog.com/). The
project has no release yet and is partly playable: see [RELEASE-CRITERIA.md](docs/RELEASE-CRITERIA.md).

## [Unreleased]

### Added
- The recompiled game starts under Proton on Linux, opens a Direct3D 12 window and runs from the studio logos to the title screen and the main menu (Story, Game, Gallery, Extras, Options).
- Story mode: the memory book with photos, narration and speech bubbles, a real-time 3D room scene and the start of episode 2.
- Game mode opens, and the first minigame, Flap your wings! Chick!, plays a full round to its score screen.
- Keyboard input with the game's original controls, and pads through SDL3 (a DualShock 4 played by hand; other pads untested). On a pad without a motion sensor, or on the keyboard, the right stick stands in for motion.
- The game writes its save. Loading it after a restart is not checked.
- The PPU code (about 15,000 functions) and 17 SPU programs are translated to C ahead of time and built into one Windows x64 exe from your own copy of the game; see [docs/BUILDING.md](docs/BUILDING.md).
- A project site, https://undecuple.github.io/paatii-neko/, generated from the same pages as the repository.

### Changed
- The README leads with what the port is, what you need and its key numbers, each with its proof; the README and the project site no longer show game screenshots.

### Fixed
- A Game mode category label that was too long for its button is now narrowed to fit, as the game asks, instead of being cut off.

### Known gaps
- Sound, the other minigames, Gallery text, Extras, Options, Japanese text, trophies and online features are untested or not implemented; see [docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md) and [docs/FEATURES.md](docs/FEATURES.md).
- No installer or portable zip yet; the port is built from source. It has been run only under Proton on Linux, not on real Windows.
