#!/usr/bin/env python3
"""Validate, execute, render, and inspect Jupyter notebook outputs."""

from __future__ import annotations

import argparse
import base64
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from notebook_utils import (
    atomic_write_notebook,
    load_notebook,
    source_text,
    truncate_text,
    validate_notebook,
)


def print_json(value: Any) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False))


def add_path_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--path", required=True, help="Path to the notebook.")


def validate_command(args: argparse.Namespace) -> int:
    notebook = load_notebook(args.path)
    validate_notebook(notebook)
    print_json({
        "ok": True,
        "path": str(Path(args.path).resolve()),
        "cell_count": len(notebook.cells),
        "nbformat": notebook.nbformat,
        "nbformat_minor": notebook.nbformat_minor,
    })
    return 0


def execution_summary(notebook: Any) -> dict[str, Any]:
    code_cells = [cell for cell in notebook.cells if cell.cell_type == "code"]
    executed = [cell for cell in code_cells if cell.get("execution_count") is not None]
    error_count = sum(
        output.get("output_type") == "error"
        for cell in code_cells
        for output in cell.get("outputs", [])
    )
    return {
        "code_cells": len(code_cells),
        "executed_code_cells": len(executed),
        "error_outputs": error_count,
    }


def execute_command(args: argparse.Namespace) -> int:
    from nbclient import NotebookClient

    notebook_path = Path(args.path).resolve()
    notebook = load_notebook(notebook_path)
    validate_notebook(notebook)

    if args.in_place and args.output:
        raise ValueError("Use either --in-place or --output, not both.")

    output_path = (
        notebook_path
        if args.in_place
        else Path(args.output).resolve()
        if args.output
        else notebook_path.with_name(f"{notebook_path.stem}.executed.ipynb")
    )
    working_directory = Path(args.cwd).resolve() if args.cwd else notebook_path.parent
    if not working_directory.is_dir():
        raise NotADirectoryError(f"Execution working directory not found: {working_directory}")

    kernel_name = args.kernel
    if not kernel_name:
        kernel_name = notebook.get("metadata", {}).get("kernelspec", {}).get("name", "python3")

    client = NotebookClient(
        notebook,
        timeout=args.timeout,
        kernel_name=kernel_name,
        resources={"metadata": {"path": str(working_directory)}},
        allow_errors=args.allow_errors,
        record_timing=True,
    )
    client.execute()
    validate_notebook(notebook)
    atomic_write_notebook(notebook, output_path)

    print_json({
        "ok": True,
        "input": str(notebook_path),
        "output": str(output_path),
        "working_directory": str(working_directory),
        "kernel_name": kernel_name,
        "timeout": args.timeout,
        "allow_errors": args.allow_errors,
        **execution_summary(notebook),
    })
    return 0


def errors_command(args: argparse.Namespace) -> int:
    notebook = load_notebook(args.path)
    errors = []

    for cell_index, cell in enumerate(notebook.cells):
        if cell.cell_type != "code":
            continue
        for output_index, output in enumerate(cell.get("outputs", [])):
            if output.get("output_type") != "error":
                continue
            errors.append({
                "cell_index": cell_index,
                "cell_id": cell.get("id"),
                "output_index": output_index,
                "ename": output.get("ename"),
                "evalue": output.get("evalue"),
                "traceback": output.get("traceback", []),
                "source": truncate_text(source_text(cell), 300),
            })

    print_json({"path": str(Path(args.path).resolve()), "error_count": len(errors), "errors": errors})
    return 1 if errors else 0


def decode_image_data(value: str | list[str]) -> bytes:
    encoded = "".join(value) if isinstance(value, list) else value
    return base64.b64decode(encoded)


def extract_images_command(args: argparse.Namespace) -> int:
    notebook = load_notebook(args.path)
    output_directory = Path(args.output_dir).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    extracted = []

    for cell_index, cell in enumerate(notebook.cells):
        for output_index, output in enumerate(cell.get("outputs", [])):
            data = output.get("data", {})
            if "image/png" not in data:
                continue

            image_path = output_directory / f"cell-{cell_index:03d}-output-{output_index:03d}.png"
            image_path.write_bytes(decode_image_data(data["image/png"]))
            extracted.append({
                "cell_index": cell_index,
                "cell_id": cell.get("id"),
                "output_index": output_index,
                "path": str(image_path),
            })

    print_json({
        "path": str(Path(args.path).resolve()),
        "output_directory": str(output_directory),
        "image_count": len(extracted),
        "images": extracted,
    })
    return 0


def atomic_write_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(text)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        os.replace(temporary_path, path)
    finally:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()


def render_html_command(args: argparse.Namespace) -> int:
    from nbconvert import HTMLExporter

    notebook = load_notebook(args.path)
    validate_notebook(notebook)
    exporter = HTMLExporter()
    exporter.exclude_input_prompt = True
    exporter.exclude_output_prompt = True
    body, _ = exporter.from_notebook_node(notebook)
    output_path = Path(args.output).resolve()
    atomic_write_text(body, output_path)

    print_json({
        "ok": True,
        "path": str(Path(args.path).resolve()),
        "output": str(output_path),
        "bytes": output_path.stat().st_size,
    })
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate notebook schema and cell IDs.")
    add_path_argument(validate_parser)
    validate_parser.set_defaults(handler=validate_command)

    execute_parser = subparsers.add_parser("execute", help="Execute a notebook atomically.")
    add_path_argument(execute_parser)
    execute_parser.add_argument("--output", help="Executed notebook destination.")
    execute_parser.add_argument("--in-place", action="store_true")
    execute_parser.add_argument("--kernel", help="Kernel name; defaults to notebook metadata.")
    execute_parser.add_argument("--cwd", help="Kernel working directory; defaults to notebook directory.")
    execute_parser.add_argument("--timeout", type=int, default=600)
    execute_parser.add_argument("--allow-errors", action="store_true")
    execute_parser.set_defaults(handler=execute_command)

    errors_parser = subparsers.add_parser("errors", help="List recorded error outputs.")
    add_path_argument(errors_parser)
    errors_parser.set_defaults(handler=errors_command)

    images_parser = subparsers.add_parser("extract-images", help="Extract embedded PNG outputs.")
    add_path_argument(images_parser)
    images_parser.add_argument("--output-dir", required=True)
    images_parser.set_defaults(handler=extract_images_command)

    html_parser = subparsers.add_parser("render-html", help="Render a notebook to standalone HTML.")
    add_path_argument(html_parser)
    html_parser.add_argument("--output", required=True)
    html_parser.set_defaults(handler=render_html_command)

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
