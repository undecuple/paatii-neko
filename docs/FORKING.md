# Copying or forking this project

For anyone who copies, forks or reuses this repository. The code is MIT-licensed, so you may. This page lists what to
change so your copy does not claim to be this project, and what to keep. Paths are relative to the repository root.
To build your copy, follow [BUILDING.md](BUILDING.md).

## 1. Names and branding

| What | Where | Change it to your own |
|---|---|---|
| Project name "Paatii Neko!" (パーティー猫！), tag line and the repository slug | `README.md`, `NOTICE.md`, `CITATION.cff`, `.recomp.json`, `docs/*.md` | yes |
| Banner and social preview | `docs/assets/` | yes |
| Screenshots | `docs/screenshots/` | yes, with your own (see [SCREENSHOTS.md](SCREENSHOTS.md)) |

パーティー猫！ is this port's name, not the game's. Keep the disclaimer in `NOTICE.md` that your project is a fan
project, not affiliated with or endorsed by the game's publisher or developer.

## 2. Identity and remotes

| What | Where |
|---|---|
| Author and maintainer (name, link) | `CITATION.cff`, `.recomp.json`, `.github/CODEOWNERS`, `NOTICE.md`, `LICENSE` (copyright line) |
| Repository URL | `README.md`, `CITATION.cff`, `.recomp.json`, `NOTICE.md`, `docs/*.md`, `.github/ISSUE_TEMPLATE/config.yml`, `.github/CONTRIBUTING.md` |
| Funding link | `.github/FUNDING.yml` (delete or replace) |
| Security contact | `.github/SECURITY.md` |

Set your own git identity (`git config user.name`, `git config user.email`) before committing. After editing, search
the tree for the old owner name and repository slug; a plain `git grep` finds every leftover.

## 3. Versions and releases

- Tags are `vMAJOR.MINOR.PATCH`. While the major version is 0, mark every release as a pre-release on GitHub.
- Never move or reuse a tag; fix forward with a new patch version.
- Keep a changelog in [CHANGELOG.md](../CHANGELOG.md) with an `## [Unreleased]` section. `tools/release/release.py`
  turns it into a release section, checks the version string and the project card, and `tools/release/release_notes.py`
  drafts the release notes from it. `tools/release/recomp_card.py` checks `.recomp.json` against the README status and
  [RELEASE-CRITERIA.md](RELEASE-CRITERIA.md).
- Publish a checksum file next to every release file.

## 4. CI and GitHub settings

| What | Notes |
|---|---|
| `.github/workflows/ci.yml` | shell and Python scripts parse, every patch applies to the pinned ps3recomp, a host test that needs no game data |
| `.github/workflows/secrets.yml` | secret scan |
| `.github/dependabot.yml` | dependency update pull requests |
| Issue forms | `.github/ISSUE_TEMPLATE/` |

CI cannot build the exe: the lifted code comes from the player's own copy of the game and is never committed.
Check these settings in your repository: Actions should require approval for workflows from outside collaborators,
and the default token should be read-only. Add a ruleset on the default branch (pull request required, no force
push, no deleting).

## 5. What the user supplies

Your users supply their own copy of the game. No game files are shipped here. The decrypted main program used for the
lift comes from the player's own copy; for that, see [RPCS3](https://rpcs3.net) and its documentation.
[GETTING-FILES.md](GETTING-FILES.md) says which files the port expects. Keep it that way in a fork: do not commit disc
files, a decrypted EBOOT, extracted assets, keys or a built game exe.

## 6. Licences and credits to keep

- `LICENSE` (MIT): keep the notice with any copied code; add your own line, do not remove the existing one.
- `NOTICE.md`: the credit lines for ps3recomp (MIT) and other referenced work, and the trademark statement. Extend it
  when you add a dependency.
- ps3recomp is a git submodule (`third_party/ps3recomp`, pinned in `.gitmodules` and by commit); the patches in
  `port/patches/` apply to that pin. Keep its licence and credit its author.
- If you change what goes online, change the "What goes online" section of `README.md` too.

## 7. Baked-in paths and environment variables

Scripts that assume a layout you may need to adapt:

| Script | What it assumes |
|---|---|
| `tools/sandbox.sh` | the bubblewrap layout (repository read-only, writes only under `work/` and `build/`); without bubblewrap it runs the command directly |
| `tools/lift.sh`, `tools/build-tlp.sh` | `work/` and `build/` under the repository |
| `tools/proton-test.sh`, `tools/proton-inner.sh` | a Proton install and a prefix on the machine that runs them; `tools/proton-inner.sh` points Vulkan at an NVIDIA file in a NixOS location |

The port reads some settings from environment variables, for example `PS3_VFS_ROOT` (the game folder); they are
described in [BUILDING.md](BUILDING.md) or in the source where they are read.
