"""Validation utilities for the Dug data model.

This module provides functions for validating collections of DugElement objects,
including uniqueness checks.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import DugElement


class DuplicateIdError(ValueError):
    """Raised when duplicate element IDs are found."""

    def __init__(self, duplicate_ids: dict[str, int]):
        self.duplicate_ids = duplicate_ids
        ids_str = ", ".join(f"{id_!r} ({count}x)" for id_, count in duplicate_ids.items())
        super().__init__(f"Duplicate element IDs found: {ids_str}")


class MissingReferenceError(ValueError):
    """Raised when referenced IDs are not found."""

    def __init__(self, missing_ids: set[str], reference_type: str = "parent"):
        self.missing_ids = missing_ids
        self.reference_type = reference_type
        ids_str = ", ".join(sorted(missing_ids))
        super().__init__(f"Missing {reference_type} references: {ids_str}")


def find_duplicate_ids(elements: Iterable[DugElement]) -> dict[str, int]:
    """Find duplicate element IDs.

    Args:
        elements: An iterable of DugElement objects.

    Returns:
        A dict mapping duplicate IDs to their occurrence count.
        Empty dict if no duplicates.
    """
    seen: dict[str, int] = {}
    for elem in elements:
        seen[elem.id] = seen.get(elem.id, 0) + 1
    return {id_: count for id_, count in seen.items() if count > 1}


def validate_unique_ids(elements: Iterable[DugElement]) -> None:
    """Validate that all element IDs are unique.

    Args:
        elements: An iterable of DugElement objects.

    Raises:
        DuplicateIdError: If duplicate IDs are found.
    """
    duplicates = find_duplicate_ids(elements)
    if duplicates:
        raise DuplicateIdError(duplicates)


def find_missing_references(elements: Iterable[DugElement]) -> dict[str, set[str]]:
    """Find IDs that elements refer to but that are not in the collection.

    An element refers to others through `parents` and through any field whose name ends in
    `_list` (e.g. `variable_list`, `section_list`, `document_list`).

    Args:
        elements: An iterable of DugElement objects.

    Returns:
        A dict mapping each referring field name to the set of IDs it refers to that are
        missing. Empty dict if every reference resolves.
    """
    all_elements = list(elements)
    known_ids = {elem.id for elem in all_elements}
    missing: dict[str, set[str]] = {}
    for elem in all_elements:
        for field_name in type(elem).model_fields:
            if field_name != "parents" and not field_name.endswith("_list"):
                continue
            for ref in getattr(elem, field_name):
                if ref not in known_ids:
                    missing.setdefault(field_name, set()).add(ref)
    return missing


def validate_references(elements: Iterable[DugElement]) -> None:
    """Validate that every parent and `*_list` reference points at an element in the collection.

    This is opt-in rather than part of loading, because a producer may legitimately split
    related elements across several files.

    Args:
        elements: An iterable of DugElement objects.

    Raises:
        MissingReferenceError: If any referenced ID is not in the collection.
    """
    missing = find_missing_references(elements)
    if missing:
        all_missing = set().union(*missing.values())
        raise MissingReferenceError(all_missing, reference_type="/".join(sorted(missing)))
