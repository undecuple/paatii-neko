# Requirements

## The game

- **Your own disc of TORO ! Let's Party !**: BCAS20087, version 01.00 (the Asian English release), as a folder that
  holds `PS3_GAME`. Other regions, including the Japanese original BCJS30034, are not what the port is built for.
- **The game's main program, decrypted from your own copy**, as `EBOOT.elf`. This project gives no decryption tools
  or instructions; see the PS3 emulator RPCS3 and its documentation.
- **The PS3 system fonts** (`SCE-PS3-*.TTF`) from your own console's firmware, for the game's text.

Which file goes where: [GETTING-FILES.md](GETTING-FILES.md).

## To build

- Linux with [Nix](https://nixos.org): the flake provides the MinGW-w64 cross toolchain and every other tool.
- 16 GB of RAM or more (the lifted code compiles in 64 chunks of roughly 1 to 2 GB each) and tens of GB of free disk.
  Steps: [BUILDING.md](BUILDING.md).

## To run

- Windows x64 with a Direct3D 12 GPU, or Linux with Proton.
- Tested setup: Intel Core i7-12700KF, NVIDIA GeForce RTX 4060 (driver 595.112.07), GE-Proton11-7. Real Windows has
  not been tried yet. No minimum or recommended hardware is known yet.
