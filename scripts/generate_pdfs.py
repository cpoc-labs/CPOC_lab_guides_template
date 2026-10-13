# Author: Esteban Arguedas (eargueda@cisco.com)
"""
Generate guide PDFs (offline) and the guides.json manifest used by the site's PDF buttons.

Each PDF is styled to resemble the
original Cisco CPOC template: a branded cover page, then content pages with
a repeating "Cisco Global Demo Engineering Customer Proof of Concept" header
and "Cisco (c) 2025. All Rights Reserved." + page number footer.

The PDF is assembled directly from the same markdown files mkdocs builds
the site from (in the order they appear in mkdocs.yml's nav), so there is
nothing to keep in sync by hand - edit the guide, rerun this script.

Usage:
    python scripts/generate_pdfs.py             # build static PDFs (offline use)
    python scripts/generate_pdfs.py --manifest  # write docs/javascripts/guides.json

The site's "PDF" buttons don't link to a prebuilt file: docs/javascripts/
pdf-export.js builds the PDF in the browser on click, from the rendered pages,
using the page list and cover metadata in guides.json (--manifest).

Requires (see requirements.txt): markdown, pymdown-extensions, pyyaml,
pypdf, playwright (with `playwright install chromium` run once).
"""

import html
import json
import re
import sys
from pathlib import Path

import markdown
import yaml
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None
try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    PdfReader = PdfWriter = None

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
MKDOCS_YML = ROOT / "mkdocs.yml"

MD_EXTENSIONS = ["admonition", "attr_list", "md_in_html", "tables", "toc", "pymdownx.details"]

GUIDES = {
    # key = folder name under docs/ = data-pdf-guide value; nav_label must equal the mkdocs.yml section title.
    # sync_scenarios.py adds an entry here automatically for every new guide folder.
    "example-guide": {
        "nav_label": "Example Guide",
        "title": "Example Guide",
        "subtitle": "Template lab guide",
        "date": "1 January 2026",
        "author": "Your Name",
        "email": "you@example.com",
        "pdf_name": "Example-Guide-CPOC-Guide.pdf",
    },
}

COVER_TEMPLATE = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
  body {{
    margin: 0;
    height: 100vh;
    background: #0a1929;
    color: #e8f1f8;
    font-family: Arial, Helvetica, sans-serif;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    box-sizing: border-box;
    padding: 56px 64px;
  }}
  .confidential {{ font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase; color: #7fe7ff; }}
  .titleblock {{ margin-top: auto; margin-bottom: auto; }}
  .titleblock h1 {{ font-size: 34px; margin: 0 0 8px; color: #ffffff; }}
  .titleblock h2 {{ font-size: 20px; margin: 0; color: #7fe7ff; font-weight: 400; }}
  .kicker {{ font-size: 13px; color: #a9c0d3; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 14px; }}
  .meta {{ font-size: 13px; color: #a9c0d3; line-height: 1.8; }}
  .meta strong {{ color: #e8f1f8; }}
  .bar {{ height: 6px; width: 96px; background: #00bceb; margin-bottom: 20px; border-radius: 3px; }}
</style></head>
<body>
  <div class="confidential">Cisco Confidential</div>
  <div class="titleblock">
    <div class="bar"></div>
    <div class="kicker">Cisco Global Demo Engineering &middot; Customer Proof of Concept</div>
    <h1>{title}</h1>
    <h2>{subtitle}</h2>
  </div>
  <div class="meta">
    <div>{date}</div>
    <div><strong>{author}</strong></div>
    <div>{email}</div>
  </div>
</body></html>"""

CONTENT_CSS = """
* { box-sizing: border-box; }
body {
  font-family: Arial, Helvetica, sans-serif;
  color: #1b1f24;
  font-size: 11px;
  line-height: 1.55;
  margin: 0;
}
section.page {
  padding: 0 56px;
  break-before: page;
}
section.page:first-child { break-before: auto; }
h1 { font-size: 20px; color: #0090b8; border-bottom: 2px solid #00bceb; padding-bottom: 6px; margin: 0 0 16px; }
h2 { font-size: 15px; color: #0090b8; margin: 24px 0 10px; }
h3 { font-size: 12.5px; color: #1b1f24; margin: 18px 0 8px; }
p { margin: 0 0 10px; }
ul, ol { margin: 0 0 12px; padding-left: 22px; }
li { margin-bottom: 4px; }
table { border-collapse: collapse; width: 100%; margin: 0 0 16px; font-size: 10px; break-inside: avoid; }
th, td { border: 1px solid #c7d2db; padding: 5px 8px; text-align: left; vertical-align: top; }
th { background: #e6f7fc; color: #04263d; }
img { max-width: 100%; display: block; margin: 10px auto; border: 1px solid #d7dee4; border-radius: 3px; break-inside: avoid; }
.admonition {
  border-left: 4px solid #00bceb;
  background: #e6f7fc;
  padding: 8px 12px;
  margin: 0 0 14px;
  border-radius: 2px;
  break-inside: avoid;
}
.admonition-title { font-weight: 700; color: #0090b8; margin-bottom: 4px; }
a { color: #0090b8; text-decoration: none; }
.toc-list { list-style: none; padding-left: 0; }
.toc-list li { padding: 5px 0; border-bottom: 1px solid #e3e8ec; font-size: 11.5px; }
"""


def load_nav():
    with open(MKDOCS_YML, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config["nav"]


def find_guide_pages(nav, nav_label):
    for entry in nav:
        if isinstance(entry, dict) and nav_label in entry:
            result = []
            for item in entry[nav_label]:
                for label, path in item.items():
                    result.append((label, path))
            return result
    raise ValueError(f"Nav section not found: {nav_label}")


def slugify(relpath):
    return Path(relpath).stem


def strip_cover_duplicate_lines(text):
    """The guide's index.md opens with an H1 title and a CPOC subtitle line
    that both duplicate the generated cover page / repeating PDF header.
    Drop them so they don't appear twice on the first content page."""
    lines = text.splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    while lines and not lines[0].strip():
        lines = lines[1:]
    if lines and lines[0].strip() == "*Cisco Global Demo Engineering Customer Proof of Concept*":
        lines = lines[1:]
    while lines and not lines[0].strip():
        lines = lines[1:]
    return "\n".join(lines)


def strip_pdf_skip_blocks(text):
    """Pages can wrap web-only UI (e.g. the "Convert to PDF" button itself,
    which is meaningless inside the PDF it points to) in
    <!-- pdf:skip:start --> ... <!-- pdf:skip:end --> so it's excluded here."""
    return re.sub(r"<!--\s*pdf:skip:start\s*-->.*?<!--\s*pdf:skip:end\s*-->", "", text, flags=re.DOTALL)


def rewrite_internal_links(text):
    def repl(m):
        label, target = m.group(1), m.group(2)
        if ".md#" in target:
            base = target.split(".md#")[0]
            return f"[{label}](#{Path(base).stem})"
        if target.endswith(".md"):
            return f"[{label}](#{Path(target).stem})"
        return m.group(0)

    return re.sub(r"\[([^\]]+)\]\(([^)]+\.md(?:#[^)]*)?)\)", repl, text)


def build_toc_html(pages):
    items = "".join(
        f'<li><a href="#{slugify(path)}">{html.escape(label)}</a></li>' for label, path in pages
    )
    return f'<section class="page"><h1>Contents</h1><ul class="toc-list">{items}</ul></section>'


def build_content_html(guide_dir, pages):
    sections = []
    for label, path in pages:
        md_path = DOCS / guide_dir / Path(path).name
        text = md_path.read_text(encoding="utf-8")
        if Path(path).name == "index.md":
            text = strip_cover_duplicate_lines(text)
        text = strip_pdf_skip_blocks(text)
        text = rewrite_internal_links(text)
        body_html = markdown.markdown(text, extensions=MD_EXTENSIONS, output_format="html5")
        sections.append(f'<section class="page" id="{slugify(path)}">{body_html}</section>')
    return "".join(sections)


def generate_guide_pdf(guide_dir, meta, nav):
    pages = find_guide_pages(nav, meta["nav_label"])
    out_dir = DOCS / guide_dir
    pdf_path = out_dir / meta["pdf_name"]

    cover_html_path = out_dir / "_print_cover.html"
    content_html_path = out_dir / "_print_content.html"
    cover_pdf_path = out_dir / "_print_cover.pdf"
    content_pdf_path = out_dir / "_print_content.pdf"

    temp_paths = (cover_html_path, content_html_path, cover_pdf_path, content_pdf_path)
    try:
        # Always rebuilt from the current markdown below, so a stale PDF can
        # never linger: there is no cache or "already generated" check to
        # bypass - rerunning this script is the only way to get a PDF at all.
        cover_html_path.write_text(COVER_TEMPLATE.format(**meta), encoding="utf-8")

        toc_html = build_toc_html(pages)
        body_html = build_content_html(guide_dir, pages)
        content_html_path.write_text(
            f"<!DOCTYPE html><html><head><meta charset='utf-8'><style>{CONTENT_CSS}</style></head>"
            f"<body>{toc_html}{body_html}</body></html>",
            encoding="utf-8",
        )

        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                cover_page = browser.new_page()
                cover_page.goto(cover_html_path.resolve().as_uri())
                cover_page.emulate_media(media="print")
                cover_page.pdf(path=str(cover_pdf_path), format="Letter", print_background=True)
                cover_page.close()

                content_page = browser.new_page()
                content_page.goto(content_html_path.resolve().as_uri())
                content_page.emulate_media(media="print")
                content_page.wait_for_timeout(300)
                content_page.pdf(
                    path=str(content_pdf_path),
                    format="Letter",
                    print_background=True,
                    display_header_footer=True,
                    header_template=(
                        '<div style="font-family:Arial,Helvetica,sans-serif; font-size:8px; '
                        'width:100%; text-align:center; color:#7a8894; padding-top:4px;">'
                        "Cisco Global Demo Engineering Customer Proof of Concept</div>"
                    ),
                    footer_template=(
                        '<div style="font-family:Arial,Helvetica,sans-serif; font-size:8px; '
                        'width:100%; text-align:center; color:#7a8894;">'
                        "Cisco &copy; 2025. All Rights Reserved. &nbsp; "
                        '<span class="pageNumber"></span></div>'
                    ),
                    margin={"top": "70px", "bottom": "50px", "left": "0", "right": "0"},
                )
                content_page.close()
            finally:
                browser.close()

        writer = PdfWriter()
        for src in (cover_pdf_path, content_pdf_path):
            reader = PdfReader(str(src))
            for p_ in reader.pages:
                writer.add_page(p_)
        with open(pdf_path, "wb") as f:
            writer.write(f)
    finally:
        # Clean up temp files even if generation failed partway, so a failed
        # run never leaves stale artifacts that could confuse the next one.
        for tmp in temp_paths:
            tmp.unlink(missing_ok=True)

    print(f"Generated {pdf_path} ({pdf_path.stat().st_size // 1024} KB)")


def page_url(relpath):
    """Site URL (relative to the site root) mkdocs serves a source page at."""
    p = Path(relpath)
    return f"{p.parent.as_posix()}/" if p.name == "index.md" else f"{p.with_suffix('').as_posix()}/"


def write_manifest(nav):
    manifest = {}
    for guide_dir, meta in GUIDES.items():
        pages = find_guide_pages(nav, meta["nav_label"])
        manifest[guide_dir] = {
            **{k: meta[k] for k in ("title", "subtitle", "date", "author", "email", "pdf_name")},
            "pages": [{"label": label, "url": page_url(path)} for label, path in pages],
        }
    out = DOCS / "javascripts" / "guides.json"
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {out}")


def main():
    nav = load_nav()
    if "--manifest" in sys.argv:
        write_manifest(nav)
        return
    for guide_dir, meta in GUIDES.items():
        generate_guide_pdf(guide_dir, meta, nav)


if __name__ == "__main__":
    main()
