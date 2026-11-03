#!/usr/bin/env python3
"""Check .recomp.json (recomp.fyi schema v1) against the repo.

  python3 tools/release/recomp_card.py [--root R] [--sfo PARAM.SFO | --no-sfo] [--write]

Checks, one line per problem on stderr, exit 1 when there is any:
  - the card parses and uses only schema v1 fields (private extensions start with "x-");
  - wikidata matches ^Q[1-9][0-9]*$; maintainers[].link and links[].url start with https://;
  - status is a schema value and agrees with the README "**Status: ...**" line (and the status badge, if there is one) and with the
    release criteria (docs/RELEASE-CRITERIA.md; without that file no criteria are met, so "released" and "complete"
    are not allowed);
  - links into the repo (blob/tree paths, #anchors on the README) name a file or heading that exists;
  - original.serial and original.revision equal the setup's: TITLE_ID and APP_VER of the disc's PARAM.SFO, read
    with tools/disc_info.py (default $TLP_GAME or Game/PS3_GAME/PARAM.SFO; skipped with a note when absent).
--write fixes the fields that follow from one source. Stub: it would set status to "in-progress" when the criteria
are not met and the card says released or complete; it changes nothing else and prints what it did.
No network, no git.
"""
import argparse
import json
import os
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]

TOP = {"$schema", "game", "wikidata", "system", "type", "original", "project", "status", "targets", "toolchain",
       "approach", "maintainers", "links", "help", "tags", "notes"}
ORIGINAL = {"region", "revision", "serial", "sha1"}
STATUS = ("exploring", "in-progress", "playable", "released", "complete", "paused", "unknown")
TYPES = ("recomp", "port", "decomp")
LATE = ("released", "complete")           # allowed only when the release criteria are met
CRITERIA = "docs/RELEASE-CRITERIA.md"
# README status words -> card statuses that agree with them
README_STATUS = {
    "exploring": {"exploring"},
    "work in progress": {"in-progress"},
    "partly playable": {"in-progress"},
    "playable": {"playable", "released", "complete"},
    "released": {"released", "complete"},
    "paused": {"paused"},
}
FALLBACK_REPO = "undecuple/paatii-neko"


def as_list(v):
    return v if isinstance(v, list) else [v]


def criteria_met(root):
    """(met, why). No criteria file means nothing is met. The file says `Criteria met: yes` when they are."""
    p = root / CRITERIA
    if not p.is_file():
        return False, f"{CRITERIA} does not exist, so no release criteria are met"
    m = re.search(r"^Criteria met:\s*(yes|no)\s*$", p.read_text(encoding="utf-8"), re.M | re.I)
    if m and m.group(1).lower() == "yes":
        return True, ""
    return False, f"{CRITERIA} does not say 'Criteria met: yes'"


def readme_status(text):
    """(badge words, line words), either None when absent."""
    b = re.search(r"img\.shields\.io/badge/status-([A-Za-z0-9%_-]+?)-", text)
    badge = re.sub(r"%20|_", " ", b.group(1)).replace("--", "-").lower() if b else None
    s = re.search(r"^(?:>\s*)?\*\*Status:\s*([^.*]+?)\.?\*\*", text, re.M)
    return badge, (s.group(1).strip().lower() if s else None)


def slug(heading):
    h = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", heading)
    h = re.sub(r"[`*_~]", "", h).strip().lower()
    return re.sub(r"\s", "-", re.sub(r"[^\w\s-]", "", h))


def anchors(text):
    out, fence = set(), False
    for ln in text.splitlines():
        if ln.startswith("```"):
            fence = not fence
        elif not fence:
            m = re.match(r"#{1,6}\s+(.*?)\s*#*\s*$", ln)
            if m:
                out.add(slug(m.group(1)))
    return out


def repo_slug(root):
    p = root / "CITATION.cff"
    if p.is_file():
        m = re.search(r'^repository-code:\s*"?https://github\.com/([^"\s]+?)"?\s*$', p.read_text(encoding="utf-8"), re.M)
        if m:
            return m.group(1)
    return FALLBACK_REPO


def setup_ids(root, sfo):
    """(serial, revision, note) from PARAM.SFO through tools/disc_info.read_sfo; ids None when unavailable."""
    if sfo is None:
        sfo = pathlib.Path(os.environ.get("TLP_GAME", root / "Game")) / "PS3_GAME" / "PARAM.SFO"
    sfo = pathlib.Path(sfo)
    if not sfo.is_file():
        return None, None, f"PARAM.SFO not found ({sfo.name}): serial and revision not compared"
    ns = {"__name__": "disc_info"}          # run the file's own reader; exec leaves no bytecode behind
    src = (root / "tools" / "disc_info.py").read_text(encoding="utf-8")
    exec(compile(src, "disc_info.py", "exec"), ns)
    f = ns["read_sfo"](str(sfo))
    return f.get("TITLE_ID"), f.get("APP_VER"), ""


def check_links(card, root, problems):
    repo = repo_slug(root)
    pre = f"https://github.com/{repo}"
    readme = root / "README.md"
    heads = anchors(readme.read_text(encoding="utf-8")) if readme.is_file() else set()
    urls = [("links", l.get("url", "")) for l in card.get("links", []) if isinstance(l, dict)]
    for what, url in urls:
        if not isinstance(url, str) or not (url == pre or url.startswith((pre + "/", pre + "#"))):
            continue
        rest = url[len(pre):]
        path, _, frag = rest.partition("#")
        m = re.fullmatch(r"/(?:blob|tree)/[^/]+/(.*)", path)
        if path in ("", "/"):
            target = "README.md"
        elif m:
            target = m.group(1)
        else:
            continue                      # /releases, /issues and the like exist on GitHub, not in the tree
        if target and not (root / target).exists():
            problems.append(f"{what}: {url}: {target} does not exist in the repo")
        elif frag and target == "README.md" and frag not in heads:
            problems.append(f"{what}: {url}: no README heading with anchor #{frag}")


def check(root, sfo=None, use_sfo=True):
    """(problems, notes) for the card at root."""
    problems, notes = [], []
    p = root / ".recomp.json"
    try:
        card = json.loads(p.read_text(encoding="utf-8"))
    except OSError as e:
        return [f".recomp.json: {e.strerror or e}"], notes
    except ValueError as e:
        return [f".recomp.json does not parse: {e}"], notes
    if not isinstance(card, dict):
        return [".recomp.json is not an object"], notes
    for k in card:
        if k not in TOP and not k.startswith("x-"):
            problems.append(f"field '{k}' is not in schema v1 (private fields start with x-)")
    wd = card.get("wikidata")
    if wd is not None and not (isinstance(wd, str) and re.fullmatch(r"Q[1-9][0-9]*", wd)):
        problems.append(f"wikidata {wd!r} does not match ^Q[1-9][0-9]*$")
    for t in as_list(card.get("type", [])):
        if t not in TYPES:
            problems.append(f"type {t!r} is not one of {', '.join(TYPES)}")
    for i, m in enumerate(card.get("maintainers", [])):
        if not isinstance(m, dict) or not m.get("name"):
            problems.append(f"maintainers[{i}] has no name")
        elif "link" in m and not str(m["link"]).startswith("https://"):
            problems.append(f"maintainers[{i}].link does not start with https://")
    for i, l in enumerate(card.get("links", [])):
        if not isinstance(l, dict) or not str(l.get("url", "")).startswith("https://"):
            problems.append(f"links[{i}].url does not start with https://")
    originals = [o for o in as_list(card.get("original", [])) if isinstance(o, dict)]
    for o in originals:
        for k in o:
            if k not in ORIGINAL:
                problems.append(f"original.{k} is not in schema v1")
        if "sha1" in o and not re.fullmatch(r"[0-9a-fA-F]{40}", str(o["sha1"])):
            problems.append("original.sha1 is not 40 hex digits")
    # status
    status = card.get("status")
    if status is not None and status not in STATUS:
        problems.append(f"status {status!r} is not one of {', '.join(STATUS)}")
    met, why = criteria_met(root)
    if status in LATE and not met:
        problems.append(f"status {status!r} but {why}")
    readme = root / "README.md"
    if readme.is_file() and status in STATUS:
        # The "**Status: ...**" line is required; a status badge is optional (shared readme-skeleton.md: no static
        # label badges), and checked against the line when there is one.
        badge, line = readme_status(readme.read_text(encoding="utf-8"))
        if line is None:
            problems.append("README.md has no '**Status: ...**' line to compare")
        else:
            if badge is not None and badge != line:
                problems.append(f"README status badge '{badge}' and status line '{line}' differ")
            for w in [x for x in (badge, line) if x is not None]:
                ok = README_STATUS.get(w)
                if ok is None:
                    problems.append(f"README status '{w}' is not one the check knows")
                elif status not in ok and status != "unknown":
                    problems.append(f"card status '{status}' disagrees with README status '{w}'")
    check_links(card, root, problems)
    # serial / revision
    if use_sfo:
        serial, rev, note = setup_ids(root, sfo)
        if note:
            notes.append(note)
        elif originals:
            for o in originals:
                if "serial" in o and o["serial"] != serial:
                    problems.append(f"original.serial {o['serial']!r} but the setup checks {serial!r}")
                if "revision" in o and o["revision"] != rev:
                    problems.append(f"original.revision {o['revision']!r} but the setup checks {rev!r}")
    return problems, notes


def write(root):
    """Stub: the one field derivable from one source today is status (capped by the release criteria)."""
    p = root / ".recomp.json"
    card = json.loads(p.read_text(encoding="utf-8"))
    met, why = criteria_met(root)
    if card.get("status") in LATE and not met:
        text = p.read_text(encoding="utf-8")
        new = re.sub(r'("status"\s*:\s*)"[^"]*"', r'\1"in-progress"', text, count=1)
        p.write_text(new, encoding="utf-8")
        return [f'status set to "in-progress" ({why})']
    return []


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--sfo", help="PARAM.SFO to take serial and revision from")
    ap.add_argument("--no-sfo", action="store_true", help="skip the serial/revision comparison")
    ap.add_argument("--write", action="store_true", help="fix fields that follow from one source (stub)")
    a = ap.parse_args(argv)
    root = pathlib.Path(a.root)
    if a.write:
        for line in write(root) or ["--write: nothing to change"]:
            print(line)
    problems, notes = check(root, a.sfo, not a.no_sfo)
    for n in notes:
        print("note: " + n, file=sys.stderr)
    for pr in problems:
        print("recomp_card: " + pr, file=sys.stderr)
    if not problems:
        print("recomp_card: ok")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
