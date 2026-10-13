# CPOC Lab Guides — Master Template

A **blank, reusable copy** of the CPOC lab-guide website infrastructure. It contains no lab content, only
the build system, theme, login gate, PDF export, automation scripts and one small **example guide**
(`docs/example-guide/`) that shows the page structure. Use it as the master repo: clone it (or click
**Use this template** on GitHub) every time you need a new, independent lab-guide site.

It is a [MkDocs](https://www.mkdocs.org/) + [Material](https://squidfunk.github.io/mkdocs-material/)
static site, deployed to GitHub Pages by GitHub Actions on every push to `main`. Everything is plain
Markdown: no database, no server.

| Document | Read it for |
|---|---|
| **this README** | Replicating the template, repo layout, writing guides, scripts, troubleshooting |
| [GIT-WORKFLOW.md](GIT-WORKFLOW.md) | Step-by-step Git: clone, edit, add, delete, rename, push, pull request, merge, conflicts, undo |

## Contents

1. [Replicate this template for a new project](#1-replicate-this-template-for-a-new-project)
2. [Customize the template (checklist)](#2-customize-the-template-checklist)
3. [Repository layout](#3-repository-layout)
4. [Writing guides](#4-writing-guides)
5. [Automation scripts and CI](#5-automation-scripts-and-ci)
6. [Run locally](#6-run-locally)
7. [Publish to GitHub Pages](#7-publish-to-github-pages)
8. [Keeping a project up to date with the template](#8-keeping-a-project-up-to-date-with-the-template)
9. [Troubleshooting](#9-troubleshooting)
10. [Known limitations](#10-known-limitations)

---

## 1. Replicate this template for a new project

Pick **one** of the two options. Option A is easier; Option B works for any Git host.

### Option A — GitHub "Use this template" (recommended)

1. Push this repo to GitHub (see [GIT-WORKFLOW.md §1](GIT-WORKFLOW.md#1-one-time-setup)).
2. On GitHub: **Settings → General → check "Template repository"**.
3. For each new project: open the repo and click **Use this template → Create a new repository**.
   The new repo starts with a clean history and no link back to the template.
4. Clone your new repo and continue with [§2](#2-customize-the-template-checklist).

### Option B — Clone and re-point the remote

```bash
# 1. Clone the master template into a folder named after the new project
git clone https://github.com/<ORG>/<TEMPLATE-REPO>.git my-new-lab-guides
cd my-new-lab-guides

# 2. (Optional) start with a clean history instead of the template's history
rm -rf .git                      # PowerShell: Remove-Item -Recurse -Force .git
git init -b main
git add .
git commit -m "Initial commit from CPOC master template"

# 3. Create an EMPTY repo on GitHub (no README/.gitignore), then connect and push
git remote add origin https://github.com/<ORG>/my-new-lab-guides.git
git push -u origin main
```

If you want to **keep** the template history and the ability to pull template improvements, skip step 2
and instead rename the remotes:

```bash
git remote rename origin template
git remote add origin https://github.com/<ORG>/my-new-lab-guides.git
git push -u origin main
```

See [§8](#8-keeping-a-project-up-to-date-with-the-template) for pulling later template changes.

---

## 2. Customize the template (checklist)

Search for the word `TEMPLATE` and for `Your Name` / `you@example.com` / `YOUR-ORG` to find every spot.

| # | File | Change |
|---|---|---|
| 1 | `mkdocs.yml` | `site_name`, `site_description`, `site_author` |
| 2 | `docs/index.md` | Hero title and sentence, footer name/email, one card per guide |
| 3 | `docs/login/index.html` | **Change `VALID_USERNAME` and `VALID_PASSWORD`** (see [limitations](#10-known-limitations)) and the page title |
| 4 | `docs/admin/config.yml` | `repo: YOUR-ORG/YOUR-REPO` and `base_url` (only if you use the Decap CMS; otherwise delete `docs/admin/`) |
| 5 | `scripts/sync_guides.py` | `AUTHOR, EMAIL` — used when a new guide is generated |
| 6 | `scripts/generate_pdfs.py` | `GUIDES` entries: cover title, subtitle, date, author, email |
| 7 | `docs/assets/`, `assets/` | Replace `cisco-logo.png`, `cpoc-logo.png`, `cpoc-logo.ico` with your logos (same file names) |
| 8 | `docs/stylesheets/extra.css` | Brand colours (optional) |
| 9 | `docs/javascripts/pdf-export.js` | Cover/header/footer wording in `drawCover` and `addHeaderFooter` (optional) |
| 10 | `docs/example-guide/` | Rename, rewrite or delete (see [§4.3](#43-add-a-whole-new-guide-or-remove-the-example)) |

---

## 3. Repository layout

```
.
├── mkdocs.yml                      # Site config + NAV (single source of truth for page order)
├── requirements.txt                # Pinned Python dependencies
├── README.md                       # This file
├── GIT-WORKFLOW.md                 # Git instructions: clone/edit/add/delete/push/merge
├── .gitignore                      # site/, caches, generated docs/javascripts/guides.json
├── .github/workflows/deploy.yml    # CI: autofix -> manifest -> mkdocs build --strict -> deploy
├── scripts/                        # Automation (see §5)
├── assets/                         # Repo-level source assets (NOT published)
└── docs/                           # Everything below is published
    ├── index.md                    # Home page (one card per guide)
    ├── assets/                     # Published logos/favicon (+ uploads/ for CMS media)
    ├── stylesheets/extra.css       # Theme colours and .cpoc-* components
    ├── javascripts/
    │   ├── auth-gate.js            # Redirects visitors who are not signed in to /login/
    │   ├── pdf-export.js           # Builds PDFs in the browser on click
    │   └── guides.json             # GENERATED (gitignored)
    ├── login/index.html            # Sign-in page
    ├── admin/                      # Decap CMS (optional web editor)
    └── example-guide/              # EXAMPLE guide — one folder per guide
        ├── index.md                # Overview
        ├── environment.md          # IPs, credentials, equipment
        ├── getting-started.md
        ├── scenario-1.md … scenario-3.md
        ├── whats-next.md
        └── images/                 # Screenshots: scenario-<N>-<NN>.png
```

---

## 4. Writing guides

### 4.1 Page conventions

- One `# H1` per page; sections with `##` / `###`.
- Scenario pages are named `scenario-<N>*.md` and start with `# Scenario N - Title`.
- A guide's `index.md` starts with `# Title`, then the italic subtitle line, then author/version/date
  (the PDF removes the first two because the cover already shows them).
- Screenshots: put them in the guide's `images/` folder, named `scenario-<N>-<NN>.png`, and reference them
  with a **relative** path: `![Screenshot](images/scenario-3-07.png)`. Never use absolute or Windows paths.
- Callouts: `!!! note "Title"` (also `tip`, `warning`, `danger`). Collapsible: `??? note "Title"`.
- Links between pages are relative `.md` links: `[Scenario 2](scenario-2.md)`.
- Web-only blocks (buttons, call-to-action bars) go inside `<!-- pdf:skip:start --> … <!-- pdf:skip:end -->`.

### 4.2 Add, edit, rename, delete a page

| Task | Steps |
|---|---|
| **Edit** | Edit the `.md` file, commit, push. |
| **Add a scenario** | Create `docs/<guide>/scenario-<N>-name.md` (first line `# Scenario N - Title`) and its images, then run `python scripts/sync_scenarios.py`. It adds the page to the nav, the guide's "What you'll do" table and the home-page scenario count. |
| **Add any other page** | Create the file and add one line to the `nav:` in `mkdocs.yml`, in reading order: `- My Page: example-guide/my-page.md`. |
| **Rename / move** | Use `git mv old.md new.md`, then `python scripts/fix_nav.py`, then `mkdocs build --strict` and fix any in-page links it reports. |
| **Delete** | Delete the file (`git rm`), then run `python scripts/sync_scenarios.py` (scenario pages) or remove its nav line by hand; remove links to it; run `mkdocs build --strict`. |

### 4.3 Add a whole new guide (or remove the example)

1. Create `docs/<new-guide>/` (lowercase, hyphens) with at least one `scenario-1-name.md`
   (an `index.md` is optional; it will be generated).
2. Run `python scripts/sync_scenarios.py`. It generates, in the style of the example guide:
   `index.md` (if absent), the `mkdocs.yml` nav section, the home-page card, the `GUIDES` entry in
   `scripts/generate_pdfs.py`, and the CMS collection in `docs/admin/config.yml`.
3. Edit the generated About/Scope text, the card tag/description and the PDF cover subtitle.
4. To **remove the example guide**: delete `docs/example-guide/` and run `python scripts/sync_scenarios.py`;
   it removes the nav section, card, `GUIDES` entry and CMS collection for you.
5. Run the pre-push routine below, then commit.

### 4.4 Pre-push routine

```bash
python scripts/sync_scenarios.py       # nav, indexes, counts, README tables
python scripts/fix_nav.py              # repair renamed pages in nav
python scripts/generate_pdfs.py --manifest
mkdocs build --strict                  # any warning (broken link/image/nav) = failure
```

`mkdocs build --strict` is the single best check; CI runs the same command and refuses to deploy if it fails.

---

## 5. Automation scripts and CI

<!-- auto:guides:start -->
| Guide | Folder | Scenarios | Nav section label in `mkdocs.yml` |
|---|---|---|---|
| Example Guide | `docs/example-guide/` | 3 | `Example Guide` |
<!-- auto:guides:end -->

<!-- auto:scripts:start -->
| Script | What it does |
|---|---|
| `scripts/autofix.py` | Repair the common mistakes that break `mkdocs build --strict`, then sync nav/indexes. |
| `scripts/fix_nav.py` | Auto-fix mkdocs.yml nav entries that point at renamed/moved pages. |
| `scripts/generate_pdfs.py` | Generate guide PDFs (offline) and the guides.json manifest used by the site's PDF buttons. |
| `scripts/sync_guides.py` | Detect new guide folders under docs/ and register them everywhere, in the existing style. |
| `scripts/sync_nav_titles.py` | Keep mkdocs.yml nav labels for scenario pages in sync with each page's H1. |
| `scripts/sync_scenarios.py` | Pick up new scenario pages and update the nav and index files to match. |
| `scripts/update_readme.py` | Regenerate the auto-maintained tables in README.md. |
<!-- auto:scripts:end -->

> The tables above are regenerated by `python scripts/update_readme.py`; do not edit the text between the
> `<!-- auto:... -->` markers by hand.

`.github/workflows/deploy.yml` runs on every push to `main` (and manually via **Actions → Run workflow**):

```
checkout → python 3.x → pip install -r requirements.txt → scripts/autofix.py
        → scripts/generate_pdfs.py --manifest → mkdocs build --strict → upload site/ → deploy to Pages
```

> Fixes that `autofix.py` applies in CI affect only that run's copy of the files. Run the pre-push
> routine locally and **commit the result** so the repository stays correct.

**PDF export:** every `[PDF](#){ .cpoc-btn data-pdf-guide="<guide-folder>" }` link builds that guide's PDF
in the visitor's browser from `docs/javascripts/guides.json` (generated from the nav). Keep the `(#)` target
and make `data-pdf-guide` equal the folder name and the `GUIDES` key. For searchable offline PDFs:
`playwright install chromium && python scripts/generate_pdfs.py`.

**Invariants that break the deploy if violated**

| Requirement | Enforced by |
|---|---|
| Every nav path exists under `docs/` | `fix_nav.py`, `--strict` |
| `GUIDES[...]["nav_label"]` equals the exact nav section title | `generate_pdfs.py --manifest` |
| `GUIDES` key = folder name = `data-pdf-guide` value | `pdf-export.js` ("Unknown guide") |
| Image paths are relative and the files exist | `--strict` |
| `auth-gate.js` and `pdf-export.js` stay in `extra_javascript`; `docs/login/index.html` exists | `mkdocs.yml` |
| `docs/javascripts/guides.json` is generated, never committed | `.gitignore` |

---

## 6. Run locally

```bash
python -m venv .venv
.venv\Scripts\activate              # Windows   (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt

python scripts/generate_pdfs.py --manifest   # once, and after nav changes (needed for PDF buttons)
mkdocs serve                                  # http://127.0.0.1:8000  (live reload)
```

The local login is whatever you set in `docs/login/index.html` (`changeme-user` / `changeme-password`
in the template). Open the site through `mkdocs serve`, not by double-clicking `site/index.html`.

---

## 7. Publish to GitHub Pages

1. Push the repo to GitHub on branch `main`.
2. **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. Push any commit (or **Actions → Deploy MkDocs site to Pages → Run workflow**).
4. The URL appears in the workflow summary: `https://<ORG>.github.io/<REPO>/`.

Private repos need a GitHub plan that supports private Pages; otherwise the published site is public.

---

## 8. Keeping a project up to date with the template

Only if you kept the template's history and named its remote `template` ([§1 Option B](#option-b--clone-and-re-point-the-remote)):

```bash
git fetch template
git switch -c chore/sync-template
git merge template/main --allow-unrelated-histories   # first time only; later: git merge template/main
# resolve conflicts (keep YOUR docs/ content, take the template's scripts/ and workflow), then:
git push -u origin chore/sync-template                 # open a pull request into main
```

Otherwise, copy the changed files in `scripts/`, `.github/`, `docs/javascripts/` and
`docs/stylesheets/` from the template by hand and commit them on a branch.

---

## 9. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| CI: `A reference to 'x.md' is included in the 'nav' … not found` | Page renamed/removed, nav not updated | `python scripts/fix_nav.py`, commit `mkdocs.yml` |
| CI: `Aborted with N warnings in strict mode` | Broken link or missing image | Read the warning and fix the path |
| CI: `Nav section not found: …` | `nav_label` in `GUIDES` differs from the nav section title | Make them identical |
| PDF button shows "PDF failed" | `guides.json` missing/404, page fetch failed, or CDN blocked | Run `generate_pdfs.py --manifest`; check the browser console |
| New page missing from sidebar/PDF | Not in the `mkdocs.yml` nav | Scenario page: run `sync_scenarios.py` (file must be `scenario-<N>…md`); other pages: add by hand |
| Login loop | Browser blocks `localStorage` (private mode) | Allow site storage |
| CMS cannot log in | `base_url` in `docs/admin/config.yml` is still the placeholder | Deploy an OAuth proxy and set it, or delete `docs/admin/` |
| Pages deploy but site is a 404 | Pages source not set to GitHub Actions | [§7](#7-publish-to-github-pages) |

---

## 10. Known limitations

- **The login is a front-end gate, not real security.** The username and password are constants in
  `docs/login/index.html`, and the Markdown/images are public in the repo and on Pages. Treat it as a
  speed bump; for real access control, host behind an authenticating proxy.
- **In-browser PDFs are image-based** (text not selectable) and need internet access to load jsPDF and
  html2canvas from cdnjs. The offline mode produces searchable PDFs.
- `sync_scenarios.py` only recognises files named `scenario-<number>*.md`.
- Screenshot counts, the "Last updated" date and Document history rows are maintained by hand.
- The Decap CMS edits only `title` and `body`; it does not update the nav.
- Material for MkDocs prints a warning about MkDocs 2.0; versions are pinned in `requirements.txt` so
  builds are unaffected until you choose to upgrade.
