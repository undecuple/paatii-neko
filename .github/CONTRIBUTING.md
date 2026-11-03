# Contributing

Bug reports are welcome through the issue forms. Pull requests are not being taken yet; the ground rules below say
what will apply once they are.

## Ground rules

- **No game material, ever:** no files from a disc or update, no decrypted or translated game code, no extracted
  assets, saves, keys or firmware, and no links to where they can be downloaded. Numbers, names, structure layouts
  and formulas worked out from the game are fine.
- **No GPL code:** RPCS3 is a reference to read, not code to copy. Write behaviour from your own understanding.
- **Recompiler fixes go upstream:** a fix that is not specific to this game belongs in
  [ps3recomp](https://github.com/sp00nznet/ps3recomp). Here it lives as a patch in `port/patches/` until upstream
  takes it.

## Reporting a problem

Say which build you ran (commit), your GPU and driver, Windows or Proton (and which Proton), and attach the run's
log. Remove your user name and folder paths from the log first. Do not attach save files, memory dumps or anything
else that contains game data. Security problems: see [SECURITY.md](SECURITY.md), not an issue.
