#!/usr/bin/env python3
"""Host test for tools/release/website.py on a small fixture (temp root, no game data, no network): the page is
generated with every section of the plan in order, the Japanese title above the English one, no banner and no
Discussions link; --check passes on a fresh page and fails on a stale page, a missing screenshot, social preview,
style.css, font file, requirements section, status paragraph, a stylesheet token that differs from the table and a
stylesheet that loads from outside; Markdown in the data is escaped and relative links become GitHub URLs; the lint
refuses scripts, event handlers and every outside resource (Google Fonts included); the contrast table reaches 4.5
and a bad pair is caught; the real repo's page is fresh and NOTICE.md carries the font and style credits.
After the Killzone 2 port's test_website.py (same author, MIT). Exit 0 = PASS.

    python3 tools/release/test_website.py
"""
import contextlib
import io
import os
import pathlib
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import website  # noqa: E402

HEAD = "kind\tarea\tfeature\tps3\tstatus\tevidence\n"
README = """# Title

**Status: partly playable.** No release yet: the port is built from source. See [docs/STATUS.md](docs/STATUS.md).

## Getting started

There is no release, installer or download yet. Build it yourself.

What each must contain and where it goes: [docs/GETTING-FILES.md](docs/GETTING-FILES.md). This project ships none.

## Credits

**Official channels:** パーティー猫！ is made by **undecuple**. Anyone else is not us.

This project is developed by one person with AI coding agents: [docs/AI.md](docs/AI.md).

パーティー猫！ ("party cat!") is this port's name, not the game's. It is a fan project.

**You need your own copy of the game.** Nothing of it is here. *TORO ! Let's Party !* is © Sony Interactive Entertainment.
"""
STATUS = """# Status

As of 2026-11-03, tested under Proton.

| | |
|---|---|
| Boot | Logos and the **menu**. See [KNOWN_ISSUES.md](KNOWN_ISSUES.md). |
| Sound | Not checked <script>x</script> yet. |

Feature by feature: [FEATURES.md](FEATURES.md).
"""
REQ = """# Requirements

## The game

- **Your own disc**: BCAS20087, as a folder
  that holds `PS3_GAME`.
- **Fonts**: see [GETTING-FILES.md](GETTING-FILES.md).

## To build

- Linux with [Nix](https://nixos.org).

## To run

- Windows x64.
"""
PRIVACY = """# What goes online and where your data goes

## What goes online

Not checked yet.

## Where your data goes

Everything the port writes goes into the folder it runs from:

- `gamedata/`: saves.
"""
HOW = """# How the port works

*TORO ! Let's Party !* runs on the PS3's Cell processor.

## What kind of port is this?

| Part | How it runs today |
|---|---|
| PPU game code | translated ahead of time |
| Input | SDL3 |
"""
ROAD = """# Roadmap

In order of priority.

1. **Minigames:** the rest.
2. **Sound and saves:** by ear.
"""
SHOTS_MD = "# Screenshots\n\n| Image | What it shows |\n|---|---|\n" + "".join(
    f"| [{n}](screenshots/{n}) | Caption of {n}. |\n" for n, _t in website.SHOTS)


def tokens_css(**over):
    t = dict(website.TOKENS)
    t.update(over)
    return ":root{" + "".join(f"--{k}:{v};" for k, v in t.items()) + "}\n"


def fixture(root, req=REQ, readme=README, shots=True, social=True, css=tokens_css(), fonts=True,
            evidence="Ran in `a`"):
    rows = [("ps3", "Menus", "Title", "A **title**", "works", evidence),
            ("ps3", "Menus", "Movie", "-", "not yet", "none"),
            ("ps3", "Play", "Round", "-", "partial", "once"),
            ("port", "Port only", "Stick as motion", "On pads", "not yet verified", "x")]
    (root / "docs/assets").mkdir(parents=True)
    (root / "docs/screenshots").mkdir()
    (root / "site/fonts").mkdir(parents=True)
    (root / "docs/features.tsv").write_text(HEAD + "".join("\t".join(r) + "\n" for r in rows), encoding="utf-8")
    for name, text in (("STATUS", STATUS), ("SCREENSHOTS", SHOTS_MD), ("PRIVACY", PRIVACY), ("HOW-IT-WORKS", HOW),
                       ("ROADMAP", ROAD)):
        (root / f"docs/{name}.md").write_text(text, encoding="utf-8")
    if req is not None:
        (root / "docs/requirements.md").write_text(req, encoding="utf-8")
    if readme is not None:
        (root / "README.md").write_text(readme, encoding="utf-8")
    if css is not None:
        (root / "site/style.css").write_text(css, encoding="utf-8")
    if social:
        (root / website.SOCIAL).write_bytes(b"png")
    if fonts:
        for f in website.FONT_FILES:
            (root / website.FONT_DIR / f).write_bytes(b"wOF2" + b"x" * 100)
    if shots:
        for n, _t in website.SHOTS:
            (root / "docs/screenshots" / n).write_bytes(b"png")


def run(*args):
    err = io.StringIO()
    with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
        rc = website.main(list(args))
    return rc, err.getvalue()


def main():
    fails = []

    def expect(cond, what):
        if not cond:
            fails.append(what)

    with tempfile.TemporaryDirectory() as t:
        root = pathlib.Path(t) / "ok"
        fixture(root)
        r = str(root)
        expect(run("--root", r, "--check")[0] == 1, "check passes with no page")
        expect(run("--root", r)[0] == 0, "generate fails")
        rc, err = run("--root", r, "--check")
        expect(rc == 0, f"check fails on a fresh page: {err}")
        page = (root / website.PAGE).read_text()
        expect("<script>" not in page and "&lt;script&gt;" in page, "data text not escaped")
        expect(f'href="{website.REPO}/blob/main/docs/KNOWN_ISSUES.md"' in page, "STATUS link not made from docs/")
        expect("<strong>menu</strong>" in page and "<code>gamedata/</code>" in page, "inline Markdown not rendered")
        expect("Partly playable" in page and "No release yet" in page, "status stamp missing")
        ids = [page.find(f'id="{s}"') for s in website.SECTION_IDS]
        expect(all(i >= 0 for i in ids) and ids == sorted(ids), f"sections missing or out of order: {ids}")
        expect(page.find("パーティー猫！") < page.find("<h1>Paatii Neko!</h1>"), "Japanese title not above the English one")
        expect("banner" not in page, "page mentions the banner")
        expect(page.count("<figure") == len(website.SHOTS) and "Caption of story-book.png." in page, "screens or captions wrong")
        expect("Game imagery © Sony Interactive Entertainment" in page, "image credit missing")
        expect("adapted from <a href=\"" + website.HELGHAST + "\">Project Helghast</a> by undecuple, MIT" in page,
               "style credit missing")
        expect("that holds <code>PS3_GAME</code>" in page and "Linux with <a href=\"https://nixos.org\">Nix</a>" in page,
               "requirements (continuation lines, links) wrong")
        expect("<ol>" in page and "<strong>Input</strong>: SDL3" in page and "Not checked yet." in page, "docs sections missing")
        expect(f'href="{website.HELGHAST}"' in page and f'href="{website.PYRRHUS}"' in page, "sister port links missing")
        expect("Discussions" not in page and "prefers-color-scheme" not in page, "Discussions or dark mode on the page")
        expect(f'content="{website.SITE_URL}{website.SOCIAL}"' in page, "og:image not an absolute Pages URL")
        expect(not website.lint(page), f"lint on the generated page: {website.lint(page)}")
        (root / website.PAGE).write_text(page + "x")
        expect(run("--root", r, "--check")[0] == 1, "stale page passes")
        for bad, why in (("<script>x</script>", "injected script"), ('<img src="https://example.com/a.png">', "outside image"),
                         ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=X">', "Google Fonts link"),
                         ('<link rel="preconnect" href="https://fonts.gstatic.com">', "preconnect")):
            (root / website.PAGE).write_text(page.replace("<body>", "<body>" + bad))
            expect(run("--root", r, "--check")[0] == 1, f"{why} passes")
        (root / website.PAGE).write_text(page)
        (root / website.FONT_DIR / website.FONT_FILES[0]).write_bytes(b"x" * 100)
        expect(run("--root", r, "--check")[0] == 1, "a font file that is not woff2 passes")

        css_bad = tokens_css(ink="#000000")
        for name, kw, msg in (("noshot", {"shots": False}, "screenshot"), ("nosocial", {"social": False}, "social-preview"),
                              ("nocss", {"css": None}, "style.css"), ("noreq", {"req": None}, "requirements.md"),
                              ("badreq", {"req": REQ.replace("## To run", "## Run")}, "To run"),
                              ("noreadme", {"readme": "# x\n"}, "Status"),
                              ("noofficial", {"readme": README.replace("**Official channels:**", "Channels:")}, "Official channels"),
                              ("nofont", {"fonts": False}, "woff2"),
                              ("badtoken", {"css": css_bad}, "token --ink"),
                              ("cssurl", {"css": tokens_css() + "a{background:url(https://example.com/x.png)}"}, "style.css loads"),
                              ("cssdark", {"css": tokens_css() + "@media (prefers-color-scheme: dark){a{color:red}}"}, "prefers-color-scheme"),
                              ("cssimport", {"css": tokens_css() + "@import url(x.css);"}, "@import")):
            root = pathlib.Path(t) / name
            fixture(root, **kw)
            if name in ("nofont",):      # generating works without the fonts (they are made from the page); --check refuses
                expect(run("--root", str(root))[0] == 0, f"{name}: generate fails")
                rc, err = run("--root", str(root), "--check")
            else:
                rc, err = run("--root", str(root))
            expect(rc == 1 and msg in err, f"{name}: passes or names the wrong problem: {err!r}")
            rc, err = run("--root", str(root), "--check")
            expect(rc == 1, f"{name}: check passes")

    for bad in ('<script src="a.js"></script>', '<img src="x.png" onerror="x()">', '<a href="javascript:x()">a</a>',
                '<img src="https://example.com/a.png">', '<link rel="stylesheet" href="https://cdn.example/x.css">',
                '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=X">',
                '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>', '<img src="file:///C:/a.png">',
                '<img src="//example.com/a.png">', '<meta property="og:image" content="https://example.com/a.png">',
                "see work/notes.md"):
        expect(website.lint('<meta http-equiv="Content-Security-Policy" content="x">' + bad), f"lint misses {bad}")
    for good in ('<link rel="stylesheet" href="style.css">', '<img src="../docs/assets/a.png">',
                 f'<a href="{website.REPO}/issues">issues</a>'):
        expect(not website.lint('<meta http-equiv="Content-Security-Policy" content="x">' + good), f"lint refuses {good}")

    # contrast: the table passes, and a pair below 4.5 is reported
    expect(not website.contrast_problems(), f"contrast table: {website.contrast_problems()}")
    expect(website.contrast("#000000", "#ffffff") > 20.9 and website.contrast("#ffffff", "#ffffff") == 1, "contrast formula wrong")
    keep = website.PAIRS
    website.PAIRS = keep + (("brown", "cream", "known bad"), ("orange", "cream", "known bad"))
    expect(len(website.contrast_problems()) == 2, "a pair below 4.5 is not reported")
    website.PAIRS = keep

    # the real repo: the page on disk is fresh (skipped when run from a copy without it); NOTICE carries the credits
    real = pathlib.Path(HERE).parents[1]
    if (real / website.PAGE).exists():
        rc, err = run("--root", str(real), "--check")
        expect(rc == 0, f"real repo: {err}")
        notice = (real / "NOTICE.md").read_text(encoding="utf-8")
        expect("Caveat" in notice and "site/fonts/" in notice, "NOTICE.md: Caveat or the shipped font files missing")
        expect(re.search(r"adapted from \[Project Helghast\]\([^)]*\) by undecuple, MIT", notice), "NOTICE.md: the site style credit is missing")
        for f in ("caveat", "lilitaone", "baloo2", "mplusrounded1c"):
            expect((real / f"licenses/fonts-{f}-OFL.txt").is_file(), f"licenses/fonts-{f}-OFL.txt missing")

    if fails:
        print("FAIL test_website:\n  - " + "\n  - ".join(fails))
        return 1
    print("PASS test_website (generate, sections in order, check, negative controls, lint refusals, contrast)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
