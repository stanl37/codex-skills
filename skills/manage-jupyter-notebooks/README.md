# Manage Jupyter Notebooks

A Codex skill and small Python toolkit for safely creating, inspecting, editing,
executing, rendering, and validating Jupyter notebooks.

The skill gives an agent precise cell-level operations without requiring it to
hand-edit notebook JSON. It also separates the Python environment driving the
notebook tools from the kernel environment that runs notebook code—a common
source of confusing import and execution failures.

## What it does

- Lists and reads notebook cells without dumping large outputs.
- Updates, inserts, and deletes cells by stable cell ID or index.
- Supports dry-run previews and atomic notebook writes.
- Checks the driver environment and notebook kernel metadata.
- Executes notebooks from top to bottom with a finite timeout.
- Preserves the destination when execution fails.
- Scans saved outputs for cell errors.
- Extracts embedded PNG figures for visual review.
- Renders notebooks to standalone HTML.
- Validates notebook structure and detects duplicate cell IDs.

## Install for Codex

### Ask Codex to install it

Give Codex this prompt:

```text
Use $skill-installer to install the skill from
https://github.com/stanl37/manage-jupyter-notebooks.
The skill is at the repository root and should be named
manage-jupyter-notebooks.
```

The skill will be available to Codex on the next turn.

### Install manually

Clone the repository into your personal Codex skills directory:

```bash
git clone https://github.com/stanl37/manage-jupyter-notebooks.git \
  "${CODEX_HOME:-$HOME/.codex}/skills/manage-jupyter-notebooks"
```

Start a new Codex task after installation so skill discovery runs again. Invoke
the skill directly with:

```text
$manage-jupyter-notebooks
```

Its description is also written to trigger automatically when a task involves
creating, modifying, executing, or validating an `.ipynb` file.

To require the skill for all notebook work, add this to
`~/.codex/AGENTS.md`:

```md
## Jupyter notebook workflow

Whenever a task involves Jupyter notebooks or `.ipynb` files, always invoke
and follow `$manage-jupyter-notebooks` before inspecting, editing, executing,
or validating the notebook.
```

## Use with other agents or standalone

The repository is useful outside Codex as well:

1. Clone it anywhere on your machine.
2. Point your agent at [`SKILL.md`](SKILL.md) as its notebook workflow.
3. Let the agent call the scripts, or run them directly from a terminal.

The helpers require Python 3.10 or newer. Install the driver dependencies into
the Python environment that will run the scripts:

```bash
python -m pip install nbformat nbclient nbconvert
```

For a `uv`-managed environment without `pip`:

```bash
uv pip install --python path/to/python nbformat nbclient nbconvert
```

The notebook kernel is a separate environment and must contain the packages
imported by the notebook itself.

## Quick start

Set these example paths for your environment:

```bash
PYTHON=path/to/python
SKILL=path/to/manage-jupyter-notebooks
NOTEBOOK=path/to/analysis.ipynb
```

Check the environment and kernel metadata:

```bash
"$PYTHON" "$SKILL/scripts/check_environment.py" \
  --notebook "$NOTEBOOK" \
  --require-render
```

Inspect the notebook:

```bash
"$PYTHON" "$SKILL/scripts/notebook_cells.py" list \
  --path "$NOTEBOOK" \
  --truncate 180
```

Validate and execute to a separate artifact:

```bash
"$PYTHON" "$SKILL/scripts/notebook_run.py" validate \
  --path "$NOTEBOOK"

"$PYTHON" "$SKILL/scripts/notebook_run.py" execute \
  --path "$NOTEBOOK" \
  --output /tmp/analysis.executed.ipynb \
  --cwd path/to/project \
  --timeout 600
```

Review errors and extract figures:

```bash
"$PYTHON" "$SKILL/scripts/notebook_run.py" errors \
  --path /tmp/analysis.executed.ipynb

"$PYTHON" "$SKILL/scripts/notebook_run.py" extract-images \
  --path /tmp/analysis.executed.ipynb \
  --output-dir /tmp/notebook-images
```

Every command and subcommand supports `-h` for its complete arguments.

## Repository structure

```text
manage-jupyter-notebooks/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   └── workflow.md
└── scripts/
    ├── check_environment.py
    ├── notebook_cells.py
    ├── notebook_run.py
    └── notebook_utils.py
```

`SKILL.md` contains the agent workflow. `references/workflow.md` covers
environment diagnosis, safe editing, execution semantics, and output QA. The
scripts provide deterministic notebook operations.

## Safety model

- Notebook mutations are validated and written atomically.
- Source updates preserve unrelated cells, outputs, and metadata.
- Destructive cell operations support `--dry-run`.
- Failed execution does not overwrite the requested destination.
- In-place execution is opt-in.
- Package installation is never performed silently.
