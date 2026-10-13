# Author: Esteban Arguedas (eargueda@cisco.com)
"""Pick up new scenario pages and update the nav and index files to match.

    python scripts/sync_scenarios.py           # update files in place
    python scripts/sync_scenarios.py --check   # report only, exit 1 if anything is out of date

Drop a new `docs/<guide>/scenario-<N>*.md` (starting with a `# Scenario N ...`
heading) and run this. For every guide folder it:
  0. registers brand-new guide folders (index.md, nav section, home card, PDF entry, CMS) via
     sync_guides.py,
  1. adds the page to the mkdocs.yml nav, ordered by scenario number
     (removes nav entries whose file was deleted),
  2. adds/removes its row in the "What you'll do" table of <guide>/index.md
     (descriptions of existing rows are left as you wrote them),
  3. refreshes the "N scenarios" count on the guide's card in docs/index.md,
  4. then re-syncs nav labels from the page headings (sync_nav_titles.py),
  5. and refreshes the guides/scripts tables in README.md (update_readme.py).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sync_guides  # noqa: E402
import sync_nav_titles as titles  # noqa: E402
import update_readme  # noqa: E402

ROOT, DOCS, CONFIG = titles.ROOT, titles.DOCS, titles.CONFIG
SCENARIO_FILE = re.compile(r"^scenario-(\d+)")
NAV_ENTRY = re.compile(r"^(\s*-\s+)(?:[^:\n]+?:\s+)?([^\s#:]+\.md)\s*$")
ROW = re.compile(r"^\|\s*\[Scenario (\d+)\]\(([^)]+)\)\s*\|(.*)\|\s*$")
STATS = re.compile(r"(<strong>)\d+(</strong> scenarios)")


def scenarios(guide):
    """Scenario pages of a guide as [(number, filename)], sorted by number."""
    found = [(int(m.group(1)), p.name) for p in (DOCS / guide).glob("scenario-*.md")
             if (m := SCENARIO_FILE.match(p.name))]
    return sorted(found)


def guides():
    return sorted(p.name for p in DOCS.iterdir() if p.is_dir() and scenarios(p.name))


def read(path):
    raw = path.read_bytes().decode("utf-8")
    return raw.replace("\r\n", "\n"), "\r\n" in raw


def write(path, text, crlf):
    path.write_bytes((text.replace("\n", "\r\n") if crlf else text).encode("utf-8"))


def desc_from_h1(path):
    h1 = next((l[2:] for l in path.read_text(encoding="utf-8").splitlines() if l.startswith("# ")), path.stem)
    h1 = " ".join(h1.split())
    return re.sub(r"^Scenario\s+\d+\s*[·•:–—-]*\s*", "", h1) or h1


def sync_nav(guide, lines, check):
    """Add missing scenario entries (ordered by number) and drop deleted ones."""
    prefix, changes = f"{guide}/", []
    files = dict((n, f) for n, f in scenarios(guide))
    listed = {}  # filename -> line index
    for i, l in enumerate(lines):
        m = NAV_ENTRY.match(l.rstrip("\r\n"))
        if m and m.group(2).startswith(prefix) and SCENARIO_FILE.match(Path(m.group(2)).name):
            listed[Path(m.group(2)).name] = i
    for name, i in sorted(listed.items(), key=lambda kv: -kv[1]):
        if name not in files.values():
            changes.append(f"nav: removed {prefix}{name}")
            del lines[i]
    listed = {n: i for n, i in listed.items() if n in files.values()}
    for num, name in scenarios(guide):
        if name in listed:
            continue
        # insert before the first listed scenario with a higher number, else after the last one
        later = [i for n, i in listed.items() if int(SCENARIO_FILE.match(n).group(1)) > num]
        earlier = [i for n, i in listed.items() if int(SCENARIO_FILE.match(n).group(1)) < num]
        if later:
            at = min(later)
        elif earlier:
            at = max(earlier) + 1
        else:  # first scenario of the guide: after the guide's last listed page
            pages = [i for i, l in enumerate(lines)
                     if (m := NAV_ENTRY.match(l.rstrip("\r\n"))) and m.group(2).startswith(prefix)]
            if not pages:
                changes.append(f"nav: {prefix}{name} not added (guide has no nav section)")
                continue
            at = max(pages) + 1
        indent = re.match(r"\s*-\s+", lines[min(listed.values(), default=at - 1)] if listed else lines[at - 1]).group(0)
        lines.insert(at, f"{indent}{prefix}{name}\n")
        listed = {n: (i + 1 if i >= at else i) for n, i in listed.items()}
        listed[name] = at
        changes.append(f"nav: added {prefix}{name}")
    return changes


def sync_table(guide, check):
    index = DOCS / guide / "index.md"
    if not index.exists():
        return []
    text, crlf = read(index)
    lines = text.split("\n")
    rows = {i: ROW.match(l) for i, l in enumerate(lines) if ROW.match(l)}
    if not rows:
        return []
    files = dict(scenarios(guide))
    existing = {int(m.group(1)): m for m in rows.values()}
    changes, out = [], []
    for num, name in sorted(files.items()):
        m = existing.get(num)
        row = f"| [Scenario {num}]({name}) |{m.group(3)}|" if m else \
            f"| [Scenario {num}]({name}) | {desc_from_h1(DOCS / guide / name)} |"
        if not m:
            changes.append(f"index: added Scenario {num} to {guide}/index.md")
        elif m.group(2) != name:
            changes.append(f"index: Scenario {num} link -> {name} in {guide}/index.md")
        out.append(row)
    for num in set(existing) - set(files):
        changes.append(f"index: removed Scenario {num} from {guide}/index.md")
    first, last = min(rows), max(rows)
    new_lines = lines[:first] + out + lines[last + 1:]
    if changes and not check:
        write(index, "\n".join(new_lines), crlf)
    return changes


def sync_home(check):
    home = DOCS / "index.md"
    text, crlf = read(home)
    changes = []
    parts = re.split(r"(?=<div class=\"cpoc-card\")", text)
    for k, part in enumerate(parts):
        for guide in guides():
            if f"]({guide}/index.md)" in part and STATS.search(part):
                count = len(scenarios(guide))
                new = STATS.sub(rf"\g<1>{count}\g<2>", part, count=1)
                if new != part:
                    changes.append(f"home: {guide} card now says {count} scenarios")
                    parts[k] = new
    if changes and not check:
        write(home, "".join(parts), crlf)
    return changes


def warn_ignored():
    """Flag scenario-like files that are skipped because they are not `scenario-<N>*.md`."""
    for p in sorted(DOCS.glob("*/scenario-*")):
        if p.is_file() and p.suffix.lower() != ".md" and p.suffix.lower() not in {".png", ".jpg", ".jpeg", ".gif"}:
            print(f"WARNING: {p.relative_to(ROOT)} ignored, it must end in .md (rename to {p.name}.md)")


def main():
    check = "--check" in sys.argv
    warn_ignored()
    changes = sync_guides.sync(check)  # register brand-new guide folders first
    lines = CONFIG.read_text(encoding="utf-8").splitlines(keepends=True)
    for guide in guides():
        changes += sync_nav(guide, lines, check)
        changes += sync_table(guide, check)
    changes += sync_home(check)
    if any(c.startswith("nav") for c in changes) and not check:
        CONFIG.write_text("".join(lines), encoding="utf-8")
    for c in changes:
        print(("WOULD " if check else "") + c)
    titles_changed = titles.sync(check)
    if not check:
        update_readme.main()
    if not changes and not titles_changed:
        print("scenario nav and indexes OK")
    return 1 if check and (changes or titles_changed) else 0


if __name__ == "__main__":
    sys.exit(main())
