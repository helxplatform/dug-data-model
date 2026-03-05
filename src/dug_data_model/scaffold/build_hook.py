"""Hatch build hook for generating schema files.

This module provides a custom build hook that generates JSON Schema and
Markdown documentation for each data model version during package builds.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


def _find_version_dirs(src_dir: Path) -> list[tuple[str, Path]]:
    """Find all version directories (v1, v2, etc.) in dug_data_model source.

    Args:
        src_dir: The src/dug_data_model directory.

    Returns:
        A list of (version_name, version_path) tuples.
    """
    versions = []

    for item in src_dir.iterdir():
        if item.is_dir() and item.name.startswith("v") and item.name[1:].isdigit():
            # Check if it has an __init__.py
            init_file = item / "__init__.py"
            if init_file.exists():
                versions.append((item.name, item))

    return sorted(versions, key=lambda x: x[0])


def _generate_schemas_for_version(
    version: str,
    version_path: Path,
    output_dir: Path,
    src_dir: Path,
) -> list[str]:
    """Generate JSON Schema and Markdown for a version.

    Args:
        version: The version name (e.g., 'v2').
        version_path: Path to the version's directory.
        output_dir: Directory to write schema files to.
        src_dir: Path to the src directory (for imports).

    Returns:
        List of generated file paths.
    """
    # Add src to path temporarily so we can import the modules
    src_str = str(src_dir)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)

    try:
        import importlib

        # Import the version module
        module_name = f"dug_data_model.{version}"
        try:
            version_module = importlib.import_module(module_name)
        except ImportError:
            return []

        if not hasattr(version_module, "DugElementParsedList"):
            return []

        type_adapter = version_module.DugElementParsedList
        title = f"Dug Data Model {version}"

        # Import utils from scaffold (dynamically since sys.path is modified)
        from dug_data_model.scaffold.utils import (  # type: ignore[import-not-found]
            generate_json_schema,
            generate_markdown_schema,
        )

        generated_files = []

        # Generate JSON Schema
        json_schema = generate_json_schema(type_adapter, title=title)
        json_path = output_dir / f"{version}_schema.json"
        with json_path.open("w") as f:
            json.dump(json_schema, f, indent=2)
        generated_files.append(str(json_path))

        # Generate Markdown documentation
        md_content = generate_markdown_schema(type_adapter, title=title)
        md_path = output_dir / f"{version}_schema.md"
        with md_path.open("w") as f:
            f.write(md_content)
        generated_files.append(str(md_path))

        return generated_files

    finally:
        # Clean up sys.path
        if src_str in sys.path:
            sys.path.remove(src_str)


class CustomBuildHook(BuildHookInterface):  # type: ignore[type-arg]
    """Build hook that generates schema files for all data model versions."""

    PLUGIN_NAME = "custom"

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        """Generate schema files before building.

        Args:
            version: The build version being built.
            build_data: Mutable build configuration data.
        """
        root = Path(self.root)
        src_dir = root / "src"
        package_dir = src_dir / "dug_data_model"
        schema_dir = package_dir / "schemas"
        schema_dir.mkdir(parents=True, exist_ok=True)

        # Find and process all version directories
        version_dirs = _find_version_dirs(package_dir)

        all_generated: list[str] = []
        for ver_name, ver_path in version_dirs:
            generated = _generate_schemas_for_version(ver_name, ver_path, schema_dir, src_dir)
            all_generated.extend(generated)

        if all_generated:
            # Add generated files to the build
            if "force_include" not in build_data:
                build_data["force_include"] = {}

            for file_path in all_generated:
                # Map source path to destination in package
                rel_path = Path(file_path).relative_to(src_dir)
                build_data["force_include"][file_path] = str(rel_path)
