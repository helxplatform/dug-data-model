"""Utility functions for the Dug data model.

This module provides shared utility functions used across the data model,
including JSON serialization helpers, list processing utilities, and
file I/O helpers for loading and saving elements.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from .base import DugElement

T = TypeVar("T", bound="DugElement")


def complex_handler(obj: Any) -> Any:
    """JSON serialization handler for complex objects.

    This function is intended to be passed as the `default` parameter
    to `json.dumps()`. It handles objects that have a `jsonable()` method
    by calling that method to obtain a serializable representation.

    Args:
        obj: The object to serialize.

    Returns:
        A JSON-serializable representation of the object.

    Raises:
        TypeError: If the object is not JSON serializable and does not
            have a `jsonable()` method.

    Example:
        import json
        from dug_data_model.scaffold import DugConcept, complex_handler

        concept = DugConcept(id="X", name="Y", description="Z")
        json_str = json.dumps(concept.jsonable(), default=complex_handler)
    """
    if hasattr(obj, "jsonable"):
        return obj.jsonable()
    raise TypeError(
        f"Object of type {type(obj).__name__} with value {obj!r} is not JSON serializable"
    )


def dedupe_and_sort(items: list[str]) -> list[str]:
    """Deduplicate and sort a list of strings.

    Args:
        items: A list of strings, possibly with duplicates.

    Returns:
        A sorted list with duplicates removed.

    Example:
        >>> dedupe_and_sort(["b", "a", "b", "c", "a"])
        ['a', 'b', 'c']
    """
    return sorted(set(items))


def serialize_elements(
    elements: Iterable[DugElement],
    path: str | Path,
    indent: int | None = 2,
) -> None:
    """Serialize a collection of elements to a JSON file.

    Args:
        elements: An iterable of DugElement objects to serialize.
        path: The file path to write to.
        indent: JSON indentation level (default: 2). Use None for compact output.

    Example:
        from dug_data_model.scaffold import DugElement, serialize_elements

        elements = [
            DugElement(id="e1", name="Element 1", description="First"),
            DugElement(id="e2", name="Element 2", description="Second"),
        ]
        serialize_elements(elements, "output.json")
    """
    path = Path(path)
    data = [elem.model_dump() for elem in elements]
    with path.open("w") as f:
        json.dump(data, f, indent=indent, default=complex_handler)


def load_elements(
    path: str | Path,
    type_adapter: Any,
) -> list[Any]:
    """Load and validate elements from a JSON file.

    Args:
        path: The file path to read from.
        type_adapter: A Pydantic TypeAdapter for validating the loaded data.
            This should be configured with a discriminated union type to
            correctly deserialize mixed element types.

    Returns:
        A list of validated element objects.

    Raises:
        FileNotFoundError: If the file does not exist.
        pydantic.ValidationError: If the data fails validation.

    Example:
        from pydantic import TypeAdapter
        from typing import Annotated
        from pydantic import Field

        from dug_data_model.scaffold import DugConcept, load_elements

        # For a simple case with just concepts:
        adapter = TypeAdapter(list[DugConcept])
        elements = load_elements("data.json", adapter)

        # For mixed types, define a discriminated union:
        # Indexable = DugConcept | DugVariable | DugStudy
        # DiscriminatedIndexable = Annotated[Indexable, Field(discriminator="type")]
        # adapter = TypeAdapter(list[DiscriminatedIndexable])
        # elements = load_elements("data.json", adapter)
    """
    path = Path(path)
    with path.open("r") as f:
        data = json.load(f)
    return type_adapter.validate_python(data)


def filter_by_type(
    elements: Iterable[T],
    element_type: str,
) -> list[T]:
    """Filter elements by their type field.

    Args:
        elements: An iterable of DugElement objects.
        element_type: The type string to filter by (e.g., "concept", "variable").

    Returns:
        A list of elements matching the specified type.

    Example:
        from dug_data_model.scaffold import filter_by_type

        # Assuming `elements` is a mixed list of concepts, variables, etc.
        concepts = filter_by_type(elements, "concept")
    """
    return [elem for elem in elements if elem.type == element_type]


def generate_json_schema(
    type_adapter: Any,
    title: str | None = None,
) -> dict[str, Any]:
    """Generate a JSON Schema from a Pydantic TypeAdapter.

    This is useful for exporting a version's schema for documentation
    or validation purposes.

    Args:
        type_adapter: A Pydantic TypeAdapter configured with the types to export.
        title: Optional title for the schema root.

    Returns:
        A JSON Schema dictionary.

    Example:
        from pydantic import TypeAdapter
        from dug_data_model.scaffold import generate_json_schema

        # For a list of concepts:
        adapter = TypeAdapter(list[DugConcept])
        schema = generate_json_schema(adapter, title="DugConcepts")

        # For a discriminated union (from a version's types.py):
        # adapter = TypeAdapter(list[DiscriminatedIndexable])
        # schema = generate_json_schema(adapter, title="DugElements v3")
    """
    schema = type_adapter.json_schema()
    if title:
        schema["title"] = title
    return schema


def export_json_schema(
    type_adapter: Any,
    path: str | Path,
    title: str | None = None,
    indent: int | None = 2,
) -> None:
    """Export a JSON Schema to a file.

    Args:
        type_adapter: A Pydantic TypeAdapter configured with the types to export.
        path: The file path to write the schema to.
        title: Optional title for the schema root.
        indent: JSON indentation level (default: 2).

    Example:
        from pydantic import TypeAdapter
        from dug_data_model.scaffold import export_json_schema

        adapter = TypeAdapter(list[DugConcept])
        export_json_schema(adapter, "schema.json", title="DugConcepts")
    """
    schema = generate_json_schema(type_adapter, title=title)
    path = Path(path)
    with path.open("w") as f:
        json.dump(schema, f, indent=indent)


# ---------------------------------------------------------------------------
# Filtering and grouping
# ---------------------------------------------------------------------------

def group_by_type(elements: Iterable[T]) -> dict[str, list[T]]:
    """Group elements by their type field.

    Args:
        elements: An iterable of DugElement objects.

    Returns:
        A dictionary mapping type strings to lists of elements.

    Example:
        from dug_data_model.scaffold import group_by_type

        grouped = group_by_type(elements)
        # {'variable': [...], 'study': [...], 'concept': [...]}
    """
    result: dict[str, list[T]] = {}
    for elem in elements:
        if elem.type not in result:
            result[elem.type] = []
        result[elem.type].append(elem)
    return result


def count_by_type(elements: Iterable[T]) -> dict[str, int]:
    """Count elements by their type field.

    Args:
        elements: An iterable of DugElement objects.

    Returns:
        A dictionary mapping type strings to counts.

    Example:
        >>> count_by_type(elements)
        {'variable': 100, 'study': 5, 'concept': 50}
    """
    result: dict[str, int] = {}
    for elem in elements:
        result[elem.type] = result.get(elem.type, 0) + 1
    return result


def get_element_by_id(
    elements: Iterable[T],
    element_id: str,
) -> T | None:
    """Find an element by its ID.

    Args:
        elements: An iterable of DugElement objects.
        element_id: The ID to search for.

    Returns:
        The matching element, or None if not found.

    Example:
        element = get_element_by_id(elements, "var_123")
    """
    for elem in elements:
        if elem.id == element_id:
            return elem
    return None


def get_all_ids(elements: Iterable[T]) -> set[str]:
    """Get all unique element IDs.

    Args:
        elements: An iterable of DugElement objects.

    Returns:
        A set of all element IDs.
    """
    return {elem.id for elem in elements}


def group_by_id(elements: Iterable[T]) -> dict[str, list[T]]:
    """Group elements by their ID.

    Useful for finding duplicates - any ID with more than one element is a duplicate.

    Args:
        elements: An iterable of DugElement objects.

    Returns:
        A dictionary mapping IDs to lists of elements with that ID.

    Example:
        by_id = group_by_id(elements)
        duplicates = {id_: elems for id_, elems in by_id.items() if len(elems) > 1}
    """
    result: dict[str, list[T]] = {}
    for elem in elements:
        if elem.id not in result:
            result[elem.id] = []
        result[elem.id].append(elem)
    return result


# ---------------------------------------------------------------------------
# Hierarchy utilities
# ---------------------------------------------------------------------------

def build_parent_map(elements: Iterable[T]) -> dict[str, list[T]]:
    """Build a mapping of parent IDs to their child elements.

    Args:
        elements: An iterable of DugElement objects.

    Returns:
        A dictionary mapping parent IDs to lists of child elements.

    Example:
        parent_map = build_parent_map(elements)
        children_of_study_1 = parent_map.get("study_1", [])
    """
    result: dict[str, list[T]] = {}
    for elem in elements:
        for parent_id in elem.parents:
            if parent_id not in result:
                result[parent_id] = []
            result[parent_id].append(elem)
    return result


def get_children(
    elements: Iterable[T],
    parent_id: str,
) -> list[T]:
    """Get all direct children of an element.

    Args:
        elements: An iterable of DugElement objects.
        parent_id: The ID of the parent element.

    Returns:
        A list of elements that have parent_id in their parents list.
    """
    return [elem for elem in elements if parent_id in elem.parents]


# ---------------------------------------------------------------------------
# Batch operations
# ---------------------------------------------------------------------------

def prepare_for_indexing(elements: Iterable[T]) -> None:
    """Prepare elements for indexing by aggregating search terms.

    Calls set_search_terms(), set_optional_terms(), and clean() on each element.
    Modifies elements in place.

    Args:
        elements: An iterable of DugElement objects.
    """
    for elem in elements:
        elem.set_search_terms()
        elem.set_optional_terms()
        elem.clean()


# ---------------------------------------------------------------------------
# Markdown schema documentation
# ---------------------------------------------------------------------------


def _get_type_display(field_schema: dict[str, Any] | bool, defs: dict[str, Any]) -> str:
    """Convert a JSON Schema type definition to a human-readable string.

    Args:
        field_schema: The JSON Schema for a single field, or a boolean.
        defs: The $defs section of the root schema for resolving references.

    Returns:
        A human-readable type string.
    """
    # Handle boolean schemas (true = any, false = none)
    if isinstance(field_schema, bool):
        return "any" if field_schema else "never"

    if "$ref" in field_schema:
        ref: str = field_schema["$ref"]
        # Extract definition name from "#/$defs/Name"
        def_name = ref.split("/")[-1]
        if def_name in defs:
            return _get_type_display(defs[def_name], defs)
        return def_name

    if "anyOf" in field_schema:
        types = []
        for option in field_schema["anyOf"]:
            t = _get_type_display(option, defs)
            if t != "null":
                types.append(t)
        return " | ".join(types) if types else "any"

    if "allOf" in field_schema:
        # Usually means a $ref with additional constraints
        types = [_get_type_display(opt, defs) for opt in field_schema["allOf"]]
        return " & ".join(types)

    if "const" in field_schema:
        return f'"{field_schema["const"]}"'

    if "enum" in field_schema:
        return " | ".join(f'"{v}"' for v in field_schema["enum"])

    json_type: str = field_schema.get("type", "any")

    if json_type == "array":
        items = field_schema.get("items", {})
        item_type = _get_type_display(items, defs)
        return f"list[{item_type}]"

    if json_type == "object":
        # Check for additionalProperties (dict type)
        if "additionalProperties" in field_schema:
            val_type = _get_type_display(field_schema["additionalProperties"], defs)
            return f"dict[str, {val_type}]"
        return "object"

    # Map JSON Schema types to Python-like types
    type_map: dict[str, str] = {
        "string": "str",
        "integer": "int",
        "number": "float",
        "boolean": "bool",
        "null": "null",
    }
    return type_map.get(json_type, json_type)


def _escape_md(text: str) -> str:
    """Escape pipe characters for markdown tables."""
    return text.replace("|", "\\|").replace("\n", " ")


def _extract_model_schemas(schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Extract individual model schemas from a discriminated union schema.

    Args:
        schema: The root JSON Schema (typically for a list of discriminated union).

    Returns:
        A dict mapping model names to their property schemas.
    """
    defs = schema.get("$defs", {})
    models: dict[str, dict[str, Any]] = {}

    for name, definition in defs.items():
        # Skip non-model definitions (e.g., nested types)
        if "properties" not in definition:
            continue
        models[name] = definition

    return models


def generate_markdown_schema(
    type_adapter: Any,
    title: str | None = None,
) -> str:
    """Generate a human-readable Markdown schema from a Pydantic TypeAdapter.

    This creates a Markdown document with tables describing each model type
    in the data model, including field names, types, defaults, and descriptions.

    Args:
        type_adapter: A Pydantic TypeAdapter configured with the types to document.
        title: Optional title for the document.

    Returns:
        A Markdown string documenting the schema.

    Example:
        from pydantic import TypeAdapter
        from dug_data_model.scaffold import generate_markdown_schema

        adapter = TypeAdapter(list[DiscriminatedIndexable])
        md = generate_markdown_schema(adapter, title="Dug Data Model v2")
    """
    schema = type_adapter.json_schema()
    defs = schema.get("$defs", {})
    models = _extract_model_schemas(schema)

    lines: list[str] = []

    # Title
    if title:
        lines.append(f"# {title}")
    else:
        lines.append("# Data Model Schema")
    lines.append("")
    lines.append("This document describes the data model schema in a human-readable format.")
    lines.append("")

    # Table of contents
    lines.append("## Table of Contents")
    lines.append("")
    for model_name in sorted(models.keys()):
        anchor = model_name.lower().replace(" ", "-")
        lines.append(f"- [{model_name}](#{anchor})")
    lines.append("")

    # Generate a section for each model
    for model_name in sorted(models.keys()):
        model_def = models[model_name]
        properties = model_def.get("properties", {})
        required = set(model_def.get("required", []))

        lines.append(f"## {model_name}")
        lines.append("")

        # Model description if available
        if "description" in model_def:
            lines.append(model_def["description"])
            lines.append("")

        # Field table
        lines.append("| Field | Type | Required | Default | Description |")
        lines.append("|-------|------|----------|---------|-------------|")

        for field_name, field_schema in properties.items():
            field_type = _get_type_display(field_schema, defs)
            is_required = field_name in required
            required_str = "Yes" if is_required else "No"

            # Get default value
            if "default" in field_schema:
                default = field_schema["default"]
                if default is None:
                    default_str = "`None`"
                elif isinstance(default, str):
                    default_str = f'`"{default}"`' if default else '`""`'
                elif isinstance(default, (list, dict)):
                    default_str = "`[]`" if isinstance(default, list) else "`{}`"
                else:
                    default_str = f"`{default}`"
            elif is_required:
                default_str = "-"
            else:
                default_str = "-"

            # Get description
            description = field_schema.get("description", "")
            description = _escape_md(description)

            lines.append(
                f"| `{field_name}` | `{field_type}` | {required_str} | {default_str} | {description} |"
            )

        lines.append("")

    return "\n".join(lines)


def export_markdown_schema(
    type_adapter: Any,
    path: str | Path,
    title: str | None = None,
) -> None:
    """Export a Markdown schema to a file.

    Args:
        type_adapter: A Pydantic TypeAdapter configured with the types to document.
        path: The file path to write the schema to.
        title: Optional title for the document.

    Example:
        from pydantic import TypeAdapter
        from dug_data_model.scaffold import export_markdown_schema

        adapter = TypeAdapter(list[DiscriminatedIndexable])
        export_markdown_schema(adapter, "SCHEMA.md", title="Dug Data Model v2")
    """
    md = generate_markdown_schema(type_adapter, title=title)
    path = Path(path)
    with path.open("w") as f:
        f.write(md)
