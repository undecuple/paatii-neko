# Roadmap

In order of priority. No dates: each step is done when it is checked in a run.

1. **Windows:** a test on real Windows, including with Exploit Protection forcing Control Flow Guard on (see
   [KNOWN_ISSUES.md](KNOWN_ISSUES.md)). Until then the port is only known to run under Proton on Linux.
2. **Minigames:** the remaining minigames, one by one, with the game's original controls, each played to its score
   screen.
3. **Sound and saves:** music and effects checked by ear; a save loaded again after a restart.
4. **Speed:** the game's own 30 frames per second in every mode, measured with the hardware and build named.
5. **Easier building:** fewer manual steps, in particular for the SPU programs that today need one game run first
   (see [BUILDING.md](BUILDING.md)), and later an installer that builds the port on the player's PC.
6. **Later:** a native Linux build (Vulkan), and optional display features such as an upscaler.

Any gameplay change stays optional. What a release must meet: [RELEASE-CRITERIA.md](RELEASE-CRITERIA.md).

## Wanted, not started

- Export of models and scenes to common formats, and later import back into the game, as a base for modding
  frameworks. Exports stay on the player's machine; extracted assets are never committed. Import is not designed yet.
- Fuller keyboard and mouse support. The keyboard already plays as the pad ([FEATURES.md](FEATURES.md)); to add:
  rebindable keys, mouse movement as a stand-in for the motion sensor and stick, and the mouse in menus where the
  game's own cursor allows. Prompts follow the last input device, drawn in the game's style.
- VR support (opt-in display mode; feasibility unassessed, the game renders one fixed camera per minigame).
- Wide and ultrawide displays (21:9, 32:9). Today the game's 16:9 frame is shown as-is; options: pillarbox by
  default, then a wider projection where a minigame's scene and HUD hold up (an enhancement, opt-in per minigame).
