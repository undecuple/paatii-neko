# Status

As of 2026-11-03, on Windows x64 under Proton on Linux (Intel Core i7-12700KF, NVIDIA GeForce RTX 4060, driver
595.112.07, GE-Proton11-7), tested with scripted keyboard input and hand play. Not yet run on real Windows.

| | |
|---|---|
| Boot, intro, menus | Studio logos, the title screen with its 3D background, and the main menu. Text needs the PS3 system fonts from your own console's firmware. |
| Story mode | The memory book, the real-time 3D room scene and the start of episode 2, played by hand. |
| Minigames | Game mode opens; the first minigame, Flap your wings! Chick!, plays a full round to its score screen. The others have not been played yet. |
| Input | Keyboard, with the game's original controls, and pads through SDL3: a DualShock 4 was played by hand (2026-10-21), other pads are untested. On a pad without a motion sensor, or on the keyboard, the right stick stands in for motion; the minigame above scores with it. |
| Saves | The game writes its save. Loading it after a restart has not been checked. |
| Sound | Not checked (test runs have audio off). |
| Online | Not supported. See [PRIVACY.md](PRIVACY.md). |
| Installer and portable zip | None yet: the port is built from source. |
| Performance | Shaders are cached on disk (in `scratch/`); stalls have not been measured. |
| Speed | Title screen 26.8 frames per second on average and the room scene 28.9 (the game's own rate is 30), over a 14 s and a 45 s window, on a build of the development tree of 2026-11-02 on the hardware above. Book and minigame not measured on that build. |
| Known bugs | Some menu labels and titles are cut off; paging back and forth in the Story book can overlap the text with the page images, and an episode may not reopen after paging. All of them: [KNOWN_ISSUES.md](KNOWN_ISSUES.md). |

Feature by feature, original against port: [FEATURES.md](FEATURES.md). If you want to play the game today, use a
PS3 or the RPCS3 emulator.
