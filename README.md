# Codex Skills

Reusable skills for extending Codex with focused, repeatable workflows.

## Skills

| Skill | Description |
| --- | --- |
| [`codex-overleaf`](codex-overleaf/) | Safely synchronize local LaTeX workspaces with Overleaf Git projects. |
| [`commit`](commit/) | Review and commit Git changes with a Conventional Commits message, without pushing. |
| [`manage-jupyter-notebooks`](manage-jupyter-notebooks/) | Safely inspect, edit, execute, render, and validate Jupyter notebooks. |
| [`push-to-github`](push-to-github/) | Review, commit, initialize when needed, and push Git repositories to GitHub. |

Each top-level skill directory contains a `SKILL.md` file and its supporting resources.

## Install

Ask Codex to install a skill with `$skill-installer` and its GitHub directory URL:

```text
Use $skill-installer to install the skill from
https://github.com/stanl37/codex-skills/tree/main/codex-overleaf
```

```text
Use $skill-installer to install the skill from
https://github.com/stanl37/codex-skills/tree/main/commit
```

```text
Use $skill-installer to install the skill from
https://github.com/stanl37/codex-skills/tree/main/manage-jupyter-notebooks
```

```text
Use $skill-installer to install the skill from
https://github.com/stanl37/codex-skills/tree/main/push-to-github
```

Installed skills become available to Codex on the next turn.

For Claude Code, symlink a skill directory into `~/.claude/skills` so it tracks this repository:

```bash
ln -s "$PWD/commit" ~/.claude/skills/commit
```

## MCP servers

| Server | Description |
| --- | --- |
| [`aa-db`](mcp/aa-db/) | Read-only SQL over the `supabase_readonly` libpq service in `~/.pg_service.conf`. |

`aa-db` is a single-file [uv script](https://docs.astral.sh/uv/guides/scripts/), so uv installs its dependencies on first run. Register it with Claude Code:

```bash
claude mcp add --scope user aa-db -- uv run --script "$PWD/mcp/aa-db/aa_db.py"
```
