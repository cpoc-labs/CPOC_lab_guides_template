# Author: Esteban Arguedas (eargueda@cisco.com)
"""Detect new guide folders under docs/ and register them everywhere, in the existing style.

    python scripts/sync_guides.py           # register new guides in place
    python scripts/sync_guides.py --check   # report only, exit 1 if a guide is not fully registered

A "guide" is any docs/<folder>/ that holds `scenario-<N>*.md` pages (a folder with only an
index.md also counts). For each guide that is missing from one of the places below, it adds:
  1. <folder>/index.md           (only if absent: overview, scenario table, disclaimer, history, PDF button)
  2. mkdocs.yml nav              a new top-level section: Overview, Environment, Get Started,
                                 scenarios (labelled from their H1), What's Next, other pages
  3. docs/index.md               a new card (tag, title, description, scenario count, Start + PDF buttons)
  4. scripts/generate_pdfs.py    a GUIDES entry (cover metadata, PDF file name)
  5. docs/admin/config.yml       a Decap CMS collection

The guide title comes from the H1 of <folder>/index.md (or the folder name if there is none) and the
card description from its "About this CPOC" paragraph. Existing guides are never modified here;
scenario rows, counts and labels are kept current by sync_scenarios.py.

The reverse also holds: when a guide folder is deleted (or no longer holds any .md page), its
nav section, home card, GUIDES entry and CMS collection are removed from the same five places.
"""
import datetime
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sync_nav_titles as titles  # noqa: E402

ROOT, DOCS, CONFIG = titles.ROOT, titles.DOCS, titles.CONFIG
HOME = DOCS / "index.md"
PDF_SCRIPT = ROOT / "scripts" / "generate_pdfs.py"
ADMIN = DOCS / "admin" / "config.yml"

NOT_GUIDES = {"assets", "javascripts", "stylesheets", "admin", "images"}
AUTHOR, EMAIL = "Your Name", "you@example.com"  # TEMPLATE: set to the repo owner
SUBTITLE_LINE = "*Cisco Global Demo Engineering Customer Proof of Concept*"
DEFAULT_TAG = "Cloud-managed"
SCENARIO_FILE = re.compile(r"^scenario-(\d+)")
PAGE_ORDER = ("index.md", "environment.md", "getting-started.md")
FIXED_LABELS = {"index.md": "Overview", "environment.md": "Environment",
                "getting-started.md": "Get Started", "whats-next.md": "What's Next"}

DISCLAIMER = '''## Disclaimer

Test results are suitable to the specific design, configuration, test procedure, and types of switches deployed in the environment described in this document.

This document is provided "As-Is," without warranty of any kind, express or implied, including without limitation those of merchantability, fitness for a particular purpose, and non-infringement arising from a course of dealing usage or trade practice.

All printed copies and duplicate soft copies are not considered controlled; therefore, please refer to the original online version for the latest version.
'''


def read(path):
    raw = path.read_bytes().decode("utf-8")
    return raw.replace("\r\n", "\n"), "\r\n" in raw


def write(path, text, crlf):
    path.write_bytes((text.replace("\n", "\r\n") if crlf else text).encode("utf-8"))


def today():
    d = datetime.date.today()
    return f"{d.day} {d:%B %Y}"


def humanize(folder):
    acronyms = {"cpoc", "ucs"}  # TEMPLATE: add acronyms to keep upper-case in guide titles
    return " ".join(w.upper() if w in acronyms else w.capitalize() for w in re.split(r"[-_]+", folder))


def scenario_pages(folder):
    found = [(int(m.group(1)), p.name) for p in (DOCS / folder).glob("scenario-*.md")
             if (m := SCENARIO_FILE.match(p.name))]
    return [name for _, name in sorted(found)]


def guide_folders():
    return sorted(p.name for p in DOCS.iterdir()
                  if p.is_dir() and p.name not in NOT_GUIDES
                  and (scenario_pages(p.name) or (p / "index.md").exists()))


def h1(path, fallback):
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                return " ".join(line[2:].split())
    return fallback


def guide_title(folder):
    return h1(DOCS / folder / "index.md", humanize(folder))


def about_text(folder, title):
    """First paragraph of '## About this CPOC' in the guide index, trimmed to ~220 chars."""
    index = DOCS / folder / "index.md"
    fallback = f"Step-by-step Customer Proof of Concept lab guide: {title}."
    if not index.exists():
        return fallback
    text = index.read_text(encoding="utf-8").replace("\r\n", "\n")
    m = re.search(r"##\s+About this CPOC\s*\n+(.+?)(?:\n\s*\n|\Z)", text, re.S)
    if not m:
        return fallback
    para = " ".join(m.group(1).split())
    if len(para) <= 220:
        return para
    cut = para[:220]
    end = cut.rfind(". ")
    return cut[:end + 1] if end > 80 else cut.rsplit(" ", 1)[0] + "…"


def guide_pages(folder):
    """Nav entries [(label, 'folder/page.md')] in reading order."""
    pages = [p.name for p in (DOCS / folder).glob("*.md")]
    scen = scenario_pages(folder)
    ordered = [n for n in PAGE_ORDER if n in pages] + scen
    ordered += sorted(n for n in pages if n not in ordered and n != "whats-next.md")
    if "whats-next.md" in pages:
        ordered.append("whats-next.md")
    out = []
    for name in ordered:
        path = DOCS / folder / name
        label = FIXED_LABELS.get(name) or titles.page_title(path) or Path(name).stem.replace("-", " ").title()
        out.append((label, f"{folder}/{name}"))
    return out


def yaml_label(label):
    return f'"{label}"' if re.search(r": |^[\W]", label) else label


# ---- 1. guide index.md --------------------------------------------------------------------------
def scenario_desc(folder, name):
    title = titles.page_title(DOCS / folder / name) or name
    return re.sub(r"^Scenario\s+\d+\s*[-·•:–—]*\s*", "", title)


def build_index(folder, title):
    rows = "\n".join(f"| [Scenario {SCENARIO_FILE.match(n).group(1)}]({n}) | {scenario_desc(folder, n)} |"
                     for n in scenario_pages(folder))
    has = lambda n: (DOCS / folder / n).exists()
    see = "See the [Environment](environment.md) page for lab IP addresses, credentials and equipment, and " \
        if has("environment.md") else "Use "
    begin = "[Get Started](getting-started.md) to begin." if has("getting-started.md") else \
        (f"[Scenario 1]({scenario_pages(folder)[0]}) to begin." if scenario_pages(folder) else "")
    start = "getting-started.md" if has("getting-started.md") else (scenario_pages(folder) or ["index.md"])[0]
    return f'''# {title}

{SUBTITLE_LINE}

**Author:** {AUTHOR} ({EMAIL}) · **Version:** 1.0 · **Last updated:** {today()}

<!-- pdf:skip:start -->
[Download this guide as PDF](#){{ .cpoc-btn data-pdf-guide="{folder}" }}
<!-- pdf:skip:end -->

!!! note "Document status"
    All printed copies and duplicate soft copies of this document are considered uncontrolled. Please refer to the original, online document link for the current version.

## About this CPOC

Describe the purpose of this guide here.

## Scope

### Goals

Describe what the reader will be able to do after completing the scenarios.

## What you'll do

| Scenario | Description |
|---|---|
{rows}

{see}{begin}

{DISCLAIMER}
### Document history

| Revision | Date | Author | Description | Version |
|---|---|---|---|---|
| 1 | {today()} | {AUTHOR.split()[-1]} | {title} | 1.0 |

<!-- pdf:skip:start -->
<div class="cpoc-cta" markdown>
<div class="cpoc-cta-logos">
<img src="../assets/cisco-logo.png" alt="Cisco">
<img src="../assets/cpoc-logo.png" alt="Customer Proof of Concept">
</div>

<div class="cpoc-btn-row" markdown>
[Start the Lab]({start}){{ .cpoc-btn }}
[Convert to PDF](#){{ .cpoc-btn .cpoc-btn--outline data-pdf-guide="{folder}" }}
</div>
</div>
<!-- pdf:skip:end -->
'''


def sync_index(folder, title, check):
    index = DOCS / folder / "index.md"
    if index.exists():
        return []
    if not check:
        index.write_text(build_index(folder, title), encoding="utf-8", newline="\n")
    return [f"created {folder}/index.md (fill in the About/Scope text)"]


# ---- 2. mkdocs.yml nav --------------------------------------------------------------------------
def sync_nav(folder, title, check):
    text, crlf = read(CONFIG)
    if re.search(rf"^\s*-\s+(?:[^:\n]+:\s+)?{re.escape(folder)}/", text, re.M):
        return []
    entries = guide_pages(folder)
    if not entries:
        return []
    block = f"  - {yaml_label(title)}:\n" + "".join(f"      - {yaml_label(l)}: {p}\n" for l, p in entries)
    if not text.endswith("\n"):
        text += "\n"
    # nav is the last top-level key; append the section at the end of the nav block
    lines = text.split("\n")
    nav_at = next(i for i, l in enumerate(lines) if l.startswith("nav:"))
    end = len(lines)
    for i in range(nav_at + 1, len(lines)):
        if lines[i].strip() and not lines[i][0].isspace():
            end = i
            break
    while end > nav_at + 1 and not lines[end - 1].strip():
        end -= 1
    lines[end:end] = block.rstrip("\n").split("\n")
    if not check:
        write(CONFIG, "\n".join(lines), crlf)
    return [f"mkdocs.yml: added nav section '{title}' ({len(entries)} pages)"]


# ---- 3. home page card --------------------------------------------------------------------------
def build_card(folder, title):
    n = len(scenario_pages(folder))
    stats = f'<div class="cpoc-stats"><span><strong>{n}</strong> scenarios</span></div>\n\n' if n else ""
    return f'''<div class="cpoc-card" markdown>
<span class="cpoc-tag">{DEFAULT_TAG}</span>

## {title}

<p class="cpoc-desc">{about_text(folder, title)}</p>

{stats}<div class="cpoc-btn-row" markdown>
[Start the {title} guide →]({folder}/index.md){{ .cpoc-btn }}
[PDF](#){{ .cpoc-btn .cpoc-btn--outline data-pdf-guide="{folder}" }}
</div>
</div>

'''


def sync_home(folder, title, check):
    text, crlf = read(HOME)
    if f"]({folder}/index.md)" in text or f'data-pdf-guide="{folder}"' in text:
        return []
    marker = text.find("## Disclaimer")
    grid_close = text.rfind("</div>", 0, marker if marker != -1 else len(text))
    if grid_close == -1:
        return [f"docs/index.md: could not find the card grid, card for {folder} NOT added"]
    # grid_close is the grid's closing </div>; insert the new card just before it
    new = text[:grid_close].rstrip(" \n") + "\n\n" + build_card(folder, title) + text[grid_close:]
    if not check:
        write(HOME, new, crlf)
    return [f"docs/index.md: added card for '{title}'"]


# ---- 4. generate_pdfs.py GUIDES -----------------------------------------------------------------
def sync_pdf_script(folder, title, check):
    text, crlf = read(PDF_SCRIPT)
    if re.search(rf'^\s*"{re.escape(folder)}"\s*:\s*\{{', text, re.M):
        return []
    pdf_name = "-".join(w.capitalize() if not w.isupper() else w for w in re.split(r"[-_]+", folder)) + "-CPOC-Guide.pdf"
    subtitle = title.split(" – ", 1)[1] if " – " in title else "Lab guide"
    cover = title.split(" – ", 1)[0]
    entry = f'''    "{folder}": {{
        "nav_label": "{title}",
        "title": "{cover}",
        "subtitle": "{subtitle}",
        "date": "{today()}",
        "author": "{AUTHOR}",
        "email": "{EMAIL}",
        "pdf_name": "{pdf_name}",
    }},
'''
    m = re.search(r"\n\}\n\nCOVER_TEMPLATE", text)
    if not m:
        return [f"generate_pdfs.py: GUIDES dict not found, {folder} NOT added"]
    new = text[:m.start() + 1] + entry + text[m.start() + 1:]
    if not check:
        write(PDF_SCRIPT, new, crlf)
    return [f"generate_pdfs.py: added GUIDES entry '{folder}'"]


# ---- 5. Decap CMS collection --------------------------------------------------------------------
def sync_admin(folder, title, check):
    if not ADMIN.exists():
        return []
    text, crlf = read(ADMIN)
    if f'folder: "docs/{folder}"' in text:
        return []
    name = folder.replace("-", "_")
    block = f'''
  - name: "{name}"
    label: "{title}"
    folder: "docs/{folder}"
    create: true
    slug: "{{{{slug}}}}"
    media_folder: "images"
    public_folder: "images"
    fields:
      - {{ label: "Title", name: "title", widget: "string" }}
      - {{ label: "Body", name: "body", widget: "markdown" }}
'''
    new = text.rstrip("\n") + "\n" + block
    if not check:
        write(ADMIN, new, crlf)
    return [f"admin/config.yml: added CMS collection '{name}'"]


# ---- removal of deleted guides ------------------------------------------------------------------
def registered_folders():
    """Guide folders referenced by any of the registration points, whether or not they still exist."""
    found = set()
    nav = re.compile(r"^\s*-\s+(?:[^:\n]+:\s+)?([\w.-]+)/[^\s]*\.md\s*$", re.M)
    found.update(nav.findall(read(CONFIG)[0]))
    home = read(HOME)[0]
    found.update(re.findall(r'data-pdf-guide="([^"]+)"', home))
    found.update(re.findall(r"\]\(([\w.-]+)/index\.md\)", home))
    found.update(re.findall(r'^    "([^"]+)"\s*:\s*\{', read(PDF_SCRIPT)[0], re.M))
    if ADMIN.exists():
        found.update(re.findall(r'^\s+folder:\s*"docs/([^"/]+)"', read(ADMIN)[0], re.M))
    return found - NOT_GUIDES


def remove_nav(folder, check):
    text, crlf = read(CONFIG)
    lines = text.split("\n")
    entry = re.compile(rf"^\s*-\s+(?:[^:\n]+:\s+)?{re.escape(folder)}/[^\s]*\.md\s*$")
    hits = [i for i, l in enumerate(lines) if entry.match(l)]
    if not hits:
        return []
    depth = lambda l: len(l) - len(l.lstrip())
    start, end = hits[0], hits[-1] + 1
    top = start - 1  # a section header sits one level above its pages: "  - Title:"
    while top >= 0 and (not lines[top].strip() or depth(lines[top]) >= depth(lines[start])):
        top -= 1
    if top >= 0 and lines[top].rstrip().endswith(":"):
        j = end
        while j < len(lines) and lines[j].strip() and depth(lines[j]) > depth(lines[top]):
            j += 1
        start, end = top, j
    del lines[start:end]
    if not check:
        write(CONFIG, "\n".join(lines), crlf)
    return [f"mkdocs.yml: removed nav section for deleted guide '{folder}'"]


def remove_home(folder, check):
    text, crlf = read(HOME)
    m = re.search(rf'\]\({re.escape(folder)}/index\.md\)|data-pdf-guide="{re.escape(folder)}"', text)
    if not m:
        return []
    start = text.rfind('<div class="cpoc-card"', 0, m.start())
    if start == -1:
        return []
    nxt = text.find('<div class="cpoc-card"', m.end())
    if nxt == -1:  # last card: stop before the grid's closing </div>
        marker = text.find("## Disclaimer")
        nxt = text.rfind("</div>", 0, marker if marker != -1 else len(text))
    new = text[:start].rstrip(" \n") + "\n\n" + text[nxt:]
    if not check:
        write(HOME, new, crlf)
    return [f"docs/index.md: removed card for deleted guide '{folder}'"]


def remove_pdf_script(folder, check):
    text, crlf = read(PDF_SCRIPT)
    new, n = re.subn(rf'^    "{re.escape(folder)}"\s*:\s*\{{\n.*?^    \}},\n', "", text,
                     count=1, flags=re.M | re.S)
    if not n:
        return []
    if not check:
        write(PDF_SCRIPT, new, crlf)
    return [f"generate_pdfs.py: removed GUIDES entry '{folder}'"]


def remove_admin(folder, check):
    if not ADMIN.exists():
        return []
    text, crlf = read(ADMIN)
    blocks = re.split(r"(?=^  - name: )", text, flags=re.M)
    kept = [b for b in blocks if not re.search(rf'^\s+folder:\s*"docs/{re.escape(folder)}"', b, re.M)]
    if len(kept) == len(blocks):
        return []
    if not check:
        write(ADMIN, "".join(kept).rstrip("\n") + "\n", crlf)
    return [f"admin/config.yml: removed CMS collection for deleted guide '{folder}'"]


def sync(check=False):
    changes = []
    for folder in guide_folders():
        title = guide_title(folder)
        for step in (sync_index, sync_nav, sync_home, sync_pdf_script, sync_admin):
            changes += step(folder, title, check)
    for folder in sorted(registered_folders() - set(guide_folders())):
        for step in (remove_nav, remove_home, remove_pdf_script, remove_admin):
            changes += step(folder, check)
    return changes


def main():
    check = "--check" in sys.argv
    changes = sync(check)
    for c in changes:
        print(("WOULD " if check else "") + c)
    if not changes:
        print("all guides registered")
    return 1 if check and changes else 0


if __name__ == "__main__":
    sys.exit(main())
