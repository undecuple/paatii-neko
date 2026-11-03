# Getting your files ready

The port is built on your PC from your own copy of the game: the disc BCAS20087, version 01.00, the Asian English
release "TORO ! Let's Party !". This page says which files the port needs and where it looks for them. It does not
say how to make the files. For that, see the PS3 emulator [RPCS3](https://rpcs3.net) and its documentation. Nothing
here is shipped or downloaded by this project.

## What you need

| Item | What it is | Where the port expects it |
|---|---|---|
| The disc's files, as a folder | The folder that holds `PS3_GAME`, with the disc's files in it as they are laid out on the disc (`PS3_GAME/PARAM.SFO`, `PS3_GAME/USRDIR/...`) | The game folder you give when you run the exe (see below) |
| The game's main program, decrypted to a plain ELF | A file named `EBOOT.elf`, made from your own copy of the game. A plain ELF starts with the letters `ELF`; an encrypted file does not | For the build: `work/bin/EBOOT.elf` in the repository. For a run: `<game folder>/PS3_GAME/USRDIR/EBOOT.elf` |
| The PS3 system fonts (for text) | The TrueType files `SCE-PS3-*.TTF` from your own console's firmware | A folder named by the `KZ3_FONT_DIR` environment variable. Text needs them |

The decrypted EBOOT is used twice: the build reads it from `work/bin/EBOOT.elf` and translates its code to C, and the
exe reads the same file when you run it. The rest of the disc's files are only needed to run the game, not to build.

## Where things go

```
paatii-neko/                       your clone of this repository
  work/bin/EBOOT.elf               your decrypted main program, for the build (stays out of git)
game-folder/                       any folder you like
  PS3_GAME/
    PARAM.SFO
    USRDIR/
      EBOOT.elf                    the same decrypted file, for the run
      ...                          the disc's other files as they are on the disc
```

The exe takes the path of `EBOOT.elf` as its one argument and finds the game folder by going up three levels from
it, so the layout must be `<game folder>/PS3_GAME/USRDIR/EBOOT.elf`. Set `PS3_VFS_ROOT` to use a different game
folder. Full steps: [BUILDING.md](BUILDING.md).

## Self-check

- The disc's `PS3_GAME/PARAM.SFO` says title id `BCAS20087` and version `01.00`. `tools/disc_info.py` reads it, and
  `tools/elf_info.py` lists what is in `EBOOT.elf`; both are in this repository.
- `EBOOT.elf` is a 64-bit PowerPC ELF file, about 11.8 MB.
- The disc is about 1.04 GiB.

Other regions of the game, such as the Japanese original (BCJS30034), are not what the port is built for.

## Where your data goes

The port writes only into the folder it runs from: `gamedata/` (the PS3 hard-disk area the game sees), `cache/`
(decrypted game data files) and `scratch/` (shader cache and timing logs).
Do not commit any of these files or the disc's files to a repository.
