# Release criteria

Criteria met: no

パーティー猫！ (Paatii Neko!) has no release and no release date. Versions below 1.0.0 are previews: **v0.x =
preview**, published as GitHub pre-releases, each saying what is missing. **v1.0.0 = every minigame and the Story mode
playable start to finish at about the game's own 30 frames per second.** The first release that calls itself
**playable** waits for every point of the second list. Booting to a title screen does not count. This list, not a
date, is what a release is measured against.

The line `Criteria met:` above says `yes` only when every point of the v1.0.0 list holds. Until then the project card
(`.recomp.json`) may not call the project released or complete.

## Gates for a v0.x tag (preview)

1. **CI green** on the commit that is tagged.
2. **A build that a player can start:** the release names which way of getting the port it offers. Today there is no
   installer and no portable zip; see [BUILDING.md](BUILDING.md).
3. **Tested on real Windows** before a release says it runs there. Today the port has only been run under Proton on
   Linux.
4. **Known issues listed** in [KNOWN_ISSUES.md](KNOWN_ISSUES.md).
5. **Checksums published** beside every release file.
6. **One version string** everywhere it appears (checked by `tools/release/release.py`).
7. **Tags are never moved**; a fix is a new tag.
8. **Published as a pre-release** while the version is 0.x.
9. **A changelog entry** for the version in [CHANGELOG.md](../CHANGELOG.md).

## Release criteria for v1.0.0 (playable)

1. **Played by a person:** the Story mode through every episode and every minigame, by hand, on one save, with a
   dated playthrough log (what was played, time, build, bugs met) published beside the release.
2. **A picture first:** the game's frames are drawn correctly in every mode and compared with the PS3 emulator RPCS3
   on the same scene.
3. **Automated coverage:** a scripted run that loads and plays every minigame and Story episode on the release build,
   with saves written and read back, and the boot check.
4. **Speed:** about 30 frames per second in every mode on the recommended hardware, with steady frame pacing (the
   slowest 1 % of frames measured next to the average). Numbers go in the release notes with the hardware and the
   build they were measured on.
5. **No known crash or soft-lock** on any path through the game; everything else in the published known-issues list.
6. **Sound and saves work:** music and effects play, and a save loads again after a restart.
7. **Accurate label:** the README and release notes say what is translated, what is reimplemented and what is native,
   and how AI was used.
8. **Getting the game files explained:** the player brings the files of their own copy of the game and the decrypted
   main program made from it; [GETTING-FILES.md](GETTING-FILES.md) says which files and where. This project gives no
   decryption procedure or keys, and does not link to or name where to get game files.
9. **Maintenance shown, not promised:** a changelog, GitHub releases, and issue forms that ask for GPU, driver and the
   newest log file.
10. **Tested on real Windows** as well as under Proton.

The numbers here are targets for 1.0.0, not a statement about today: see [FEATURES.md](FEATURES.md) for what works
now and [KNOWN_ISSUES.md](KNOWN_ISSUES.md) for what is wrong.
