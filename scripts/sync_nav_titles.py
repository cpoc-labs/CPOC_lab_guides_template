"""Keep mkdocs.yml nav labels for scenario pages in sync with each page's H1.

    python scripts/sync_nav_titles.py           # rewrite mkdocs.yml in place
    python scripts/sync_nav_titles.py --check   # report only, exit 1 if out of sync

Edit the `# Scenario N ...` heading in a lab guide page and run this (the deploy
workflow does) so the left-pane nav shows the same title.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
CONFIG = ROOT / "mkdocs.yml"
NAV_LINE = re.compile(r"^(\s*-\s+)(?:([^:\n]+?):\s+)?([^\s#:]+\.md)(\s*)$")
# Guide folders that keep short hand-written nav labels; every other guide (including new ones
# registered by sync_guides.py) follows the page H1.
MANUAL_LABELS = ()
SCENARIO = re.compile(r"^(?!(?:%s)/)[^/]+/scenario-[^/]*\.md$" % "|".join(map(re.escape, MANUAL_LABELS)))
SEPARATOR = re.compile(r"^(Scenario\s+\d+)\s*[·•:–—-]*\s*(?=\S)")


def page_title(path):
    """Nav label from the first H1: 'Scenario 2 <tab> Foo' -> 'Scenario 2 - Foo'."""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            title = " ".join(line[2:].split())
            m = SEPARATOR.match(title)
            return f"{m.group(1)} - {title[m.end():]}" if m and title[m.end():] else title
    return None


def sync(check_only=False):
    lines = CONFIG.read_text(encoding="utf-8").splitlines(keepends=True)
    in_nav, changes = False, 0
    for i, line in enumerate(lines):
        if line.startswith("nav:"):
            in_nav = True
            continue
        if in_nav and line.strip() and not line[0].isspace():
            in_nav = False
        m = in_nav and NAV_LINE.match(line.rstrip("\r\n"))
        if not m or not SCENARIO.search(m.group(3)):
            continue
        page = DOCS / m.group(3)
        title = page.exists() and page_title(page)
        if not title or title == m.group(2):
            continue
        eol = line[len(line.rstrip("\r\n")):]
        print(f"{'OUT OF SYNC' if check_only else 'UPDATED'}: {m.group(3)}: "
              f"{m.group(2)!r} -> {title!r}")
        label = f'"{title}"' if re.search(r": |^[\W]", title) else title
        lines[i] = f"{m.group(1)}{label}: {m.group(3)}{eol}"
        changes += 1
    if changes and not check_only:
        CONFIG.write_text("".join(lines), encoding="utf-8")
    if not changes:
        print("nav titles OK")
    return changes


if __name__ == "__main__":
    check = "--check" in sys.argv
    sys.exit(1 if sync(check) and check else 0)
