---
name: manage-jupyter-notebooks
description: Create, inspect, edit, execute, render, and validate Jupyter notebooks (`.ipynb`) with precise cell-level control and reliable output capture. Use when Codex must build or modify notebooks, preserve existing cells while making targeted edits, run notebooks top-to-bottom in a project environment, diagnose kernel or dependency mismatches, inspect execution errors, or verify generated tables and figures.
---

# Manage Jupyter Notebooks

Use the bundled scripts instead of hand-editing notebook JSON. Resolve every
script path relative to this `SKILL.md`.

## Core workflow

1. Inspect the project instructions, notebook, active Python environment, and
   kernel metadata.
2. Read only the cells needed for the task. Identify cells by stable cell ID
   whenever IDs exist.
3. Make targeted edits. Preview destructive cell operations with `--dry-run`.
4. Validate the notebook schema before execution.
5. Execute top-to-bottom in memory. Write results only after successful
   execution unless the user explicitly requests `--allow-errors`.
6. Scan recorded outputs for errors and inspect material tables and figures.
7. Review the notebook diff and preserve unrelated user changes.

Never silently install packages into a global interpreter. Prefer the
project-local environment, such as `.venv/bin/python`, and install missing
helpers there only when installation is authorized.

## Check the environment

Run:

```bash
<python> scripts/check_environment.py --notebook path/to/notebook.ipynb
```

The driver environment needs `nbformat` and `nbclient`. Rendering additionally
needs `nbconvert`. The notebook kernel separately needs every package imported
by notebook cells.

If the environment is incomplete, use the exact interpreter reported by the
check:

```bash
<python> -m pip install nbformat nbclient nbconvert
```

For a `uv`-managed environment without `pip`, use the diagnostic's suggested
`uv pip install --python <python> ...` command instead.

Do not assume the editor, linter, shell, and notebook kernel use the same
interpreter. Read `references/workflow.md` when resolving environment or kernel
mismatches.

## Inspect and edit cells

List cells without dumping large outputs:

```bash
<python> scripts/notebook_cells.py list \
  --path path/to/notebook.ipynb \
  --truncate 180
```

Read one cell:

```bash
<python> scripts/notebook_cells.py get \
  --path path/to/notebook.ipynb \
  --id CELL_ID
```

Prefer a content file for multiline updates:

```bash
<python> scripts/notebook_cells.py update \
  --path path/to/notebook.ipynb \
  --id CELL_ID \
  --content-file /tmp/replacement.md \
  --dry-run
```

Repeat without `--dry-run` after reviewing the preview. Use `insert`, `delete`,
`clear-outputs`, or `create` for the corresponding operations. Run each
subcommand with `-h` for its complete arguments.

Re-read the target cell immediately before mutation when the user may also be
editing the notebook. Preserve Markdown trailing spaces because they can encode
line breaks.

## Validate and execute

Validate:

```bash
<python> scripts/notebook_run.py validate --path path/to/notebook.ipynb
```

Execute to a separate artifact by default:

```bash
<python> scripts/notebook_run.py execute \
  --path path/to/notebook.ipynb \
  --output /tmp/notebook.executed.ipynb \
  --cwd path/to/project \
  --timeout 600
```

Use `--in-place` only when the task requires saved outputs in the source
notebook. In-place execution is atomic: a failed run does not overwrite the
notebook.

When a sandboxed run fails before cell execution because kernel launch or
network access is restricted, rerun the same scoped execution with the required
approval. Do not replace the data source merely to avoid an approval.

## Review outputs

Scan errors:

```bash
<python> scripts/notebook_run.py errors --path path/to/notebook.ipynb
```

Extract PNG outputs for visual inspection:

```bash
<python> scripts/notebook_run.py extract-images \
  --path path/to/notebook.ipynb \
  --output-dir /tmp/notebook-images
```

Render HTML when page-level review helps:

```bash
<python> scripts/notebook_run.py render-html \
  --path path/to/notebook.ipynb \
  --output /tmp/notebook.html
```

Inspect every material figure, not only whether an image output exists. Check
labels, units, legends, clipping, ordering, colors, and whether the plotted
data match the stated timing.

## Quality rules

- Keep notebooks runnable from top to bottom in a fresh kernel.
- Keep imports and configuration near the top.
- Use short Markdown cells to explain purpose, equations, timing, units, and
  interpretation.
- Keep code cells focused on one analytical step.
- Avoid hidden state, unexplained constants, and stale outputs.
- Use deterministic seeds when outputs are used for comparison.
- Do not clear or replace useful outputs unless the task requires it.
- Do not claim execution succeeded without checking the executed artifact.

Read `references/workflow.md` for environment diagnostics, safe editing
details, execution semantics, and the final QA checklist.
