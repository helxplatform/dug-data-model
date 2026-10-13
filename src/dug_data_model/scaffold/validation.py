"""Validation utilities for the Dug data model.

This module provides functions for validating collections of DugElement objects:
that their IDs are unique, and that the IDs they refer to resolve to the right elements.
"""

from __future__ import annotations

from collections.abc import Iterable
from functools import cache
from typing import TYPE_CHECKING, Literal, get_args, get_origin

from .base import References
from .utils import group_by_id

if TYPE_CHECKING:
    from .base import DugElement

_Index = dict[str, list["DugElement"]]


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


@cache
def _literal_values(cls: type[DugElement], field_name: str) -> frozenset[object] | None:
    """Return the values *cls*'s field allows if it is a `Literal`, else None."""
    annotation = cls.model_fields[field_name].annotation
    return frozenset(get_args(annotation)) if get_origin(annotation) is Literal else None


def find_missing_references(elements: Iterable[DugElement]) -> dict[str, set[str]]:
    """Find IDs that elements refer to but that are not in the collection.

    An element refers to others through the fields marked with `References`: `parents`, and
    in v2 `variable_list`, `section_list` and `studies`. Nothing lists its children: a study
    does not list its resources, nor a resource the resources or content under it.

    Args:
        elements: An iterable of DugElement objects.

    Returns:
        A dict mapping each referring field name to the set of IDs it refers to that are
        missing. Empty dict if every reference resolves.
    """
    all_elements = list(elements)
    return _missing_references(all_elements, group_by_id(all_elements))


def _missing_references(elements: list[DugElement], by_id: _Index) -> dict[str, set[str]]:
    missing: dict[str, set[str]] = {}
    for elem in elements:
        for field_name, _ in _reference_fields(type(elem)):
            for ref in getattr(elem, field_name):
                if ref not in by_id:
                    missing.setdefault(field_name, set()).add(ref)
    return missing


def find_inconsistent_references(elements: Iterable[DugElement]) -> list[str]:
    """Find references that resolve but point at the wrong kind of element.

    Each referenced element must have the `type` that its field's `References` marker
    declares: `element_type`, or for `parents` the element's `parent_type`. An element that
    names parents must say what type they are, and when its class narrows `parent_type` to a
    `Literal`, the value must be one it allows. Loading enforces that too, but pydantic does
    not validate assignment, so an element changed after it was built is caught here. IDs
    that do not resolve are left to `find_missing_references()`. A field marked `inherited`,
    such as `studies`, must name exactly what the element's parents imply: the parents of its
    `element_type`, and whatever the same field names on the other parents. Every
    element is checked, even one that shares its ID with another; a reference to a shared ID
    must suit every element that has it.

    An earlier version also checked that a `children` list and its members' `parents` agreed
    in both directions. Those lists are gone (a child names its parent; nothing lists its
    children), so there is nothing left to disagree.

    Args:
        elements: An iterable of DugElement objects.

    Returns:
        One sentence per problem, naming the element at fault. Empty list if none.
    """
    all_elements = list(elements)
    return _inconsistent_references(all_elements, group_by_id(all_elements))


def _inconsistent_references(elements: list[DugElement], by_id: _Index) -> list[str]:
    problems: list[str] = []
    for elem in elements:
        for field_name, marker in _reference_fields(type(elem)):
            refs = getattr(elem, field_name)
            expected = marker.element_type
            if marker.type_from:
                expected = getattr(elem, marker.type_from)
                allowed = _literal_values(type(elem), marker.type_from)
                if allowed is not None and expected not in allowed:
                    problems.append(
                        f"{elem.id}: {marker.type_from} is {expected!r}, not one of "
                        f"{', '.join(repr(v) for v in sorted(map(str, allowed)))}"
                    )
                    continue
                if refs and not expected:
                    problems.append(f"{elem.id}: {field_name} is set but {marker.type_from} is empty")
                    continue
            if not expected:
                continue
            for ref in refs:
                for target in by_id.get(ref, ()):
                    if target.type != expected:
                        problems.append(
                            f"{elem.id}: {field_name} names {ref}, a {target.type or 'untyped element'}, "
                            f"not a {expected}"
                        )
            if marker.inherited:
                problem = _inherited_problem(elem, field_name, marker.element_type, by_id)
                if problem:
                    problems.append(problem)
    return problems


def _inherited_problem(elem: DugElement, field_name: str, element_type: str, by_id: _Index) -> str:
    """Return a problem if *elem*'s inherited *field_name* is not what its parents imply.

    The parents imply those of them that are of *element_type*, and whatever the same field
    names on the others. An element without parents is not checked, since there is nothing
    to derive the field from, nor one whose parents do not all resolve.
    """
    implied: set[str] = set()
    for parent_id in elem.parents:
        if parent_id not in by_id:
            return ""
        for parent in by_id[parent_id]:
            if parent.type == element_type:
                implied.add(parent.id)
            else:
                implied.update(getattr(parent, field_name, ()))
    named = set(getattr(elem, field_name))
    if not elem.parents or named == implied:
        return ""
    return (
        f"{elem.id}: {field_name} names {', '.join(sorted(named)) or 'nothing'}, but its parents "
        f"put it under {', '.join(sorted(implied)) or 'nothing'}"
    )


def validate_references(elements: Iterable[DugElement]) -> None:
    """Validate that every `References` field points at the right elements in the collection.

    First that no two elements share an ID, since a reference to a shared ID is ambiguous;
    then that every referenced ID is in the collection, and that each points at the right kind
    of element (see `find_inconsistent_references()`). This is opt-in rather than part of
    loading, because a producer may legitimately split related elements across several files.

    Args:
        elements: An iterable of DugElement objects.

    Raises:
        DuplicateIdError: If two elements share an ID.
        MissingReferenceError: If any referenced ID is not in the collection.
        InconsistentReferenceError: If a reference points at the wrong type of element.
    """
    all_elements = list(elements)
    by_id = group_by_id(all_elements)
    duplicates = {id_: len(elems) for id_, elems in by_id.items() if len(elems) > 1}
    if duplicates:
        raise DuplicateIdError(duplicates)
    missing = _missing_references(all_elements, by_id)
    if missing:
        all_missing = set().union(*missing.values())
        raise MissingReferenceError(
            all_missing, reference_type="/".join(sorted(missing)), by_field=missing
        )
    problems = _inconsistent_references(all_elements, by_id)
    if problems:
        raise InconsistentReferenceError(problems)
