"""Validation utilities for the Dug data model.

This module provides functions for validating collections of DugElement objects,
including uniqueness checks.
"""

from __future__ import annotations

from collections.abc import Iterable
from functools import cache
from typing import TYPE_CHECKING

from .base import References
from .utils import get_all_ids

if TYPE_CHECKING:
    from .base import DugElement


class DuplicateIdError(ValueError):
    """Raised when duplicate element IDs are found."""

    def __init__(self, duplicate_ids: dict[str, int]):
        self.duplicate_ids = duplicate_ids
        ids_str = ", ".join(f"{id_!r} ({count}x)" for id_, count in duplicate_ids.items())
        super().__init__(f"Duplicate element IDs found: {ids_str}")


class MissingReferenceError(ValueError):
    """Raised when referenced IDs are not found.

    `missing_ids` holds every missing ID; `by_field` says which field each one came from, as
    `find_missing_references()` returns it, and the message lists them field by field.
    """

    def __init__(
        self,
        missing_ids: set[str],
        reference_type: str = "parent",
        by_field: dict[str, set[str]] | None = None,
    ):
        self.missing_ids = missing_ids
        self.reference_type = reference_type
        self.by_field = by_field if by_field is not None else {reference_type: missing_ids}
        super().__init__(
            "; ".join(
                f"Missing {field} references: {', '.join(sorted(ids))}"
                for field, ids in sorted(self.by_field.items())
            )
        )


class InconsistentReferenceError(ValueError):
    """Raised when references resolve but point at the wrong kind of element.

    `problems` holds one sentence per problem, as `find_inconsistent_references()` returns them.
    """

    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("Inconsistent references: " + "; ".join(problems))


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


@cache
def _reference_fields(cls: type[DugElement]) -> tuple[tuple[str, References], ...]:
    """Return the name and `References` marker of each of *cls*'s fields that hold IDs."""
    return tuple(
        (name, marker)
        for name, field in cls.model_fields.items()
        for marker in field.metadata
        if isinstance(marker, References)
    )


def find_missing_references(elements: Iterable[DugElement]) -> dict[str, set[str]]:
    """Find IDs that elements refer to but that are not in the collection.

    An element refers to others through the fields marked with `References`: `parents`, and
    in v2 `variable_list`, `section_list` and `studies`. Nothing lists its children: a study
    does not list its resources, nor a resource its documents, nor a document its content.

    Args:
        elements: An iterable of DugElement objects.

    Returns:
        A dict mapping each referring field name to the set of IDs it refers to that are
        missing. Empty dict if every reference resolves.
    """
    all_elements = list(elements)
    known_ids = get_all_ids(all_elements)
    missing: dict[str, set[str]] = {}
    for elem in all_elements:
        for field_name, _ in _reference_fields(type(elem)):
            for ref in getattr(elem, field_name):
                if ref not in known_ids:
                    missing.setdefault(field_name, set()).add(ref)
    return missing


def find_inconsistent_references(elements: Iterable[DugElement]) -> list[str]:
    """Find references that resolve but point at the wrong kind of element.

    Each referenced element must have the `type` that its field's `References` marker
    declares: `element_type`, or for `parents` the element's `parent_type` (not checked when
    that is empty). IDs that do not resolve are left to `find_missing_references()`.

    An earlier version also checked that a `children` list and its members' `parents` agreed
    in both directions. Those lists are gone (a child names its parent; nothing lists its
    children), so there is nothing left to disagree.

    Args:
        elements: An iterable of DugElement objects.

    Returns:
        One sentence per problem, naming the element at fault. Empty list if none.
    """
    by_id = {elem.id: elem for elem in elements}
    problems: list[str] = []
    for elem in by_id.values():
        for field_name, marker in _reference_fields(type(elem)):
            expected = marker.element_type or (getattr(elem, marker.type_from) if marker.type_from else "")
            if not expected:
                continue
            for ref in getattr(elem, field_name):
                target = by_id.get(ref)
                if target is not None and target.type != expected:
                    problems.append(
                        f"{elem.id}: {field_name} names {ref}, a {target.type or 'untyped element'}, "
                        f"not a {expected}"
                    )
    return problems


def validate_references(elements: Iterable[DugElement]) -> None:
    """Validate that every `References` field points at the right elements in the collection.

    First that every referenced ID is in the collection, then that each points at the right
    kind of element (see `find_inconsistent_references()`). This is opt-in rather than part of
    loading, because a producer may legitimately split related elements across several files.

    Args:
        elements: An iterable of DugElement objects.

    Raises:
        MissingReferenceError: If any referenced ID is not in the collection.
        InconsistentReferenceError: If a reference points at the wrong type of element.
    """
    all_elements = list(elements)
    missing = find_missing_references(all_elements)
    if missing:
        all_missing = set().union(*missing.values())
        raise MissingReferenceError(
            all_missing, reference_type="/".join(sorted(missing)), by_field=missing
        )
    problems = find_inconsistent_references(all_elements)
    if problems:
        raise InconsistentReferenceError(problems)
