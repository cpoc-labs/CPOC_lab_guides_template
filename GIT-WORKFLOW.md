# Git Workflow — clone, edit, add, delete, push, merge

Everything you need to work on a lab-guide repo made from this template. Commands work in Git Bash,
PowerShell, macOS and Linux unless noted. Replace `<ORG>`, `<REPO>` and branch names with yours.

**The rule of thumb:** never commit straight to `main`. Make a **branch**, push it, open a **pull request**
(PR), get it reviewed, **merge**. Every merge into `main` automatically rebuilds and redeploys the site.

```mermaid
flowchart LR
    A[clone] --> B[git switch -c my-branch]
    B --> C[edit / add / delete files]
    C --> D[mkdocs build --strict]
    D --> E[git add + git commit]
    E --> F[git push -u origin my-branch]
    F --> G[Pull request]
    G --> H[Review + merge to main]
    H --> I[CI deploys the site]
    I --> J[git switch main + git pull]
```

## Contents

1. [One-time setup](#1-one-time-setup)
2. [Clone](#2-clone)
3. [Create a branch](#3-create-a-branch)
4. [Edit, add, rename, delete files](#4-edit-add-rename-delete-files)
5. [Check your work](#5-check-your-work)
6. [Commit](#6-commit)
7. [Push](#7-push)
8. [Pull request and merge](#8-pull-request-and-merge)
9. [Stay in sync (pull / rebase)](#9-stay-in-sync-pull--rebase)
10. [Resolve merge conflicts](#10-resolve-merge-conflicts)
11. [Undo mistakes](#11-undo-mistakes)
12. [Cheat sheet](#12-cheat-sheet)

---

## 1. One-time setup

```bash
git --version                                   # install Git from https://git-scm.com if missing
git config --global user.name  "Your Name"
git config --global user.email "you@example.com"
git config --global init.defaultBranch main
git config --global pull.rebase false           # plain merge on pull (simplest, predictable)
git config --global core.autocrlf true          # Windows only: avoids CRLF/LF noise
```

Authenticate to GitHub with **one** of:

- **HTTPS + browser/credential manager** (default in Git for Windows: the first `git push` opens a sign-in window), or
- **GitHub CLI:** `gh auth login`, or
- **SSH key:** `ssh-keygen -t ed25519 -C "you@example.com"`, add `~/.ssh/id_ed25519.pub` under
  GitHub → Settings → SSH and GPG keys, and clone with the `git@github.com:<ORG>/<REPO>.git` URL.

**Publishing the template itself for the first time** (from the template folder):

```bash
git init -b main                 # skip if the folder is already a repo
git add .
git commit -m "Initial commit: CPOC master template"
git remote add origin https://github.com/<ORG>/<TEMPLATE-REPO>.git    # create the empty repo on GitHub first
git push -u origin main
```

**Recommended repo protection** (GitHub → Settings → Branches → Add rule for `main`): require a pull
request before merging and require the *Deploy MkDocs site to Pages → build* check to pass.

## 2. Clone

```bash
cd ~/Documents/repositories                       # any folder you keep projects in
git clone https://github.com/<ORG>/<REPO>.git
cd <REPO>
git status                                        # should say: On branch main, nothing to commit
```

Clone into a different folder name: `git clone https://github.com/<ORG>/<REPO>.git my-folder`.
Then set up the Python environment once: see README §6.

## 3. Create a branch

Always start from an up-to-date `main`:

```bash
git switch main
git pull
git switch -c docs/scenario-4-backup        # create AND switch to the new branch
```

Branch naming: `docs/<what>` for content, `fix/<what>` for corrections, `chore/<what>` for tooling.
Keep one topic per branch.

## 4. Edit, add, rename, delete files

Work in your editor. Git tracks the changes; nothing is saved to history until you commit.

| Task | Commands |
|---|---|
| **Edit** a page | Edit `docs/<guide>/scenario-2.md` and save. |
| **Add** a page | Create `docs/<guide>/scenario-4-backup.md` (first line `# Scenario 4 - Backup`), then `python scripts/sync_scenarios.py` to register it in the nav/index. |
| **Add** screenshots | Copy files into `docs/<guide>/images/` as `scenario-4-01.png`, `scenario-4-02.png`… and reference with `![Screenshot](images/scenario-4-01.png)`. |
| **Rename / move** | `git mv docs/<guide>/old.md docs/<guide>/new.md` then `python scripts/fix_nav.py` and fix links to it. Always `git mv` (not a manual rename) so history follows the file. |
| **Delete** a page | `git rm docs/<guide>/scenario-4-backup.md` then `python scripts/sync_scenarios.py`; remove links to it and its unused images (`git rm docs/<guide>/images/scenario-4-*.png`). |
| **Delete** a whole guide | `git rm -r docs/<guide>` then `python scripts/sync_scenarios.py` (removes nav, card, PDF entry, CMS collection). |
| **Add** a new guide | See README §4.3. |

Only commit what belongs in the repo: never `site/`, `.venv/`, or `docs/javascripts/guides.json`
(all already in `.gitignore`), and never real customer data or secrets.

## 5. Check your work

```bash
python scripts/sync_scenarios.py
python scripts/fix_nav.py
python scripts/generate_pdfs.py --manifest
mkdocs build --strict            # must finish with no WARNING lines
mkdocs serve                     # preview at http://127.0.0.1:8000
```

## 6. Commit

```bash
git status                       # what changed (red = unstaged, green = staged)
git diff                         # review unstaged changes line by line

git add docs/<guide>/scenario-4-backup.md docs/<guide>/images/ mkdocs.yml    # stage specific files (preferred)
# or stage everything:  git add -A
git status                       # confirm only the intended files are green

git commit -m "Add scenario 4: backup and restore"
```

Good messages are short and in the imperative: "Fix broken image in scenario 2", "Update IP table".
Make several small commits instead of one huge one. Fix the last commit message (not yet pushed):
`git commit --amend -m "new message"`.

## 7. Push

```bash
git push -u origin docs/scenario-4-backup     # first push of this branch (-u links it to the remote)
git push                                       # every later push on the same branch
```

Pushing a branch other than `main` does **not** deploy anything.

## 8. Pull request and merge

### On GitHub (web)

1. After the push, GitHub shows **Compare & pull request**. Click it (or **Pull requests → New pull request**,
   base `main`, compare `docs/scenario-4-backup`).
2. Write a title and a short description (what changed, which scenarios). Assign a reviewer.
3. Wait for the **build** check to turn green. If it is red, open the log, fix locally, commit and `git push`
   again; the PR updates itself.
4. Reviewer approves. Click **Merge pull request** (use **Squash and merge** to keep `main` history tidy).
5. Click **Delete branch**.
6. The merge to `main` triggers the deploy workflow; watch it under the **Actions** tab. When it finishes the
   site is live.

### With the GitHub CLI

```bash
gh pr create --base main --title "Add scenario 4: backup" --body "Adds scenario 4 and 6 screenshots."
gh pr checks                 # watch the build
gh pr merge --squash --delete-branch
```

### Merge locally (only when you own the repo and have no branch protection)

```bash
git switch main
git pull
git merge --no-ff docs/scenario-4-backup
git push
git branch -d docs/scenario-4-backup            # delete local branch
git push origin --delete docs/scenario-4-backup # delete remote branch
```

### After the merge: update your local copy

```bash
git switch main
git pull
git branch -d docs/scenario-4-backup            # if the branch still exists locally
```

## 9. Stay in sync (pull / rebase)

Bring other people's merged work into your branch before opening or merging a PR:

```bash
git fetch origin
git switch docs/scenario-4-backup
git merge origin/main            # simple and safe
# or, for a linear history (only on a branch nobody else uses):
# git rebase origin/main && git push --force-with-lease
```

Refresh `main` any time with `git switch main && git pull`.

## 10. Resolve merge conflicts

A conflict happens when two branches changed the same lines (often `mkdocs.yml` nav, `docs/index.md`
or a guide's `index.md` table).

```bash
git merge origin/main
# CONFLICT (content): Merge conflict in mkdocs.yml
git status                       # lists "both modified" files
```

Open each conflicted file and look for the markers:

```
<<<<<<< HEAD
      - Scenario 4 - Backup: example-guide/scenario-4-backup.md
=======
      - Scenario 4 - Monitoring: example-guide/scenario-4-monitoring.md
>>>>>>> origin/main
```

Keep what is correct (often **both** lines, renumbered), delete the three marker lines, then:

```bash
python scripts/sync_scenarios.py        # re-sync nav/indexes after fixing
mkdocs build --strict                   # verify
git add mkdocs.yml docs/...             # mark as resolved
git commit                              # completes the merge (accept the default message)
git push
```

Abort and start over: `git merge --abort`.

## 11. Undo mistakes

| Situation | Command |
|---|---|
| Discard unsaved edits to one file | `git restore path/to/file.md` |
| Unstage a file (keep the edits) | `git restore --staged path/to/file.md` |
| Undo the last commit, keep the changes | `git reset --soft HEAD~1` |
| Undo a commit that is already pushed/merged | `git revert <commit-sha>` then push (creates a new "undo" commit; safe) |
| Recover a deleted file from the last commit | `git restore --source=HEAD path/to/file.md` |
| Recover a file from an older commit | `git log --oneline -- path/to/file.md` then `git restore --source=<sha> path/to/file.md` |
| Committed to `main` by accident (not pushed) | `git branch docs/my-fix && git reset --hard origin/main && git switch docs/my-fix` |
| Committed a secret | Rotate the secret immediately, then ask a repo admin to purge it from history. Deleting the file in a new commit is **not** enough. |

Avoid `git push --force` and `git reset --hard` unless you understand exactly what they discard; if you must
force-push a branch, use `--force-with-lease` and never on `main`.

## 12. Cheat sheet

```bash
git clone <url>                     # copy a repo
git switch main && git pull         # update main
git switch -c <branch>              # new branch
git status / git diff               # what changed
git add <files>                     # stage
git commit -m "message"             # save a snapshot
git push -u origin <branch>         # publish the branch (first time)
git push                            # publish more commits
git mv old new                      # rename/move a tracked file
git rm <file>                       # delete a tracked file
git merge origin/main               # bring main into your branch
git log --oneline --graph -15       # recent history
git branch -d <branch>              # delete a merged local branch
```
