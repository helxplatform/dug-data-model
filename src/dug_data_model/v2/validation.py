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


