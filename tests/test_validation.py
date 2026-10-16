"""Tests for dug_data_model validation functions."""

from typing import Annotated, Literal

import pytest
from pydantic import Field

from dug_data_model.v2 import (
    DugElement,
    DugSection,
    DugStudy,
    DugVariable,
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

def _study_tree():
    """A study, a section in it, and a variable in the section, each naming its parent."""
    return [
        DugStudy(id="s1", name="Study", description="desc", section_list=["crf"],
                 variable_list=["v1"]),
        DugSection(id="crf", name="CRF", description="", parents=["s1"], parent_type="study",
                   variable_list=["v1"]),
        DugVariable(id="v1", name="V1", description="", parents=["crf"], parent_type="section"),
    ]


class TestReferences:
    def test_complete_tree_has_no_missing_references(self):
        assert find_missing_references(_study_tree()) == {}
        validate_references(_study_tree())

    def test_missing_parent(self):
        elements = _study_tree()[1:]  # drop the study
        assert find_missing_references(elements) == {"parents": {"s1"}}

    def test_missing_list_member(self):
        study = DugStudy(id="s1", name="Study", description="desc", variable_list=["v1"])
        assert find_missing_references([study]) == {"variable_list": {"v1"}}

    def test_validate_raises_with_all_missing_ids(self):
        section = _study_tree()[1]
        with pytest.raises(MissingReferenceError) as exc_info:
            validate_references([section])
        assert exc_info.value.missing_ids == {"s1", "v1"}
        assert exc_info.value.reference_type == "parents/variable_list"

    def test_validate_says_which_field_each_missing_id_came_from(self):
        section = _study_tree()[1]
        with pytest.raises(MissingReferenceError) as exc_info:
            validate_references([section])
        assert exc_info.value.by_field == {"parents": {"s1"}, "variable_list": {"v1"}}
        assert str(exc_info.value) == (
            "Missing parents references: s1; Missing variable_list references: v1"
        )

    def test_error_built_without_by_field_keeps_its_old_message(self):
        error = MissingReferenceError({"b", "a"})
        assert str(error) == "Missing parent references: a, b"
        assert error.by_field == {"parent": {"a", "b"}}

    def test_accepts_a_generator(self):
        assert find_missing_references(e for e in _study_tree()) == {}


class _Node(DugElement):
    """An element whose class narrows `parent_type` to a `Literal`, as a stricter type would."""

    type: Literal["node"] = "node"
    parent_type: Literal["", "study", "node"] = ""


class TestInconsistentReferences:
    def test_a_consistent_tree_has_no_problems(self):
        assert find_inconsistent_references(_study_tree()) == []

    def test_a_list_naming_the_wrong_type(self):
        study = DugStudy(id="s1", name="Study", description="desc", variable_list=["s2"])
        other = DugStudy(id="s2", name="Study 2", description="desc")
        assert find_inconsistent_references([study, other]) == [
            "s1: variable_list names s2, a study, not a variable",
        ]

    def test_a_parent_of_the_wrong_type(self):
        study, section, variable = _study_tree()
        variable.parents = ["s1"]
        assert find_inconsistent_references([study, section, variable]) == [
            "v1: parents names s1, a study, not a section",
        ]

    def test_a_free_parent_type_is_checked_only_when_set(self):
        # The HEAL CDE output writes variables and sections with parents and no parent_type.
        study = DugStudy(id="s1", name="Study", description="desc")
        section = DugSection(id="crf", name="CRF", description="", parents=["s1"])
        variable = DugVariable(id="v", name="V", description="", parents=["crf"])
        assert find_inconsistent_references([study, section, variable]) == []
        variable.parent_type = "study"
        assert find_inconsistent_references([study, section, variable]) == [
            "v: parents names crf, a section, not a study",
        ]

    def test_parents_need_a_parent_type_where_the_class_narrows_it(self):
        study = DugStudy(id="s1", name="Study", description="desc")
        node = _Node(id="n", name="N", description="", parents=["s1"])
        assert find_inconsistent_references([study, node]) == [
            "n: parents is set but parent_type is empty",
        ]

    def test_a_parent_type_without_parents(self):
        lost = _Node(id="n", name="N", description="", parent_type="study")
        top = _Node(id="top", name="Top", description="")
        assert find_inconsistent_references([lost, top]) == [
            "n: parent_type is 'study' but parents is empty",
        ]

    def test_a_parent_type_assigned_after_loading_is_checked(self):
        # Pydantic does not validate assignment, so the Literal is checked again here.
        study = DugStudy(id="s1", name="Study", description="desc")
        node = _Node(id="n", name="N", description="", parents=["s1"], parent_type="study")
        node.parent_type = "section"
        assert find_inconsistent_references([study, node]) == [
            "n: parent_type is 'section', not one of '', 'node', 'study'",
        ]

    def test_a_type_assigned_after_loading_is_checked(self):
        # Otherwise a section renamed to "study" would satisfy a reference to a study.
        study, section, variable = _study_tree()
        section.type = "study"
        assert "crf: type is 'study', not one of 'section'" in (
            find_inconsistent_references([study, section, variable])
        )

    def test_lists_need_not_agree_with_parents(self):
        # variable_list is a reference list, so a variable that names the study as its
        # parent need not be listed, and vice versa.
        study = DugStudy(id="s1", name="Study", description="desc", variable_list=["v2"])
        v1 = DugVariable(id="v1", name="A", description="", parents=["s1"], parent_type="study")
        v2 = DugVariable(id="v2", name="B", description="")
        validate_references([study, v1, v2])

    def test_every_element_sharing_an_id_is_checked(self):
        study = DugStudy(id="s1", name="Study", description="desc")
        bad = DugVariable(id="x", name="X", description="", parents=["s1"], parent_type="section")
        good = DugVariable(id="x", name="X", description="", parents=["s1"], parent_type="study")
        assert find_inconsistent_references([study, bad, good]) == [
            "x: parents names s1, a study, not a section",
        ]

    def test_validate_rejects_duplicate_ids_first(self):
        study, section, variable = _study_tree()
        twin = DugSection(id="crf", name="CRF again", description="", parents=["s1"],
                          parent_type="study")
        with pytest.raises(DuplicateIdError) as exc_info:
            validate_references([study, section, variable, twin])
        assert exc_info.value.duplicate_ids == {"crf": 2}

    def test_parents_that_go_round_in_a_cycle(self):
        a = _Node(id="a", name="A", description="", parents=["b"], parent_type="node")
        b = _Node(id="b", name="B", description="", parents=["a"], parent_type="node")
        own = _Node(id="own", name="O", description="", parents=["own"], parent_type="node")
        assert find_inconsistent_references([a, b, own]) == [
            "a: parents lead back to a (a -> b -> a)",
            "own: parents lead back to own (own -> own)",
        ]

    def test_shared_ancestors_are_not_a_cycle(self):
        # Two paths up to the same study meet, but never return to where they began.
        study = DugStudy(id="s1", name="Study", description="desc")
        a = _Node(id="a", name="A", description="", parents=["s1"], parent_type="study")
        b = _Node(id="b", name="B", description="", parents=["s1"], parent_type="study")
        leaf = _Node(id="leaf", name="L", description="", parents=["a", "b"], parent_type="node")
        assert find_inconsistent_references([study, a, b, leaf]) == []

    def test_validate_raises_on_inconsistency(self):
        study, section, variable = _study_tree()
        variable.parents = ["s1"]
        with pytest.raises(InconsistentReferenceError) as exc_info:
            validate_references([study, section, variable])
        assert exc_info.value.problems == [
            "v1: parents names s1, a study, not a section",
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
