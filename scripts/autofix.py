# Author: Esteban Arguedas (eargueda@cisco.com)
"""Repair the common mistakes that break `mkdocs build --strict`, then sync nav/indexes.

    python scripts/autofix.py           # fix in place
    python scripts/autofix.py --check   # report only, exit 1 if anything needs fixing

Steps, in order:
  1. Scenario pages saved without a proper extension (`scenario-1`, `scenario-2.markdown`,
     `scenario-3.MD`, `scenario-4.txt`) are renamed to `scenario-<N>....md` so they get picked up.
  2. Image links that point at a file that does not exist are repaired by finding the image:
     the same name in another guide (only when every copy is identical), or the same name with a different extension or
     letter case in the page's own images folder. Links that cannot be repaired are listed and make
     the script exit 1 (a real missing screenshot has to be added by a person).
  3. fix_nav.py: nav entries of renamed pages follow the rename; deleted pages are left for step 4.
  4. sync_scenarios.py: registers new guides, drops deleted guides/scenarios from the nav, home page,
     PDF list and CMS, and refreshes indexes, counts and titles.
"""
import hashlib
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import unquote

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fix_nav  # noqa: E402
import sync_guides  # noqa: E402
import sync_scenarios  # noqa: E402

ROOT, DOCS = sync_scenarios.ROOT, sync_scenarios.DOCS
IMG_LINK = re.compile(r"""!\[[^\]]*\]\(\s*<?([^)\s>]+)|<img\b[^>]*?\bsrc=["']([^"']+)["']""", re.I)
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}


def guide_dirs():
    return [p for p in sorted(DOCS.iterdir()) if p.is_dir() and p.name not in sync_guides.NOT_GUIDES]


def fix_page_extensions(check):
    changes = []
    for guide in guide_dirs():
        for p in sorted(guide.glob("scenario-*")):
            if not p.is_file() or p.suffix.lower() in IMAGE_EXT or p.suffix == ".md":
                continue
            if p.suffix.lower() not in {"", ".md", ".markdown", ".txt"}:
                continue  # e.g. "scenario-1.2" or an unrelated asset: not ours to guess
            target = p.with_name((p.stem if p.suffix else p.name) + ".md")
            if target.exists() and not target.samefile(p):
                changes.append(f"WARNING {p.relative_to(DOCS)}: cannot rename, {target.name} already exists")
                continue
            changes.append(f"renamed {p.relative_to(DOCS)} -> {target.name}")
            if not check:
                tmp = p.with_name(p.name + ".tmp-rename")  # two steps: case-only renames on Windows
                p.rename(tmp)
                tmp.rename(target)
    return changes


def find_image(page, ref):
    """(replacement, None) for the missing image `ref` linked from `page`; (None, reason) if none is safe."""
    want = (page.parent / ref).resolve()
    if want.parent.is_dir():  # same name, other case or extension, in the page's own images folder
        for f in want.parent.iterdir():
            if f.is_file() and f.stem.lower() == want.stem.lower() and f.suffix.lower() in IMAGE_EXT:
                return f, None
    found = sorted(p for p in DOCS.rglob(want.name) if p.is_file() and p.resolve() != want)
    distinct = {hashlib.md5(p.read_bytes()).hexdigest(): p for p in found}  # identical copies count once
    if len(distinct) == 1:
        return next(iter(distinct.values())), None
    if not distinct:
        return None, "no file with that name anywhere in docs/"
    where = ", ".join(str(p.relative_to(DOCS)) for p in distinct.values())
    return None, f"{len(distinct)} different images share that name ({where}), copy the right one by hand"


def fix_images(check):
    changes, unresolved, seen = [], [], set()
    for page in sorted(DOCS.rglob("*.md")):
        if page.relative_to(DOCS).parts[0] in sync_guides.NOT_GUIDES - {"images"}:
            continue
        text = page.read_text(encoding="utf-8")
        for m in IMG_LINK.finditer(text):
            ref = unquote((m.group(1) or m.group(2)).split("#")[0].split("?")[0])
            if not ref or re.match(r"^(?:[a-z]+:|/|\{)", ref, re.I) or Path(ref).suffix.lower() not in IMAGE_EXT:
                continue
            dest = (page.parent / ref).resolve()
            if dest.is_file() or (page, dest) in seen:
                continue
            seen.add((page, dest))
            src, why = find_image(page, ref)
            name = f"{page.relative_to(DOCS)}: {ref}"
            if not src:
                unresolved.append(f"UNRESOLVED image {name} ({why})")
                continue
            changes.append(f"image: {name} <- {src.relative_to(DOCS)}")
            if not check:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dest)
    return changes, unresolved


def main():
    check = "--check" in sys.argv
    problems = 0

    changes = fix_page_extensions(check)
    img_changes, unresolved = fix_images(check)
    for c in changes + img_changes + unresolved:
        print(("WOULD " if check and not c.startswith(("WARNING", "UNRESOLVED")) else "") + c)
    problems += len(changes) + len(img_changes) + len(unresolved)

    if fix_nav.main() != 0:
        problems += 1
    if sync_scenarios.main() != 0:
        problems += 1

    if unresolved:
        print(f"\n{len(unresolved)} image(s) could not be repaired: add the missing file(s) or fix the link(s).")
    return 1 if unresolved or (check and problems) else 0


if __name__ == "__main__":
    sys.exit(main())
