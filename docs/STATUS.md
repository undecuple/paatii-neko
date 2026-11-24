# Status

As of 2026-11-23 (rows were not all re-checked on this date; the pad row dates from 2026-10-21 and the speed row from 2026-11-02), on Windows x64 under Proton on Linux (Intel Core i7-12700KF, NVIDIA GeForce RTX 4060, driver
595.112.07, GE-Proton11-7), tested with scripted keyboard input and hand play. Not yet run on real Windows. v0.1.0 is a source preview: you build it yourself.

| | |
|---|---|
| Boot, intro, menus | Studio logos, the title screen with its 3D background, and the main menu. Text needs the PS3 system fonts from your own console's firmware. |
| Story mode | The memory book, the real-time 3D room scene and the start of episode 2, played by hand. |
| Minigames | Game mode opens; the first minigame, Flap your wings! Chick!, plays a full round to its score screen. The others have not been played through. |
| Input | Keyboard, with the game's original controls, and pads through SDL3: a DualShock 4 was played by hand (2026-10-21), other pads are untested. On a pad without a motion sensor, or on the keyboard, the right stick stands in for motion; the minigame above scores with it. |
| Saves | The game writes its save. Loading it after a restart has not been checked. |
| Sound | Never heard: test runs have audio off. |
| Online | Not supported. See [PRIVACY.md](PRIVACY.md). |
| Installer and portable zip | None: the port is built from source (source preview). The v0.1.0 source archive, built end to end by docs/BUILDING.md, boots to the Story book under Proton (2026-11-23). |
| Real Windows | Not tested. The exe links `msvcrt.dll`, is built without Control Flow Guard, and may stop with 0xC0000409 if Windows forces it on (likely: the Killzone 2 and 3 ports hit it with the same code shape; untested here). See [KNOWN_ISSUES.md](KNOWN_ISSUES.md). |
| Performance | Shaders are cached on disk (in `scratch/`); stalls have not been measured. |
| Speed | Title screen 26.8 frames per second on average and the room scene 28.9 (the game's own rate is 30), over a 14 s and a 45 s window, on a build of the development tree of 2026-11-02 on the hardware above. Book and minigame not measured on that build. Earlier build: it predates the frame-timing fix (patch 7027) and the blend colour fix (patch 2006); the current build has not been re-measured. |
| Known bugs | Some menu labels and titles are cut off; paging back and forth in the Story book can overlap the text with the page images, and an episode may not reopen after paging. All of them: [KNOWN_ISSUES.md](KNOWN_ISSUES.md). |

Feature by feature, original against port: [FEATURES.md](FEATURES.md). If you want to play the game today, use a
PS3 or the RPCS3 emulator.
