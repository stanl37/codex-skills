---
name: push-to-github
description: Verify, review, stage, commit, and push the current Git repository. Also initialize the current folder and create a private GitHub repository when the user explicitly requests initialization, or after confirming the folder when no Git repository exists. Use when the user explicitly invokes /push-to-github or $push-to-github to commit and push the current repository's work, optionally with initialization.
---

# Push to GitHub

Run this workflow with the underlying Git and GitHub CLI commands. Do not use shell aliases because aliases may be unavailable in non-interactive shells or may collide with installed executables.

Invoking `$push-to-github` or otherwise explicitly requesting this skill constitutes explicit authorization to push the complete reviewed commit payload to the current repository's existing configured push remote and current branch. Do not request a second confirmation solely for that payload or destination. This authorization does not cover a remote that changes during the workflow, adding or replacing a remote in an existing repository, or creating a new remote repository; follow the initialization and remote-creation rules below for those cases.

## Repository resolution and initialization

1. Treat the current working directory as the only candidate project directory. Do not guess or select another directory.
2. If the user explicitly asks to initialize the current folder, run `git init -b main` there before repository verification. This also allows the current folder to become its own repository when it is nested inside another repository.
3. Run `git rev-parse --show-toplevel` from the current working directory.
4. If verification fails and the user did not explicitly request initialization:
   - Run `pwd` and derive the current folder name from the returned path.
   - Ask whether that exact folder is the one the user wants to initialize and push to a new GitHub repository with the same name.
   - State that the GitHub repository will be private unless the user specifies another visibility.
   - Stop and wait for confirmation. Do not initialize, create a remote repository, or choose another folder before confirmation.
5. After confirmation, run `git init -b main` in that folder and continue. Record that this repository was initialized by the workflow and retain the confirmed folder name for remote creation.

## Review and commit

1. Run `git status`. Review the branch, staged changes, unstaged changes, and untracked files shown in the full status output.
2. If there are no changes to commit, stop and report that the working tree is clean.
3. Run `git add -A` to stage all changes.
4. Review `git diff --cached --stat` and `git diff --cached` to understand all staged changes since `HEAD`.
5. If nothing is staged, stop and report that there is nothing to commit.
6. Generate a descriptive but concise commit message of one or two lines. Summarize the purpose of the staged changes and their most important effect; do not invent details not supported by the diff.
7. Run `git commit -m "<commit message>"`.
8. If the commit fails, stop and report the failure. Do not push.

## Remote creation and push

1. Run `git remote -v`.
2. If this workflow initialized the repository and no remote is configured:
   - Create a GitHub repository using the confirmed current folder name.
   - Use private visibility by default. Use public or another visibility only when the user explicitly requests it.
   - Run `gh repo create <repository-name> --private --source=. --remote=origin`, replacing `--private` only when the user requested another visibility.
   - If repository creation fails, report the failure and do not claim the push completed.
3. Determine the current branch with `git branch --show-current`.
4. For a new remote without an upstream branch, run `git push -u origin <current-branch>`. Otherwise run `git push`.
5. Report the commit message, remote repository URL when created, and push result. If the push fails, report the failure without claiming completion.
