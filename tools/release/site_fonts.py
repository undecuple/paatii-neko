#!/usr/bin/env python3
"""Subset the project page's fonts to site/fonts/*.woff2 (maintainer-side; needs fontTools and brotli, and the OFL
font files in a folder outside the repository).

    nix shell nixpkgs#python3Packages.fonttools nixpkgs#python3Packages.brotli --command \
        python3 tools/release/site_fonts.py FONT_DIR

Latin faces (Lilita One, Baloo 2, Caveat): basic Latin, Latin-1 and typographic punctuation. M PLUS Rounded 1c
ExtraBold: only the Japanese characters that site/index.html contains (so regenerate the page first). The files
are SIL OFL 1.1 subsets; the licence texts are in licenses/. The sources are not in this repository.
"""
import pathlib
import sys

from fontTools import subset
from fontTools.varLib import instancer

ROOT = pathlib.Path(__file__).resolve().parents[2]
LATIN = list(range(0x20, 0x7F)) + list(range(0xA0, 0x100)) + [0x2013, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D,
                                                              0x2022, 0x2026, 0x2192, 0x2190]
# (output name, source file in the font folder)
LATIN_FACES = (("lilitaone.woff2", "LilitaOne-Regular.ttf"), ("baloo2.woff2", "Baloo2[wght].ttf"),
               ("caveat.woff2", "Caveat[wght].ttf"))
# variable faces pinned to one weight (the page uses Caveat at a single weight, which keeps the file small)
PINNED = {"caveat.woff2": {"wght": 500}}
JP_FACE = ("mplusrounded1c-800.woff2", "MPLUSRounded1c-ExtraBold.ttf")


def japanese(page):
    return sorted({c for c in page if ord(c) >= 0x3000})


def make(src, dst, codepoints, pin=None):
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern", "liga", "calt", "locl", "mark", "mkmk"]
    opts.notdef_outline = True
    opts.name_IDs = [0, 1, 2, 3, 4, 5, 6, 13, 14]
    f = subset.load_font(str(src), opts)
    if pin:
        f = instancer.instantiateVariableFont(f, pin)
    s = subset.Subsetter(opts)
    s.populate(unicodes=codepoints)
    s.subset(f)
    subset.save_font(f, str(dst), opts)
    return dst.stat().st_size


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    src = pathlib.Path(argv[1])
    out = ROOT / "site/fonts"
    out.mkdir(parents=True, exist_ok=True)
    total = 0
    for name, file in LATIN_FACES:
        n = make(src / file, out / name, LATIN, PINNED.get(name))
        print(f"{name}: {n} bytes")
        total += n
    jp = japanese((ROOT / "site/index.html").read_text(encoding="utf-8"))
    n = make(src / JP_FACE[1], out / JP_FACE[0], [ord(c) for c in jp])
    print(f"{JP_FACE[0]}: {n} bytes ({''.join(jp)})")
    print(f"total {total + n} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
