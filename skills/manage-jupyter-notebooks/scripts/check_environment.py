#!/usr/bin/env python3
"""Report whether a Python interpreter can drive notebook operations."""

from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import os
import platform
import shutil
import sys
from pathlib import Path


DRIVER_PACKAGES = ("nbformat", "nbclient")
OPTIONAL_PACKAGES = ("nbconvert", "ipykernel", "jupyter_client")


def package_status(package: str) -> dict[str, object]:
    available = importlib.util.find_spec(package) is not None
    version = None

    if available:
        try:
            version = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            pass

    return {"available": available, "version": version}


def notebook_metadata(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8") as notebook_file:
        notebook = json.load(notebook_file)

    metadata = notebook.get("metadata", {})
    return {
        "path": str(path.resolve()),
        "kernelspec": metadata.get("kernelspec"),
        "language_info": metadata.get("language_info"),
    }


def build_report(args: argparse.Namespace) -> tuple[dict[str, object], list[str]]:
    required_packages = list(DRIVER_PACKAGES)
    if args.require_render:
        required_packages.append("nbconvert")

    packages = {
        package: package_status(package)
        for package in (*DRIVER_PACKAGES, *OPTIONAL_PACKAGES)
    }
    missing = [
        package
        for package in required_packages
        if not packages[package]["available"]
    ]

    report: dict[str, object] = {
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "working_directory": os.getcwd(),
        "packages": packages,
        "required_packages": required_packages,
        "missing_required_packages": missing,
        "ready": not missing,
    }

    if args.notebook:
        report["notebook"] = notebook_metadata(Path(args.notebook))

    if missing:
        if importlib.util.find_spec("pip") is not None:
            install_command = f"{sys.executable} -m pip install {' '.join(missing)}"
        elif shutil.which("uv"):
            install_command = f"uv pip install --python {sys.executable} {' '.join(missing)}"
        else:
            install_command = "No pip or uv installer was detected for this interpreter."
        report["suggested_install_command"] = install_command

    return report, missing


def print_human_report(report: dict[str, object]) -> None:
    print(f"Python executable: {report['python_executable']}")
    print(f"Python version:    {report['python_version']}")
    print(f"Working directory: {report['working_directory']}")
    print("Packages:")

    packages = report["packages"]
    assert isinstance(packages, dict)
    for package, status in packages.items():
        assert isinstance(status, dict)
        state = status["version"] or ("available" if status["available"] else "missing")
        print(f"  {package:<14} {state}")

    notebook = report.get("notebook")
    if isinstance(notebook, dict):
        print(f"Notebook:          {notebook['path']}")
        print(f"Kernel metadata:   {json.dumps(notebook['kernelspec'])}")

    if report["ready"]:
        print("Status:            ready")
    else:
        print("Status:            missing required packages")
        print(f"Install with:      {report['suggested_install_command']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check the driver interpreter and notebook kernel metadata."
    )
    parser.add_argument("--notebook", help="Optional notebook whose metadata should be inspected.")
    parser.add_argument("--require-render", action="store_true", help="Treat nbconvert as required.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report, missing = build_report(args)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_human_report(report)

    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
