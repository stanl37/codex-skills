# Notebook workflow reference

## Environment and kernel identity

Notebook work involves two Python environments:

1. The **driver interpreter** runs `nbformat`, `nbclient`, and `nbconvert`.
2. The **kernel interpreter** runs the notebook's code.

They may differ. Check the driver with `check_environment.py`. Inspect
`metadata.kernelspec.name` in the notebook and the installed kernelspecs when
imports work in the notebook but fail in the editor, or the reverse.

Prefer a project-local interpreter. Install helpers with that exact interpreter:

```bash
path/to/python -m pip install nbformat nbclient nbconvert
```

If that interpreter is managed by `uv` and does not contain `pip`, use:

```bash
uv pip install --python path/to/python nbformat nbclient nbconvert
```

The kernel environment must also contain the notebook's analytical
dependencies. Registering or changing kernels is external environment state;
do it only when the task requires it.

## Safe cell editing

- List cells first and use IDs instead of positions when possible.
- Read the full source of every cell being changed.
- Use content files for multiline Markdown and code.
- Run mutating commands with `--dry-run` before deletion or replacement.
- Re-read the target immediately before writing if concurrent edits are
  possible.
- Review the resulting diff. Notebook serialization may alter formatting, but
  it must not remove unrelated cells, metadata, or outputs.
- Preserve trailing Markdown spaces and intentional blank lines.

Do not dump unbounded rich outputs into model context. Inspect output types and
small text summaries first, then extract only the figures or tables needed.

## Execution semantics

`notebook_run.py execute` reads the complete notebook, executes it in memory,
validates the executed notebook, and writes the result atomically. A failed
execution leaves the destination unchanged.

Default to a separate output while diagnosing. Use `--in-place` only after the
run is stable or when saved outputs are part of the deliverable.

Set `--cwd` to the project or notebook directory expected by relative paths.
Set a finite timeout. Avoid `--allow-errors` for final validation because error
outputs can otherwise be recorded while the command exits successfully.

Sandbox failures are not analytical failures. Kernel launch can require process
permission, and a notebook that legitimately downloads data can require network
permission. When either is blocked before the analysis runs, rerun the same
scoped command with the required approval.

## Output review

After execution:

1. Run the `errors` command.
2. Confirm execution counts are populated in top-to-bottom order.
3. Inspect key scalar and table outputs for expected ranges and units.
4. Extract and view important figures.
5. Render HTML when layout across cells matters.
6. Confirm the final written interpretation agrees with computed outputs.
7. Re-run after every material code change.

For plots, verify:

- x-axis timing and date alignment;
- y-axis units and transformations;
- legend descriptions and ex-ante/ex-post distinctions;
- layer order and color meaning;
- clipping, empty panels, and unreadable labels.

## Common commands

```bash
# Environment
python scripts/check_environment.py --notebook analysis.ipynb

# Cell map
python scripts/notebook_cells.py list --path analysis.ipynb --truncate 160

# Full source for one cell
python scripts/notebook_cells.py get --path analysis.ipynb --id CELL_ID

# Targeted update
python scripts/notebook_cells.py update \
  --path analysis.ipynb \
  --id CELL_ID \
  --content-file /tmp/source.txt \
  --dry-run

# Schema validation
python scripts/notebook_run.py validate --path analysis.ipynb

# Atomic in-place execution
python scripts/notebook_run.py execute \
  --path analysis.ipynb \
  --in-place \
  --cwd . \
  --timeout 600

# Error scan and figures
python scripts/notebook_run.py errors --path analysis.ipynb
python scripts/notebook_run.py extract-images \
  --path analysis.ipynb \
  --output-dir /tmp/notebook-images
```
