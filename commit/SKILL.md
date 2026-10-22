---
name: commit
description: Review, stage, and commit the current Git repository's changes with a Conventional Commits message, without pushing. Use when the user explicitly invokes /commit or $commit, or asks to commit the current work locally without pushing it.
---

# Commit

Run this workflow with the underlying Git commands. Do not use shell aliases because aliases may be unavailable in non-interactive shells or may collide with installed executables.

Invoking `$commit` or otherwise explicitly requesting this skill constitutes explicit authorization to create one new local commit on the current branch. It does not authorize pushing, amending, rebasing, switching branches, or adding, changing, or creating remotes. Never push as part of this workflow; use `push-to-github` when the user wants the commit pushed.

## Repository resolution

1. Treat the current working directory as the only candidate project directory. Do not guess or select another directory.
2. Run `git rev-parse --show-toplevel` from the current working directory.
3. If verification fails, stop and report that the current folder is not a Git repository. Do not initialize one.

## Review and commit

1. Run `git status`. Review the branch, staged changes, unstaged changes, and untracked files shown in the full status output.
2. If there are no changes to commit, stop and report that the working tree is clean.
3. If changes are already staged, commit only those and leave everything else as it is. Otherwise run `git add -A` to stage all changes.
4. Review `git diff --cached --stat` and `git diff --cached` to understand all staged changes since `HEAD`.
5. If nothing is staged, stop and report that there is nothing to commit.
6. Generate a concise commit message using the naming convention below. Summarize the purpose and most important effect of the staged changes; do not invent details not supported by the diff.
7. Run `git commit -m "<commit message>"`.
8. If the commit fails, for example because a hook rejects it, stop and report the failure. Do not retry with `--no-verify`.
9. Report the short commit hash, the commit message, any changes left unstaged, and that nothing was pushed.

## Commit naming

Follow [AA's GitHub Naming Conventions](https://www.notion.so/84578c5dd8d84ab0bccdcbd61ff0dc15): use Conventional Commits where possible.

- Format the title as `<type>(<scope>): <summary>`. The scope is optional; use the component affected when it adds useful context.
- Use `feat` for a new feature and `fix` for a bug correction. Use `refactor`, `docs`, `test`, `build`, `ci`, `chore`, `style`, or `perf` when one of those more accurately describes the change.
- For a breaking change, append `!` after the type or scope and explain the incompatibility.
- Describe the concrete change in a short, active summary. Add a brief body, separated by a blank line, when the reason or important effect needs explanation.

Examples:

```text
feat(gdp_pdf): add an agentic judge
docs(push-to-github): adopt AA commit naming conventions
```

AA's published guidance primarily concerns the final merge commit, which uses the PR title. This workflow also uses the same naming style for new local commits; it does not require every intermediate commit in an existing branch to be renamed.
