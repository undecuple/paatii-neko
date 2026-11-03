# What goes online and where your data goes

## What goes online

Not checked yet. The game has online features, and the port includes ps3recomp's network layer (real sockets and
HTTP), so it may try to connect. Every test run so far had no network access. None of the game's online features are
supported, and the port has no update check, crash reporting or other online feature of its own. Until this is
checked, run the port without network access if that matters to you.

## Where your data goes

Everything the port writes goes into the folder it runs from:

- `gamedata/`: the PS3 hard-disk area the game sees, saves included.
- `cache/`: decrypted game data files, made from your own disc as they are read.
- `scratch/`: the shader cache and timing logs.

Test runs found nothing written anywhere else by the port itself; the graphics driver may keep its own shader cache.
To remove the port, delete that folder.
