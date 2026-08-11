#!/usr/bin/env python3
"""Inspect and mutate Jupyter notebook cells without hand-editing JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import nbformat

from notebook_utils import (
    atomic_write_notebook,
    find_cell,
    load_notebook,
    output_summary,
    source_text,
    truncate_text,
    validate_notebook,
)


def print_json(value: Any) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False))


def add_path_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--path", required=True, help="Path to the notebook.")


def add_cell_selector(parser: argparse.ArgumentParser) -> None:
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--id", dest="cell_id", help="Stable notebook cell ID.")
    selector.add_argument("--index", type=int, help="Zero-based cell index.")


def add_content_arguments(parser: argparse.ArgumentParser) -> None:
    content = parser.add_mutually_exclusive_group(required=True)
    content.add_argument("--content", help="Replacement cell source.")
    content.add_argument("--content-file", help="UTF-8 file containing cell source.")


def read_content(args: argparse.Namespace) -> str:
    if args.content_file:
        return Path(args.content_file).read_text(encoding="utf-8")
    return args.content


def cell_record(
    cell: nbformat.NotebookNode,
    index: int,
    truncate: int = 0,
    include_outputs: bool = False,
) -> dict[str, Any]:
    record = {
        "index": index,
        "id": cell.get("id"),
        "cell_type": cell.cell_type,
        "source": truncate_text(source_text(cell), truncate),
    }

    if cell.cell_type == "code":
        record["execution_count"] = cell.get("execution_count")
        if include_outputs:
            record["outputs"] = cell.get("outputs", [])
        else:
            record["output_summary"] = output_summary(cell)

    return record


def list_cells(args: argparse.Namespace) -> int:
    notebook = load_notebook(args.path)
    records = []

    for index, cell in enumerate(notebook.cells):
        source = source_text(cell)
        if args.cell_type and cell.cell_type != args.cell_type:
            continue
        if args.contains and args.contains.lower() not in source.lower():
            continue

        record = cell_record(cell, index, args.truncate)
        if not args.include_output_summary:
            record.pop("output_summary", None)
        records.append(record)

    print_json({"path": str(Path(args.path).resolve()), "cell_count": len(records), "cells": records})
    return 0


def get_cell(args: argparse.Namespace) -> int:
    notebook = load_notebook(args.path)
    index, cell = find_cell(notebook, args.cell_id, args.index)
    print_json(cell_record(cell, index, include_outputs=args.include_outputs))
    return 0


def update_cell(args: argparse.Namespace) -> int:
    notebook = load_notebook(args.path)
    index, cell = find_cell(notebook, args.cell_id, args.index)
    old_source = source_text(cell)
    new_source = read_content(args)
    result = {
        "operation": "update",
        "path": str(Path(args.path).resolve()),
        "index": index,
        "id": cell.get("id"),
        "cell_type": cell.cell_type,
        "changed": old_source != new_source,
        "dry_run": args.dry_run,
        "old_source": old_source,
        "new_source": new_source,
    }

    if old_source != new_source and not args.dry_run:
        cell.source = new_source
        atomic_write_notebook(notebook, args.path)

    print_json(result)
    return 0


def insertion_index(notebook: nbformat.NotebookNode, args: argparse.Namespace) -> int:
    positions = [
        args.before_id is not None,
        args.after_id is not None,
        args.at_index is not None,
    ]
    if sum(positions) > 1:
        raise ValueError("Specify at most one insertion position.")

    if args.before_id:
        index, _ = find_cell(notebook, cell_id=args.before_id)
        return index
    if args.after_id:
        index, _ = find_cell(notebook, cell_id=args.after_id)
        return index + 1
    if args.at_index is not None:
        if args.at_index < 0 or args.at_index > len(notebook.cells):
            raise IndexError(f"Insertion index out of range: {args.at_index}")
        return args.at_index
    return len(notebook.cells)


def insert_cell(args: argparse.Namespace) -> int:
    notebook = load_notebook(args.path)
    index = insertion_index(notebook, args)
    source = read_content(args)
    cell = (
        nbformat.v4.new_markdown_cell(source)
        if args.cell_type == "markdown"
        else nbformat.v4.new_code_cell(source)
    )

    result = {
        "operation": "insert",
        "path": str(Path(args.path).resolve()),
        "index": index,
        "id": cell.get("id"),
        "cell_type": cell.cell_type,
        "dry_run": args.dry_run,
        "source": source,
    }

    if not args.dry_run:
        notebook.cells.insert(index, cell)
        atomic_write_notebook(notebook, args.path)

    print_json(result)
    return 0


def delete_cell(args: argparse.Namespace) -> int:
    notebook = load_notebook(args.path)
    index, cell = find_cell(notebook, args.cell_id, args.index)
    result = {
        "operation": "delete",
        "path": str(Path(args.path).resolve()),
        "index": index,
        "id": cell.get("id"),
        "cell_type": cell.cell_type,
        "dry_run": args.dry_run,
        "source": source_text(cell),
    }

    if not args.dry_run:
        del notebook.cells[index]
        atomic_write_notebook(notebook, args.path)

    print_json(result)
    return 0


def clear_outputs(args: argparse.Namespace) -> int:
    notebook = load_notebook(args.path)
    changed_cells = []

    for index, cell in enumerate(notebook.cells):
        if cell.cell_type == "code" and (cell.get("outputs") or cell.get("execution_count") is not None):
            changed_cells.append({"index": index, "id": cell.get("id")})
            cell.outputs = []
            cell.execution_count = None

    if changed_cells and not args.dry_run:
        atomic_write_notebook(notebook, args.path)

    print_json({
        "operation": "clear-outputs",
        "path": str(Path(args.path).resolve()),
        "changed_cells": changed_cells,
        "dry_run": args.dry_run,
    })
    return 0


def create_notebook(args: argparse.Namespace) -> int:
    notebook_path = Path(args.path)
    if notebook_path.exists() and not args.force:
        raise FileExistsError(f"Refusing to overwrite existing file: {notebook_path}")

    notebook = nbformat.v4.new_notebook()
    notebook.metadata.kernelspec = {
        "display_name": args.kernel_display_name,
        "language": "python",
        "name": args.kernel_name,
    }
    notebook.metadata.language_info = {"name": "python"}
    notebook.cells = [nbformat.v4.new_markdown_cell(f"# {args.title}")]
    validate_notebook(notebook)

    if not args.dry_run:
        atomic_write_notebook(notebook, notebook_path)

    print_json({
        "operation": "create",
        "path": str(notebook_path.resolve()),
        "title": args.title,
        "kernel_name": args.kernel_name,
        "dry_run": args.dry_run,
    })
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List cells with truncated sources.")
    add_path_argument(list_parser)
    list_parser.add_argument("--cell-type", choices=("markdown", "code"))
    list_parser.add_argument("--contains", help="Case-insensitive source filter.")
    list_parser.add_argument("--truncate", type=int, default=180)
    list_parser.add_argument("--include-output-summary", action="store_true")
    list_parser.set_defaults(handler=list_cells)

    get_parser = subparsers.add_parser("get", help="Read one cell.")
    add_path_argument(get_parser)
    add_cell_selector(get_parser)
    get_parser.add_argument("--include-outputs", action="store_true")
    get_parser.set_defaults(handler=get_cell)

    update_parser = subparsers.add_parser("update", help="Replace one cell's source.")
    add_path_argument(update_parser)
    add_cell_selector(update_parser)
    add_content_arguments(update_parser)
    update_parser.add_argument("--dry-run", action="store_true")
    update_parser.set_defaults(handler=update_cell)

    insert_parser = subparsers.add_parser("insert", help="Insert a new cell.")
    add_path_argument(insert_parser)
    insert_parser.add_argument("--cell-type", choices=("markdown", "code"), required=True)
    add_content_arguments(insert_parser)
    insert_parser.add_argument("--before-id")
    insert_parser.add_argument("--after-id")
    insert_parser.add_argument("--at-index", type=int)
    insert_parser.add_argument("--dry-run", action="store_true")
    insert_parser.set_defaults(handler=insert_cell)

    delete_parser = subparsers.add_parser("delete", help="Delete one cell.")
    add_path_argument(delete_parser)
    add_cell_selector(delete_parser)
    delete_parser.add_argument("--dry-run", action="store_true")
    delete_parser.set_defaults(handler=delete_cell)

    clear_parser = subparsers.add_parser("clear-outputs", help="Clear all code outputs and counts.")
    add_path_argument(clear_parser)
    clear_parser.add_argument("--dry-run", action="store_true")
    clear_parser.set_defaults(handler=clear_outputs)

    create_parser = subparsers.add_parser("create", help="Create a minimal Python notebook.")
    add_path_argument(create_parser)
    create_parser.add_argument("--title", required=True)
    create_parser.add_argument("--kernel-name", default="python3")
    create_parser.add_argument("--kernel-display-name", default="Python 3")
    create_parser.add_argument("--force", action="store_true")
    create_parser.add_argument("--dry-run", action="store_true")
    create_parser.set_defaults(handler=create_notebook)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.handler(args)
    except Exception as error:
        print_json({"ok": False, "error_type": type(error).__name__, "error": str(error)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
