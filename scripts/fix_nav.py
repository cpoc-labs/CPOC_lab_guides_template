# Author: Esteban Arguedas (eargueda@cisco.com)
"""Auto-fix mkdocs.yml nav entries that point at renamed/moved pages.

Run before `mkdocs build --strict` (the deploy workflow does this) or locally:

    python scripts/fix_nav.py           # fix mkdocs.yml in place
    python scripts/fix_nav.py --check   # report only, exit 1 if anything is broken

For each nav entry whose file no longer exists, the new location is found by:
  1. git rename history (`git log -M`), when history is available, then
  2. the closest-named page in the same folder that the nav does not use yet.
Entries that cannot be resolved confidently are reported and exit code is 1.

Deletions are not renames: entries of a guide whose folder is gone, or of a scenario page that was
deleted, are left alone here and removed by sync_scenarios.py / sync_guides.py.
"""
import difflib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
CONFIG = ROOT / "mkdocs.yml"
SCENARIO_FILE = re.compile(r"^scenario-\d+")
NAV_LINE = re.compile(r"^(\s*-\s+(?:[^:\n]+:\s+)?)([^\s#]+\.md)(\s*)$")


def git_renames():
    """Map old docs path -> newest path from git history (empty if unavailable)."""
    try:
        out = subprocess.run(
            ["git", "log", "-M", "--diff-filter=R", "--name-status", "--format=",
             "--", "docs"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return {}
    renames = {}
    for line in out.splitlines():  # newest commit first
        parts = line.split("\t")
        if len(parts) == 3 and parts[0].startswith("R"):
            old, new = (p.removeprefix("docs/") for p in parts[1:])
            renames.setdefault(old, new)
    for old in list(renames):  # follow chains: a -> b -> c
        seen = {old}
        while renames[old] in renames and renames[old] not in seen:
            seen.add(renames[old])
            renames[old] = renames[renames[old]]
    return renames


def resolve(missing, renames, unused):
    target = renames.get(missing)
    if target and (DOCS / target).exists():
        return target
    folder = Path(missing).parent.as_posix()
    cands = [p for p in unused if Path(p).parent.as_posix() == folder]
    if len(cands) == 1:
        return cands[0]
    match = difflib.get_close_matches(Path(missing).stem,
                                      [Path(c).stem for c in cands], n=1, cutoff=0.6)
    return next((c for c in cands if Path(c).stem == match[0]), None) if match else None


def main():
    check_only = "--check" in sys.argv
    lines = CONFIG.read_text(encoding="utf-8").splitlines(keepends=True)
    in_nav = False
    refs = []  # (line index, path)
    for i, line in enumerate(lines):
        if line.startswith("nav:"):
            in_nav = True
        elif in_nav and line.strip() and not line[0].isspace():
            in_nav = False
        m = in_nav and NAV_LINE.match(line.rstrip("\r\n"))
        if m:
            refs.append((i, m.group(2)))

    used = {p for _, p in refs}
    all_pages = {p.relative_to(DOCS).as_posix() for p in DOCS.rglob("*.md")}
    unused = sorted(all_pages - used)
    missing = [(i, p) for i, p in refs if p not in all_pages]
    if not missing:
        print("nav OK: every entry points at an existing page")
        return 0

    renames, unresolved = git_renames(), 0
    for i, old in missing:
        new = resolve(old, renames, unused)
        guide_gone = not any((DOCS / Path(old).parts[0]).glob("*.md"))
        if not new and (guide_gone or SCENARIO_FILE.match(Path(old).name)):
            print(f"DELETED: {old} (left for sync_scenarios.py to remove from the nav)")
            continue
        if not new:
            print(f"UNRESOLVED: {old} (no matching page found)")
            unresolved += 1
            continue
        unused.remove(new) if new in unused else None
        print(f"{'WOULD FIX' if check_only else 'FIXED'}: {old} -> {new}")
        lines[i] = lines[i].replace(old, new)
    if not check_only:
        CONFIG.write_text("".join(lines), encoding="utf-8")
    return 1 if unresolved or check_only else 0


if __name__ == "__main__":
    sys.exit(main())
