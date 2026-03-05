"""Validation utilities for the Dug data model.

This module provides functions for validating collections of DugElement objects,
including uniqueness checks, hierarchy validation, and reference integrity.
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


def find_missing_parents(elements: Iterable[DugElement]) -> set[str]:
    """Find parent IDs that don't exist in the element collection.

    Args:
        elements: An iterable of DugElement objects.

    Returns:
        A set of missing parent IDs. Empty set if all parents exist.
    """
    elements_list = list(elements)
    all_ids = {elem.id for elem in elements_list}
    missing: set[str] = set()

    for elem in elements_list:
        for parent_id in elem.parents:
            if parent_id not in all_ids:
                missing.add(parent_id)

    return missing


def find_missing_list_references(elements: Iterable[DugElement]) -> set[str]:
    """Find variable_list and section_list IDs that don't exist.

    Checks DugStudy.variable_list, DugStudy.section_list, and
    DugSection.variable_list for references to non-existent elements.

    Args:
        elements: An iterable of DugElement objects.

    Returns:
        A set of missing reference IDs. Empty set if all references exist.
    """
    elements_list = list(elements)
    all_ids = {elem.id for elem in elements_list}
    missing: set[str] = set()

    for elem in elements_list:
        if hasattr(elem, "variable_list"):
            for var_id in elem.variable_list:
                if var_id not in all_ids:
                    missing.add(var_id)

        if hasattr(elem, "section_list"):
            for sec_id in elem.section_list:
                if sec_id not in all_ids:
                    missing.add(sec_id)

    return missing


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


def validate_parent_references(elements: Iterable[DugElement]) -> None:
    """Validate that all parent references point to existing elements.

    Args:
        elements: An iterable of DugElement objects.

    Raises:
        MissingReferenceError: If any parent IDs don't exist.
    """
    missing = find_missing_parents(elements)
    if missing:
        raise MissingReferenceError(missing, "parent")


def validate_list_references(elements: Iterable[DugElement]) -> None:
    """Validate that variable_list and section_list references exist.

    Args:
        elements: An iterable of DugElement objects.

    Raises:
        MissingReferenceError: If any referenced IDs don't exist.
    """
    missing = find_missing_list_references(elements)
    if missing:
        raise MissingReferenceError(missing, "variable/section list")
