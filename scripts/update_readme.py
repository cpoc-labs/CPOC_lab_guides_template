"""Regenerate the auto-maintained tables in README.md.

    python scripts/update_readme.py           # rewrite README.md in place
    python scripts/update_readme.py --check   # report only, exit 1 if README is stale

Only the text between these marker pairs is replaced; the rest of the README is yours:
    <!-- auto:guides:start --> ... <!-- auto:guides:end -->    guides table (from mkdocs.yml nav)
    <!-- auto:scripts:start --> ... <!-- auto:scripts:end -->  scripts table (docstring first lines)
"""
import ast
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
CONFIG = ROOT / "mkdocs.yml"
DOCS = ROOT / "docs"


def guides_table():
    nav = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))["nav"]
    rows = ["| Guide | Folder | Scenarios | Nav section label in `mkdocs.yml` |", "|---|---|---|---|"]
    for item in nav:
        for label, pages in item.items():
            if not isinstance(pages, list):
                continue
            paths = [p for e in pages for p in e.values() if isinstance(p, str)] if \
                all(isinstance(e, dict) for e in pages) else []
            folders = {Path(p).parent.as_posix() for p in paths if "/" in p}
            if len(folders) != 1:
                continue
            folder = folders.pop()
            count = len(list((DOCS / folder).glob("scenario-*.md")))
            rows.append(f"| {label} | `docs/{folder}/` | {count} | `{label}` |")
    return "\n".join(rows)


def scripts_table():
    rows = ["| Script | What it does |", "|---|---|"]
    for path in sorted((ROOT / "scripts").glob("*.py")):
        doc = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8"))) or ""
        first = doc.strip().splitlines()[0] if doc.strip() else ""
        rows.append(f"| `scripts/{path.name}` | {first} |")
    return "\n".join(rows)


def replace_block(text, name, body):
    pattern = re.compile(rf"(<!-- auto:{name}:start -->).*?(<!-- auto:{name}:end -->)", re.S)
    if not pattern.search(text):
        print(f"WARNING: marker pair auto:{name} not found in README.md")
        return text
    return pattern.sub(lambda m: f"{m.group(1)}\n{body}\n{m.group(2)}", text)


def main():
    check = "--check" in sys.argv
    raw = README.read_bytes().decode("utf-8")
    crlf = "\r\n" in raw
    old = raw.replace("\r\n", "\n")
    new = replace_block(old, "guides", guides_table())
    new = replace_block(new, "scripts", scripts_table())
    if new == old:
        print("README OK")
        return 0
    if check:
        print("README is out of date (run python scripts/update_readme.py)")
        return 1
    README.write_bytes((new.replace("\n", "\r\n") if crlf else new).encode("utf-8"))
    print("README updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
