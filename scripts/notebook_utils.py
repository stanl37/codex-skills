"""Shared notebook loading, validation, inspection, and atomic-write helpers."""

from __future__ import annotations

import os
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

import nbformat


def load_notebook(path: str | Path) -> nbformat.NotebookNode:
    notebook_path = Path(path)
    if not notebook_path.is_file():
        raise FileNotFoundError(f"Notebook not found: {notebook_path}")

    with notebook_path.open(encoding="utf-8") as notebook_file:
        return nbformat.read(notebook_file, as_version=4)


def validate_notebook(notebook: nbformat.NotebookNode) -> None:
    nbformat.validate(notebook)
    ids = [cell.get("id") for cell in notebook.cells if cell.get("id")]
    duplicates = sorted(cell_id for cell_id, count in Counter(ids).items() if count > 1)

    if duplicates:
        raise ValueError(f"Duplicate cell IDs: {', '.join(duplicates)}")


def atomic_write_notebook(notebook: nbformat.NotebookNode, path: str | Path) -> None:
    notebook_path = Path(path)
    notebook_path.parent.mkdir(parents=True, exist_ok=True)
    validate_notebook(notebook)

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=notebook_path.parent,
            prefix=f".{notebook_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            nbformat.write(notebook, temporary_file)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        os.replace(temporary_path, notebook_path)
    finally:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()


def source_text(cell: nbformat.NotebookNode) -> str:
    source = cell.get("source", "")
    return "".join(source) if isinstance(source, list) else source


def truncate_text(text: str, limit: int) -> str:
    if limit <= 0 or len(text) <= limit:
        return text
    return f"{text[:limit]}…"


def find_cell(
    notebook: nbformat.NotebookNode,
    cell_id: str | None = None,
    index: int | None = None,
) -> tuple[int, nbformat.NotebookNode]:
    if (cell_id is None) == (index is None):
        raise ValueError("Specify exactly one of cell ID or index.")

    if cell_id is not None:
        for cell_index, cell in enumerate(notebook.cells):
            if cell.get("id") == cell_id:
                return cell_index, cell
        raise KeyError(f"Cell ID not found: {cell_id}")

    assert index is not None
    if index < 0 or index >= len(notebook.cells):
        raise IndexError(f"Cell index out of range: {index}")
    return index, notebook.cells[index]


def output_summary(cell: nbformat.NotebookNode) -> dict[str, Any]:
    outputs = cell.get("outputs", [])
    output_types: dict[str, int] = {}
    mime_types: dict[str, int] = {}
    errors: list[str] = []

    for output in outputs:
        output_type = output.get("output_type", "unknown")
        output_types[output_type] = output_types.get(output_type, 0) + 1

        if output_type in {"display_data", "execute_result"}:
            for mime_type in output.get("data", {}):
                mime_types[mime_type] = mime_types.get(mime_type, 0) + 1
        elif output_type == "error":
            errors.append(f"{output.get('ename', 'Error')}: {output.get('evalue', '')}")

    return {
        "execution_count": cell.get("execution_count"),
        "output_count": len(outputs),
        "output_types": output_types,
        "mime_types": mime_types,
        "errors": errors,
    }
