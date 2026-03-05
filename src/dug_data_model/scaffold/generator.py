"""Code generator for the Dug data model scaffold.

This module provides functions for generating new data model versions
inside the dug_data_model package by copying the scaffold source files.
"""

from __future__ import annotations

from importlib import resources
from pathlib import Path

# Files to copy from the scaffold package to the generated version
SOURCE_FILES = [
    "base.py",
    "concept.py",
    "types.py",
    "utils.py",
    "validation.py",
]


def get_package_root() -> Path:
    """Get the root directory of the dug_data_model package.

    Returns:
        Path to the dug_data_model package directory.
    """
    scaffold = resources.files("dug_data_model.scaffold")
    # scaffold is dug_data_model/scaffold, so parent is dug_data_model
    return Path(str(scaffold)).parent


def get_source_file(name: str) -> str:
    """Load a source file from the scaffold package.

    Args:
        name: The source filename (e.g., 'base.py').

    Returns:
        The file contents as a string.
    """
    scaffold = resources.files("dug_data_model.scaffold")
    return (scaffold / name).read_text()


def generate_init_file(version: str) -> str:
    """Generate the __init__.py content for a new version.

    Derives the content from the scaffold's __init__.py, replacing the
    scaffold-specific docstring with a version-specific one.

    Args:
        version: The version name (e.g., 'v3').

    Returns:
        The __init__.py content as a string.
    """
    scaffold_init = get_source_file("__init__.py")

    # Find the first import line (end of docstring)
    lines = scaffold_init.splitlines(keepends=True)
    code_start = 0
    for i, line in enumerate(lines):
        if line.startswith("from ") or line.startswith("import "):
            code_start = i
            break

    # Build the new file with a simple version-specific docstring
    docstring = f'"""Dug data model {version}."""\n\n'
    code = "".join(lines[code_start:])

    return docstring + code


def generate_model_version(version: str, output_dir: Path) -> None:
    """Generate a new data model version.

    Copies the scaffold source files to create a new version directory
    inside dug_data_model (e.g., dug_data_model/v3/).

    Args:
        version: The version name (e.g., 'v3').
        output_dir: The directory to create the version in.

    Raises:
        OSError: If the directory cannot be created or files cannot be written.
    """
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Copy source files
    for filename in SOURCE_FILES:
        content = get_source_file(filename)
        (output_dir / filename).write_text(content)

    # Generate __init__.py
    init_content = generate_init_file(version)
    (output_dir / "__init__.py").write_text(init_content)

    # Create empty py.typed marker for PEP 561
    (output_dir / "py.typed").write_text("")
