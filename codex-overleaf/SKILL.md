---
name: codex-overleaf
description: Safely synchronize an Overleaf project with a local Codex workspace through Overleaf Git. Use when the user asks to clone, pull, download, upload, push, or sync an Overleaf project; provides an Overleaf project URL or ID; or asks to reconcile local LaTeX files with Overleaf.
---

# Codex Overleaf

Synchronize Overleaf and a local workspace with explicit Git operations. Preserve all local and remote work.

## Establish the repository

1. Run `git status --short --branch` before any Git write. If the current directory is not a repository, inspect the directory before cloning.
2. Extract the project ID from `https://www.overleaf.com/project/PROJECT_ID` and use `https://git.overleaf.com/PROJECT_ID` as the Git remote.
3. Clone into the current directory only when it is empty. Otherwise clone into a clearly named new directory or ask the user which directory to use.
4. For an existing repository, inspect `git remote -v` and confirm that the intended Overleaf project is the remote before synchronizing.
5. Let Git request authentication through the user's configured credential flow. Never store credentials in the skill, repository, command line, or tracked files.

## Inspect both sides

Run:

```bash
git status --short --branch
git remote -v
git fetch origin
git rev-list --left-right --count HEAD...@{upstream}
```

If the branch has no upstream, inspect `git branch -vv` and `git ls-remote --heads origin` before choosing a remote branch.

Treat the two counts from `git rev-list` as local-only and remote-only commits. Also inspect uncommitted and untracked files. Do not stash, discard, overwrite, rebase, merge, or force-push to hide a conflict.

## Synchronize

- If the worktree is clean and only the remote is ahead, run `git pull --ff-only`.
- If only the local branch is ahead and the commits belong to the requested work, push the current branch explicitly to its intended Overleaf branch.
- If the user asks to upload uncommitted edits, inspect the diff, stage only in-scope files, commit them, fetch again, confirm that the remote has not advanced, and push explicitly.
- If both sides have commits, or the remote advanced while local edits remain uncommitted, stop and explain the divergence. Ask the user whether to merge or rebase before changing history.
- If the worktree contains unrelated or unclear edits, do not include them in a commit. Ask the user how to handle them.

Use an explicit push such as:

```bash
git push origin HEAD:main
```

Replace `main` only after confirming the Overleaf remote branch. Never use `--force` or `--force-with-lease` unless the user explicitly requests history replacement and approves the exact consequences.

## Keep pushes deliberate

Inspect `.git/hooks/post-commit` when it exists and is executable. If it automatically pushes to Overleaf, disable its executable bit in this repository and use explicit fetch/check/push commands. Do not alter hooks in other repositories.

## Report the result

After synchronization, run:

```bash
git status --short --branch
git log -1 --date=iso --format='%h%n%ad%n%s'
```

Report the branch, whether the worktree is clean, the remote relationship, the latest commit, and any files or conflicts that still need attention.
