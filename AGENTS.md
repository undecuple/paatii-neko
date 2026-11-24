# Instructions for AI coding agents

Read this before changing anything in this repository. It applies to every automated contributor (Claude Code, Codex,
Copilot, Cursor and the like) and to the people who run them. Human contributors: the same rules are in
[CONTRIBUTING.md](.github/CONTRIBUTING.md).

## The project

An unofficial PC port of Toro! Let's Party! (PlayStation 3) to Windows x64. It is made by static recompilation with
[ps3recomp](https://github.com/sp00nznet/ps3recomp). The game's PPU and SPU code is lifted to C ahead of time. The
recompiler's runtime replaces the PS3 system libraries, and Direct3D 12 draws the RSX graphics. The repository holds
only the port. Each player builds it from their own copy of the game. More:
[how it works](docs/HOW-IT-WORKS.md), [features](docs/FEATURES.md), [roadmap](docs/ROADMAP.md),
[known issues](docs/KNOWN_ISSUES.md), [release criteria](docs/RELEASE-CRITERIA.md).

## Repository map

| Path | What it holds |
|---|---|
| `port/tlp/` | the program: entry point, host-side overrides, settings and logging |
| `port/patches/` | numbered patches to ps3recomp, applied to a copy by `tools/ps3recomp-patched.sh` |
| `port/ppu_overrides.txt` | functions the port replaces on the host side |
| `third_party/ps3recomp/` | the recompiler, a pinned submodule, never edited in place |
| `tools/` | lift, build, sandbox and run scripts; data tools; `tools/release/` packaging and its host tests |
| `docs/` | public documentation and the data behind generated pages (`features.tsv` for FEATURES.md) |
| `site/` | the project page, generated and checked by `tools/release/website.py` |
| `licenses/` | full licence texts of everything that ships |

## Hard rules

- **No game material, ever.** Never commit, attach, paste, request or link to any of these: files from the disc or
  an update, decrypted binaries, lifted or decompiled game code, extracted assets, saves, keys or firmware.
- Numbers, names, layouts and formulas recovered from the game are fine.
- `Game/`, `work/` and `build/` stay out of git. Do not weaken `.gitignore`.
- **No circumvention.** No decryption or copy-protection tools, keys, step-by-step procedures or links to them.
- The executable comes from the player's own copy. Pointing to [RPCS3](https://github.com/RPCS3/rpcs3) and its
  documentation is allowed.
- **ps3recomp stays pristine.** Never edit the submodule or move its pin as part of a fix (a planned rebase onto a new ps3recomp release is separate). Every change is a new
  numbered patch in `port/patches/`. `tools/ps3recomp-patched.sh` fails on a patch that does not apply.
- **No GPL code.** RPCS3 (GPL-2) may be read for behaviour, never copied, translated or closely paraphrased.
- **Gameplay stays original by default.** Mark additions `ENHANCEMENT:`. Gameplay changes stay opt-in.
- Mark values not yet recovered from the game `ASSUMPTION:`.
- Recompiled code keeps original names where known, and the original address in a comment (`// @0x00123abc`).
- **Nothing goes online by default.** The game's online features are not supported. Do not add a connection. If one
  is ever added, it is opt-in and listed in [docs/PRIVACY.md](docs/PRIVACY.md).

## Licence, attribution and citation

- The port's own code, tools and docs are [MIT](LICENSE). ps3recomp is MIT too.
- Other components keep their own terms. They are listed in [NOTICE.md](NOTICE.md), with full texts in
  [licenses/](licenses/README.md).
- A new dependency, bundled tool or font needs a compatible licence and a row in NOTICE.md in the same change.
- **Credit what you absorb.** Credit work from an upstream pull request, fork or other source in three places: the
  patch header, NOTICE.md and the commit message. Example: "Based on ps3recomp PR #NNN by <author>".
- Never remove existing credits.
- **Cite, do not paraphrase silently.** A fact from an external reference names its source next to it.
- Check such a fact against the game's program before relying on it.
- Citing the project: [CITATION.cff](CITATION.cff). Reuse terms: [NOTICE.md](NOTICE.md).

## Build and test

The toolchain comes from the Nix flake (`flake.nix`); full steps in [docs/BUILDING.md](docs/BUILDING.md).

~~~sh
nix develop .#ci     # what CI runs: lint, patch apply, host tests
nix develop .#re     # analysis and lifting
nix develop .#win    # MinGW-w64 cross build of the Windows exe
nix develop .#run    # Proton test runs (tools/proton-test.sh)
~~~

- **Before every pull request**, run what CI runs (`.github/workflows/ci.yml`). It needs no game data and no GPU:
  - the shell and Python syntax checks;
  - `bash tools/ps3recomp-patched.sh`;
  - the host tests, `tools/release/test_*.py`;
  - `python3 tools/release/recomp_card.py --no-sfo` and `python3 tools/release/website.py --check`.
- **Test the build that ships.** Compare runs only on the same build. The pull request says which build was tested.
- **Host tests are self-contained.** A runtime fix comes with a focused test. It fails without the patch and passes
  with it.
- A test that needs game data prints SKIP, not FAIL. When a patch changes what an old test checks, update that test
  in the same change.
- **Anything that reads the game** runs inside `tools/sandbox.sh`. The game and the repository are read-only there.
  Writes go only to `work/` and `build/`, and there is no network.
- **Windows runs from Linux** go through `tools/proton-test.sh` in `nix develop .#run`, with its own Proton prefix and a hidden display. The
  log and a screenshot land under `work/`. Look at the screenshot before claiming anything about the picture.
- Agents without the game can still work on tools, patches with host tests, docs and packaging. Say in the pull
  request that game runs were not done.

## Docs travel with code

- Update the docs a change affects in the same commit: build steps, requirements, features, credits.
- Two pages are generated. `tools/features.py` writes [docs/FEATURES.md](docs/FEATURES.md) from `docs/features.tsv`.
  `tools/release/website.py` writes the project page.
- Never edit generated output by hand. Change the data with its evidence, run the tool, and commit both.
- A status changes only with evidence.
- Never write that something works unless you ran it, and say how.
- CI checks the generated pages and the project card. The rest is checked in review.
- Environment switches are documented where they are read, with their default.

## Commits and pull requests

- Pull requests are not being taken yet ([CONTRIBUTING.md](.github/CONTRIBUTING.md)); bug reports go through the
  issue forms.
- One topic per commit. Messages are short, plain and descriptive.
- Credits go in the message. No tool-generated footers or advertising lines.
- A pull request says what was run and what was seen. Use [the template](.github/PULL_REQUEST_TEMPLATE.md).
- If an AI tool helped write the change, say so in the pull request in one general line, with no model or vendor name.
- Workflow changes pin actions to commit SHAs and use the least permissions. Justify every write scope in the pull
  request.
- Never add personal paths, user names, tokens or other secrets. CI runs a secret scan.

## Fixes that belong upstream

A patch that is not specific to this game is a candidate for [ps3recomp](https://github.com/sp00nznet/ps3recomp).
Keep it free of game-specific content, and keep its focused test. Follow the maintainer's lead there. The patch stays
in `port/patches/` until upstream takes it.

## Security and rights holders

- Report vulnerabilities privately ([SECURITY.md](.github/SECURITY.md)), never in a public issue.
- Rights holders use the same private channel. Formal notices follow [NOTICE.md](NOTICE.md).
- Do not open issues or pull requests about such reports.
