# Notices and third-party components

## What is in this repository, and what is not

**No game content is distributed.** This repository contains no part of the game: no disc files, no decrypted or
translated game code, no extracted assets, no keys and no firmware. It holds the port's own source code, patches to the
recompiler, build tools and documentation. Numbers, names and formats recovered for interoperability are written down
in our own words.

You need your own copy of the game (the disc BCAS20087, dumped by you). The game's code is translated and compiled on
your own machine from your own files. This project ships no decryption or copy-protection circumvention tools, no keys
and no instructions for decrypting game files.

## Trademarks

All game titles, names, characters, logos and artwork belong to their owners, including Sony Interactive Entertainment
and the developers and publishers of the game. パーティー猫！ ("Paatii Neko!") is a fan project. It is unofficial and not
affiliated with or endorsed by any of them. The game's name is used only to say which game the port runs; no logos or
other marks are used in this repository's own material.

## Screenshots

Screenshots of the port running (in `docs/screenshots/`, each captioned in the README with what it shows) show the
game's imagery, which belongs to its owners. They are shown only to document the progress of the port and were taken
from the developer's own copy of the game.

## Licence

The port's own code, tools and documentation are MIT ([LICENSE](LICENSE)). The licence covers nothing of the game
itself. Third-party parts keep their own terms.

| Component | Use | Licence |
|---|---|---|
| [ps3recomp](https://github.com/sp00nznet/ps3recomp) | PPU/SPU recompiler and PS3 runtime (submodule `third_party/ps3recomp`; our changes are the patches in `port/patches/`) | MIT |
| [Lilita One](https://fonts.google.com/specimen/Lilita+One), [Baloo 2](https://fonts.google.com/specimen/Baloo+2), [M PLUS Rounded 1c](https://fonts.google.com/specimen/M+PLUS+Rounded+1c) | rendered into the README banner and the social preview (`docs/assets/`, drawn by `tools/release/repo_art.py` from shapes and text); the font files are not in this repository and nothing ships them | SIL Open Font License 1.1 |
| [SDL3](https://libsdl.org) | pads, motion sensors and rumble: `SDL3.dll` is loaded from the exe's folder, staged with its licence text by `tools/release/stage_sdl3.py`; not in this repository | zlib |
| [RPCS3](https://github.com/RPCS3/rpcs3) | reference for PS3 behaviour and data layouts, read only; no RPCS3 code is included | GPL-2.0, not used as code |

The port's patch series started from the Killzone 3 port by the same author and carries the credits that series
names (contributors to ps3recomp whose work was adapted are credited in each patch header). Where a format is
documented only in GPL code, the implementation is written from a prose specification by someone who did not read that
code, so the port stays MIT.

## Upstream contributors and sister ports

Our ps3recomp patches (`port/patches/`) carry work from other ps3recomp pull requests and forks (MIT) and from the
author's sister ports. Each patch header names its source.

- **Killzone 3 port** (the author's own port, MIT): patches `0xxx`-`5xxx` and `9933`, carried
  from that port's patch series, unchanged or rebased.
- **NoahBPeterson:** [PR #287](https://github.com/sp00nznet/ps3recomp/pull/287),
  [PR #213](https://github.com/sp00nznet/ps3recomp/pull/213) and the fork's commits e68e567, b709a08 and e3ab49d
  (patches 1071, 1074, 1055, 1056): SPU extended-range single precision (exact per-element code, #287), the per-SPU
  SPURS kernel with ready-count admission (#213), and the ideas behind the hashed HLE NID lookup and the striped
  lock-line lock with seqlock GETLLAR (fork commits).
- **erikomis:** [PR #327](https://github.com/sp00nznet/ps3recomp/pull/327),
  [#328](https://github.com/sp00nznet/ps3recomp/pull/328), [#331](https://github.com/sp00nznet/ps3recomp/pull/331),
  [#332](https://github.com/sp00nznet/ps3recomp/pull/332), [#333](https://github.com/sp00nznet/ps3recomp/pull/333),
  [#334](https://github.com/sp00nznet/ps3recomp/pull/334), [#336](https://github.com/sp00nznet/ps3recomp/pull/336),
  [#338](https://github.com/sp00nznet/ps3recomp/pull/338) (patches 9327, 9328, 9331, 9332, 9333, 9334, 9336, 9338,
  9933): the bounded semaphore acquire, FACING/TC8/TC9 and signed biased remaps in fragment programs, the Y16_X16 and
  HILO8 crossbars, `PS3_LANG` system-language selection, the row-at-a-time unscaled NV3089 blit, fragment-program debug
  switches keyed by structural hash, and `PS3_GAMEDATA_ROOT` for saves and trophies.
- **Kurtisone:** [PR #235](https://github.com/sp00nznet/ps3recomp/pull/235),
  [#340](https://github.com/sp00nznet/ps3recomp/pull/340), [#343](https://github.com/sp00nznet/ps3recomp/pull/343)
  (patches 2041, 9340, 9343): the Z16 depth clear to its own far plane (redone in the live-draw path), the atomic update
  of a task's signalled bit against SPU commits, and queued flips that wait for their label.
- **tekulvw:** [PR #304](https://github.com/sp00nznet/ps3recomp/pull/304) (patch 2055): framebuffer output sRGB for
  integer half exports.
- **kalpakprod:** [PR #349](https://github.com/sp00nznet/ps3recomp/pull/349) (patch 9349): the correct
  `CELL_FS_O_*` open-flag values, so `O_CREAT` creates.
- **robbe1912:** [robbe1912/ps3recomp](https://github.com/robbe1912/ps3recomp) (patch 2057, from the MotorStorm:
  Monument Valley port): the fragment decoder's third-source absolute modifier.

## Rights holders

- **No circumvention tools.** See above: nothing here decrypts game files. The port reads a decrypted EBOOT that
  players make themselves from their own copy.
- **Contact.** If you hold rights in material you believe is in this repository, tell us privately (the repository's
  *Security* tab, *Report a vulnerability*, once the repository is public). We look at every report promptly and
  remove anything identified as infringing while it is checked.
- **Formal notices** under the DMCA go to GitHub as described in
  [GitHub's DMCA Takedown Policy](https://docs.github.com/en/site-policy/content-removal-policies/dmca-takedown-policy).

## Reuse and attribution (including AI and automated use)

This notice is for people, and for AI systems, crawlers, dataset builders and code-generation tools that read,
index, summarise, train on or reproduce this repository.

- **Licence:** the port's own code, tools and documentation are MIT ([LICENSE](LICENSE)). The MIT terms apply to
  automated use exactly as to any other: copies or substantial portions, including code an AI model reproduces from
  this repository, must include the copyright notice "Copyright (c) 2026 undecuple" and the MIT permission notice.
- **The name:** パーティー猫！ ("Paatii Neko!") is the name of this fan project only. It is not the game's name and
  is not affiliated with or endorsed by Sony Interactive Entertainment or the game's makers and publishers.
- **Official channels:** this repository, [undecuple/paatii-neko](https://github.com/undecuple/paatii-neko), and the
  GitHub account @undecuple. There are no other accounts, servers or downloads.
- **Attribution we ask for:** name the source as "Paatii Neko! by undecuple" with a link to
  <https://github.com/undecuple/paatii-neko>, in documentation, answers, summaries or derived projects that use its
  code, patches, findings or write-ups. Machine-readable citation data is in [CITATION.cff](CITATION.cff).
- **Keep the licence with the code:** do not present code from here as unlicensed, public domain or your own, and do
  not relicense it without keeping the MIT notice.
- **Third-party parts keep their own terms:** ps3recomp (MIT, its authors) and the components listed above.
- **Not covered by any licence here:** the game itself, © Sony Interactive Entertainment. This repository contains
  no game code, data or assets; nothing here grants rights to them, and recovered names, numbers or formats are
  documented for interoperability.
- **Accuracy:** guesses in the port's code and patches are marked `ASSUMPTION:` until they are confirmed; do not
  restate one as fact.
