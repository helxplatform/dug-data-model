"""Tests for dug_data_model validation functions."""

from typing import Annotated, Literal

import pytest
from pydantic import Field

from dug_data_model.v2 import (
    DugElement,
    DugDocument,
    DugContent,
    DugStudy,
    DugVariable,
    DugResource,
    DuplicateIdError,
    InconsistentReferenceError,
    MissingReferenceError,
    References,
    find_duplicate_ids,
    find_inconsistent_references,
    find_missing_references,
    validate_references,
    validate_unique_ids,
)


# ---------------------------------------------------------------------------
# find_duplicate_ids
# ---------------------------------------------------------------------------

class TestFindDuplicateIds:
    def test_no_duplicates(self):
        elements = [
            DugVariable(id="v1", name="V1", description="desc"),
            DugVariable(id="v2", name="V2", description="desc"),
        ]
        result = find_duplicate_ids(elements)
        assert result == {}

    def test_finds_duplicates(self):
        elements = [
            DugVariable(id="v1", name="V1", description="desc"),
            DugVariable(id="v1", name="V1 dup", description="desc"),
            DugVariable(id="v2", name="V2", description="desc"),
        ]
        result = find_duplicate_ids(elements)
        assert "v1" in result
        assert result["v1"] == 2
        assert "v2" not in result

    def test_empty_list(self):
        result = find_duplicate_ids([])
        assert result == {}


# ---------------------------------------------------------------------------
# validate_unique_ids
# ---------------------------------------------------------------------------

class TestValidateUniqueIds:
    def test_no_duplicates(self):
        elements = [
            DugVariable(id="v1", name="V1", description="desc"),
            DugVariable(id="v2", name="V2", description="desc"),
        ]
        validate_unique_ids(elements)  # Should not raise

    def test_raises_on_duplicates(self):
        elements = [
            DugVariable(id="v1", name="V1", description="desc"),
            DugVariable(id="v1", name="V1 dup", description="desc"),
        ]
        with pytest.raises(DuplicateIdError) as exc_info:
            validate_unique_ids(elements)
        assert "v1" in exc_info.value.duplicate_ids


# ---------------------------------------------------------------------------
# find_missing_references / validate_references
# ---------------------------------------------------------------------------

def _document_tree():
    return [
        DugStudy(id="s1", name="Study", description="desc", document_list=["d1"]),
        DugDocument(id="d1", name="Doc", description="", content_list=["d1/a"],
                    parents=["s1"], parent_type="study"),
        DugContent(id="d1/a", name="A", description="text",
                   parents=["d1"], parent_type="document"),
    ]


class TestReferences:
    def test_complete_tree_has_no_missing_references(self):
        assert find_missing_references(_document_tree()) == {}
        validate_references(_document_tree())

    def test_missing_parent(self):
        elements = _document_tree()[1:]  # drop the study
        assert find_missing_references(elements) == {"parents": {"s1"}}

    def test_missing_list_member(self):
        elements = _document_tree()[:2]  # drop the content
        assert find_missing_references(elements) == {"content_list": {"d1/a"}}

    def test_validate_raises_with_all_missing_ids(self):
        elements = [_document_tree()[1]]
        with pytest.raises(MissingReferenceError) as exc_info:
            validate_references(elements)
        assert exc_info.value.missing_ids == {"s1", "d1/a"}
        assert exc_info.value.reference_type == "content_list/parents"

    def test_validate_says_which_field_each_missing_id_came_from(self):
        elements = [_document_tree()[1]]
        with pytest.raises(MissingReferenceError) as exc_info:
            validate_references(elements)
        assert exc_info.value.by_field == {"content_list": {"d1/a"}, "parents": {"s1"}}
        assert str(exc_info.value) == (
            "Missing content_list references: d1/a; Missing parents references: s1"
        )

    def test_error_built_without_by_field_keeps_its_old_message(self):
        error = MissingReferenceError({"b", "a"})
        assert str(error) == "Missing parent references: a, b"
        assert error.by_field == {"parent": {"a", "b"}}

    def test_accepts_a_generator(self):
        assert find_missing_references(e for e in _document_tree()) == {}


def _resource_tree():
    return [
        DugStudy(id="s1", name="Study", description="desc", resource_list=["r1"],
                 document_list=["d1"]),
        DugResource(id="r1", name="Deposit", description="", document_list=["d1"],
                    parents=["s1"], parent_type="study"),
        DugDocument(id="d1", name="Doc", description="", parents=["r1"], parent_type="resource"),
    ]


class TestInconsistentReferences:
    def test_consistent_trees_have_no_problems(self):
        assert find_inconsistent_references(_document_tree()) == []
        assert find_inconsistent_references(_resource_tree()) == []

    def test_a_list_naming_the_wrong_type(self):
        study, document, content = _document_tree()
        study.document_list = ["d1/a"]
        document.parents = []
        assert find_inconsistent_references([study, document, content]) == [
            "s1: document_list names d1/a, a content, not a document",
        ]

    def test_a_parent_of_the_wrong_type(self):
        study, document, content = _document_tree()
        content.parents = ["s1"]
        problems = find_inconsistent_references([study, document, content])
        assert "d1/a: parents names s1, a study, not a document" in problems

    def test_parent_type_left_empty_is_not_checked(self):
        study = DugStudy(id="s1", name="Study", description="desc")
        content = DugContent(id="c", name="C", description="", parents=["s1"])
        assert find_inconsistent_references([study, content]) == []

    def test_a_listed_child_that_names_another_parent(self):
        study, resource, document = _resource_tree()
        document.parents, document.parent_type = ["s1"], "study"
        assert find_inconsistent_references([study, resource, document]) == [
            "r1: document_list lists d1, whose parents do not include it",
        ]

    def test_a_child_its_parent_does_not_list(self):
        study, document, content = _document_tree()
        document.content_list = []
        assert find_inconsistent_references([study, document, content]) == [
            "d1/a: names d1 as a parent, but its content_list does not list it",
        ]

    def test_lists_that_are_not_children_need_not_agree(self):
        # The study lists d1 although d1's parent is the resource, as the README describes.
        assert "s1" not in _resource_tree()[2].parents
        validate_references(_resource_tree())

    def test_validate_raises_on_inconsistency(self):
        study, document, content = _document_tree()
        document.content_list = []
        with pytest.raises(InconsistentReferenceError) as exc_info:
            validate_references([study, document, content])
        assert exc_info.value.problems == [
            "d1/a: names d1 as a parent, but its content_list does not list it",
        ]


class _Tagged(DugElement):
    """An element with `_list` fields that are not references, and one that is."""

    type: Literal["tagged"] = "tagged"
    keyword_list: list[str] = Field(default_factory=list)
    file_list: list[dict[str, str]] = Field(default_factory=list)
    see_also: Annotated[list[str], References()] = Field(default_factory=list)


class TestReferenceFieldsAreMarked:
    def test_unmarked_list_fields_are_not_references(self):
        elem = _Tagged(id="t1", name="T", description="", keyword_list=["pain"],
                       file_list=[{"name": "README.pdf"}])
        assert find_missing_references([elem]) == {}

    def test_a_marked_field_is_a_reference_whatever_its_name(self):
        elem = _Tagged(id="t1", name="T", description="", see_also=["t2"])
        assert find_missing_references([elem]) == {"see_also": {"t2"}}
