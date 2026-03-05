"""CLI implementation for the Dug data model scaffold.

This module provides the command-line interface for bootstrapping new
data model versions inside the dug_data_model package.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

from .generator import generate_model_version, get_package_root


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the scaffold CLI."""
    parser = argparse.ArgumentParser(
        prog="python -m dug_data_model.scaffold",
        description="Dug data model scaffold utilities.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # 'new' command
    new_parser = subparsers.add_parser(
        "new",
        help="Create a new data model version",
        description="Generate a new data model version (e.g., v3) inside dug_data_model.",
    )
    new_parser.add_argument(
        "version",
        help="Version name (e.g., 'v3')",
    )
    new_parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Overwrite existing files without prompting",
    )

    # 'schema' command
    schema_parser = subparsers.add_parser(
        "schema",
        help="Export schema for a data model version",
        description="Generate JSON Schema or Markdown documentation from a data model version's DugElementParsedList.",
    )
    schema_parser.add_argument(
        "version",
        help="Version to export schema for (e.g., 'v2')",
    )
    schema_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Output file path (default: stdout)",
    )
    schema_parser.add_argument(
        "--format",
        "-f",
        choices=["json", "markdown"],
        default="json",
        help="Output format: 'json' for JSON Schema, 'markdown' for human-readable tables (default: json)",
    )
    schema_parser.add_argument(
        "--title",
        "-t",
        type=str,
        default=None,
        help="Title for the schema (default: 'Dug Data Model <version>')",
    )

    return parser


def cmd_new(args: argparse.Namespace) -> int:
    """Handle the 'new' command."""
    version = args.version
    force = args.force

    # Validate version name (must be valid Python identifier, typically v1, v2, v3, etc.)
    if not version.isidentifier():
        print(f"Error: '{version}' is not a valid Python identifier", file=sys.stderr)
        return 1

    # Get the dug_data_model package root
    package_root = get_package_root()
    output_dir = package_root / version

    # Check if version directory already exists
    if output_dir.exists() and not force:
        if any(output_dir.iterdir()):
            print(
                f"Error: Version directory '{output_dir}' already exists and is not empty.",
                file=sys.stderr,
            )
            print("Use --force to overwrite existing files.", file=sys.stderr)
            return 1

    try:
        generate_model_version(version=version, output_dir=output_dir)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Successfully created data model version: {output_dir}")
    print()
    print("Next steps:")
    print(f"  1. Add your element subclasses in {output_dir}/ (e.g., variable.py, study.py)")
    print(f"  2. Define your Indexable union in {output_dir}/types.py")
    print(f"  3. Export your classes from {output_dir}/__init__.py")

    return 0


def cmd_schema(args: argparse.Namespace) -> int:
    """Handle the 'schema' command."""
    version = args.version
    output = args.output
    fmt = args.format
    title = args.title or f"Dug Data Model {version}"

    # Try to import the version module
    module_name = f"dug_data_model.{version}"
    try:
        version_module = importlib.import_module(module_name)
    except ImportError as e:
        print(f"Error: Could not import version '{version}': {e}", file=sys.stderr)
        print(f"Make sure dug_data_model.{version} exists and has a DugElementParsedList.", file=sys.stderr)
        return 1

    # Get DugElementParsedList from the module
    if not hasattr(version_module, "DugElementParsedList"):
        print(
            f"Error: {module_name} does not export 'DugElementParsedList'.",
            file=sys.stderr,
        )
        print("The version must define a DugElementParsedList TypeAdapter.", file=sys.stderr)
        return 1

    type_adapter = version_module.DugElementParsedList

    from .utils import generate_json_schema, generate_markdown_schema

    # Generate output based on format
    if fmt == "json":
        schema = generate_json_schema(type_adapter, title=title)
        content = json.dumps(schema, indent=2)
    else:  # markdown
        content = generate_markdown_schema(type_adapter, title=title)

    # Write to file or stdout
    if output:
        with output.open("w") as f:
            f.write(content)
        print(f"Schema written to: {output}")
    else:
        print(content)

    return 0


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the scaffold CLI."""
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.command == "new":
        return cmd_new(args)
    elif args.command == "schema":
        return cmd_schema(args)

    # Should not reach here due to required=True on subparsers
    parser.print_help()
    return 1
