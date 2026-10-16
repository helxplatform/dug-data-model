"""Validation utilities for the Dug data model.

This module provides functions for validating collections of DugElement objects:
that their IDs are unique, and that the IDs they refer to resolve to the right elements.

The public API, re-exported from the package:

- `find_duplicate_ids()` and `validate_unique_ids()` (raises `DuplicateIdError`)
- `find_missing_references()` and `find_inconsistent_references()`
- `validate_references()`, which runs all three checks and raises `DuplicateIdError`,
  `MissingReferenceError` or `InconsistentReferenceError`

The private helpers below them are grouped by what they do. The fields of a class that carry
the `References` marker come from `References.fields_of()` in `base.py`.

This is one module, sectioned, rather than several: the scaffold copies it into every version
and `tests/test_scaffold_copies.py` checks the copies match, so each extra file would be one
more copy to keep in step.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from functools import cache
from typing import TYPE_CHECKING, Literal, get_args, get_origin

from .base import References
from .utils import group_by_id

if TYPE_CHECKING:
    from .base import DugElement

_Index = dict[str, list["DugElement"]]


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Public checks
# ---------------------------------------------------------------------------

def find_duplicate_ids(elements: Iterable[DugElement]) -> dict[str, int]:
    """Find duplicate element IDs.

    Args:
        elements: An iterable of DugElement objects.

    Returns:
        A dict mapping duplicate IDs to their occurrence count.
        Empty dict if no duplicates.
    """
    return _duplicate_ids(group_by_id(elements))


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

    An element refers to others through the fields marked with `References`: `parents`, and
    in v2 `variable_list` and `section_list`.

    Args:
        elements: An iterable of DugElement objects.

    Returns:
        A dict mapping each referring field name to the set of IDs it refers to that are
        missing. Empty dict if every reference resolves.
    """
    all_elements = list(elements)
    return _missing_references(all_elements, group_by_id(all_elements))


def find_inconsistent_references(elements: Iterable[DugElement]) -> list[str]:
    """Find references that resolve but point at the wrong kind of element.

    Each rule below has its own function in this module:

    - Every element's `type` must be one its class allows, so that an element whose `type`
      was changed after loading cannot pass for another kind (`_not_allowed()`).
    - Each referenced element must have the `type` that its field's `References` marker
      declares: `element_type`, or for `parents` the element's `parent_type`. When its class
      narrows `parent_type` to a `Literal`, the value must be one it allows, an element that
      names parents must say what type they are, and one that says must name them. Where
      `parent_type` is the base class's free string, as on variables and sections, it is
      checked only when set, since producers written before this check (the HEAL CDE output,
      for one) leave it empty (`_reference_field_problems()`).
    - `parents` may not go round in a cycle, which no tree can contain (`_parent_cycles()`).

    Loading enforces the `Literal` types too, but pydantic does not validate assignment, so
    an element changed after it was built is caught here. IDs that do not resolve are left to
    `find_missing_references()`. Every element is checked, even one that shares its ID with
    another; a reference to a shared ID must suit every element that has it.

    Args:
        elements: An iterable of DugElement objects.

    Returns:
        One sentence per problem, naming the element at fault. Empty list if none.
    """
    all_elements = list(elements)
    return _inconsistent_references(all_elements, group_by_id(all_elements))


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
    duplicates = _duplicate_ids(by_id)
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


# ---------------------------------------------------------------------------
# The checks, against an index by ID that validate_references() builds once for all of them
# ---------------------------------------------------------------------------

def _duplicate_ids(by_id: _Index) -> dict[str, int]:
    return {id_: len(elems) for id_, elems in by_id.items() if len(elems) > 1}


def _missing_references(elements: list[DugElement], by_id: _Index) -> dict[str, set[str]]:
    missing: dict[str, set[str]] = {}
    for elem in elements:
        for field_name, _ in References.fields_of(type(elem)):
            for ref in getattr(elem, field_name):
                if ref not in by_id:
                    missing.setdefault(field_name, set()).add(ref)
    return missing


def _inconsistent_references(elements: list[DugElement], by_id: _Index) -> list[str]:
    problems: list[str] = []
    for elem in elements:
        if problem := _not_allowed(elem, "type"):
            problems.append(problem)
        for field_name, marker in References.fields_of(type(elem)):
            problems.extend(_reference_field_problems(elem, field_name, marker, by_id))
    problems.extend(_parent_cycles(by_id))
    return problems


# ---------------------------------------------------------------------------
# The rules that find_inconsistent_references() applies
# ---------------------------------------------------------------------------

def _reference_field_problems(
    elem: DugElement, field_name: str, marker: References, by_id: _Index
) -> list[str]:
    """Return the problems with one of *elem*'s `References` fields.

    The field's `type_from`, if it has one, is checked first, and a bad value there, or one
    set without the references or the references without it, stops the field's other
    checks, since they would only repeat it; then each resolved target must have the expected
    type. Only a class that narrows `type_from` to a `Literal` must set it with the
    references; on any other class an empty one skips the type check.
    """
    refs = getattr(elem, field_name)
    expected = marker.element_type
    if marker.type_from:
        expected = getattr(elem, marker.type_from)
        if problem := _not_allowed(elem, marker.type_from):
            return [problem]
        if _literal_values(type(elem), marker.type_from) is not None:
            if refs and not expected:
                return [f"{elem.id}: {field_name} is set but {marker.type_from} is empty"]
            if expected and not refs:
                return [f"{elem.id}: {marker.type_from} is {expected!r} but {field_name} is empty"]
    if not expected:
        return []
    return [
        f"{elem.id}: {field_name} names {ref}, a {target.type or 'untyped element'}, not a {expected}"
        for ref in refs
        for target in by_id.get(ref, ())
        if target.type != expected
    ]


def _not_allowed(elem: DugElement, field_name: str) -> str:
    """Return a problem if *elem*'s *field_name* is outside the `Literal` its class declares.

    Loading enforces the `Literal`, but pydantic does not validate assignment, so a value
    set afterwards is only caught here.
    """
    allowed = _literal_values(type(elem), field_name)
    value = getattr(elem, field_name)
    if allowed is None or value in allowed:
        return ""
    return f"{elem.id}: {field_name} is {value!r}, not one of {', '.join(repr(v) for v in sorted(map(str, allowed)))}"


def _parent_cycles(by_id: _Index) -> list[str]:
    """Return one problem per cycle in `parents`, named after the element it returns to.

    A depth-first walk up `parents`, iterative so that a deep tree cannot hit the recursion
    limit. An element is grey while the walk is above it and black once everything above it
    is done, so reaching a grey element again means the walk has gone round a cycle.
    """
    grey, black = 1, 2
    state: dict[str, int] = {}
    problems: list[str] = []

    def parents_of(id_: str) -> Iterator[str]:
        return iter([p for elem in by_id[id_] for p in elem.parents if p in by_id])

    for start in by_id:
        if start in state:
            continue
        state[start] = grey
        path = [start]
        stack = [parents_of(start)]
        while stack:
            parent = next(stack[-1], None)
            if parent is None:
                state[path.pop()] = black
                stack.pop()
            elif parent not in state:
                state[parent] = grey
                path.append(parent)
                stack.append(parents_of(parent))
            elif state[parent] == grey:
                cycle = path[path.index(parent):] + [parent]
                problems.append(f"{parent}: parents lead back to {parent} ({' -> '.join(cycle)})")
    return problems


# ---------------------------------------------------------------------------
# Reading a class's fields
# ---------------------------------------------------------------------------

@cache
def _literal_values(cls: type[DugElement], field_name: str) -> frozenset[object] | None:
    """Return the values *cls*'s field allows if it is a `Literal`, else None."""
    annotation = cls.model_fields[field_name].annotation
    return frozenset(get_args(annotation)) if get_origin(annotation) is Literal else None
