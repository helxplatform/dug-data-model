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
        DugStudy(id="s1", name="Study", description="desc"),
        DugDocument(id="d1", name="Doc", description="", parents=["s1"], parent_type="study"),
        DugContent(id="d1/a", name="A", description="", content="text",
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
        study = DugStudy(id="s1", name="Study", description="desc", variable_list=["v1"])
        assert find_missing_references([study]) == {"variable_list": {"v1"}}

    def test_missing_study_named_in_studies(self):
        study, document, content = _document_tree()
        content.studies = ["s1", "s2"]
        assert find_missing_references([study, document, content]) == {"studies": {"s2"}}

    def test_validate_raises_with_all_missing_ids(self):
        document = _document_tree()[1]
        document.studies = ["s2"]
        with pytest.raises(MissingReferenceError) as exc_info:
            validate_references([document])
        assert exc_info.value.missing_ids == {"s1", "s2"}
        assert exc_info.value.reference_type == "parents/studies"

    def test_validate_says_which_field_each_missing_id_came_from(self):
        document = _document_tree()[1]
        document.studies = ["s2"]
        with pytest.raises(MissingReferenceError) as exc_info:
            validate_references([document])
        assert exc_info.value.by_field == {"parents": {"s1"}, "studies": {"s2"}}
        assert str(exc_info.value) == (
            "Missing parents references: s1; Missing studies references: s2"
        )

    def test_error_built_without_by_field_keeps_its_old_message(self):
        error = MissingReferenceError({"b", "a"})
        assert str(error) == "Missing parent references: a, b"
        assert error.by_field == {"parent": {"a", "b"}}

    def test_accepts_a_generator(self):
        assert find_missing_references(e for e in _document_tree()) == {}


def _resource_tree():
    return [
        DugStudy(id="s1", name="Study", description="desc"),
        DugResource(id="r1", name="Deposit", description="", parents=["s1"], parent_type="study"),
        DugDocument(id="d1", name="Doc", description="", parents=["r1"], parent_type="resource"),
    ]


class TestInconsistentReferences:
    def test_consistent_trees_have_no_problems(self):
        assert find_inconsistent_references(_document_tree()) == []
        assert find_inconsistent_references(_resource_tree()) == []

    def test_a_list_naming_the_wrong_type(self):
        study = DugStudy(id="s1", name="Study", description="desc", variable_list=["s2"])
        other = DugStudy(id="s2", name="Study 2", description="desc")
        assert find_inconsistent_references([study, other]) == [
            "s1: variable_list names s2, a study, not a variable",
        ]

    def test_a_parent_of_the_wrong_type(self):
        study, document, content = _document_tree()
        content.parents = ["s1"]
        problems = find_inconsistent_references([study, document, content])
        assert "d1/a: parents names s1, a study, not a document" in problems

    def test_studies_must_name_studies(self):
        # `studies` is checked like any reference list: the ID must resolve to a study.
        study, document, content = _document_tree()
        content.studies = ["s1", "d1"]
        assert find_inconsistent_references([study, document, content]) == [
            "d1/a: studies names d1, a document, not a study",
        ]

    def test_a_study_named_in_studies_need_not_list_the_element(self):
        # `studies` is a shortcut up the tree, not a parent link, so the study has nothing
        # to agree with: a study lists none of its resources, documents or content.
        study, document, content = _document_tree()
        document.studies = content.studies = ["s1"]
        validate_references([study, document, content])

    def test_parent_type_left_empty_is_not_checked(self):
        study = DugStudy(id="s1", name="Study", description="desc")
        content = DugContent(id="c", name="C", description="", content="", parents=["s1"])
        assert find_inconsistent_references([study, content]) == []

    def test_a_resource_inside_a_resource(self):
        study = DugStudy(id="s1", name="S", description="")
        community = DugResource(id="community", name="Lab's Zenodo community", description="",
                                resource_type="website", parents=["s1"], parent_type="study")
        deposit = DugResource(id="deposit", name="Deposit", description="",
                              parents=["community"], parent_type="resource")
        assert find_inconsistent_references([study, community, deposit]) == []

    def test_nothing_lists_its_children(self):
        # A child names its parent; the parent has no list to keep in step with it.
        for cls in (DugStudy, DugResource, DugDocument):
            assert not {"document_list", "resource_list", "content_list"} & set(cls.model_fields)

    def test_lists_that_are_not_children_need_not_agree(self):
        # variable_list is a reference list, not a children list, so a variable that
        # names the study as its parent need not be listed, and vice versa.
        study = DugStudy(id="s1", name="Study", description="desc", variable_list=["v2"])
        v1 = DugVariable(id="v1", name="A", description="", parents=["s1"], parent_type="study")
        v2 = DugVariable(id="v2", name="B", description="")
        validate_references([study, v1, v2])

    def test_validate_raises_on_inconsistency(self):
        study, document, content = _document_tree()
        content.parents = ["s1"]
        with pytest.raises(InconsistentReferenceError) as exc_info:
            validate_references([study, document, content])
        assert exc_info.value.problems == [
            "d1/a: parents names s1, a study, not a document",
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
