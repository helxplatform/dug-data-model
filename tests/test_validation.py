"""Tests for dug_data_model validation functions."""

import pytest
from dug_data_model.v2 import (
    DugVariable,
    DugStudy,
    DugSection,
    DuplicateIdError,
    MissingReferenceError,
    find_duplicate_ids,
    find_missing_parents,
    find_missing_list_references,
    validate_unique_ids,
    validate_parent_references,
    validate_list_references,
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
# find_missing_parents
# ---------------------------------------------------------------------------

class TestFindMissingParents:
    def test_valid_references(self):
        elements = [
            DugStudy(id="s1", name="Study", description="desc"),
            DugVariable(id="v1", name="V1", description="desc", parents=["s1"]),
        ]
        result = find_missing_parents(elements)
        assert result == set()

    def test_missing_parent(self):
        elements = [
            DugVariable(id="v1", name="V1", description="desc", parents=["missing"]),
        ]
        result = find_missing_parents(elements)
        assert result == {"missing"}

    def test_no_parents(self):
        elements = [
            DugVariable(id="v1", name="V1", description="desc"),
        ]
        result = find_missing_parents(elements)
        assert result == set()


# ---------------------------------------------------------------------------
# find_missing_list_references
# ---------------------------------------------------------------------------

class TestFindMissingListReferences:
    def test_valid_study_variable_list(self):
        elements = [
            DugVariable(id="v1", name="V1", description="desc"),
            DugStudy(id="s1", name="Study", description="desc", variable_list=["v1"]),
        ]
        result = find_missing_list_references(elements)
        assert result == set()

    def test_missing_variable_in_study(self):
        elements = [
            DugStudy(id="s1", name="Study", description="desc", variable_list=["missing"]),
        ]
        result = find_missing_list_references(elements)
        assert result == {"missing"}

    def test_valid_section_variable_list(self):
        elements = [
            DugVariable(id="v1", name="V1", description="desc"),
            DugSection(id="sec1", name="Section", description="desc", variable_list=["v1"]),
        ]
        result = find_missing_list_references(elements)
        assert result == set()

    def test_missing_section_in_study(self):
        elements = [
            DugStudy(id="s1", name="Study", description="desc", section_list=["missing"]),
        ]
        result = find_missing_list_references(elements)
        assert result == {"missing"}


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
# validate_parent_references
# ---------------------------------------------------------------------------

class TestValidateParentReferences:
    def test_valid_references(self):
        elements = [
            DugStudy(id="s1", name="Study", description="desc"),
            DugVariable(id="v1", name="V1", description="desc", parents=["s1"]),
        ]
        validate_parent_references(elements)  # Should not raise

    def test_raises_on_missing_parent(self):
        elements = [
            DugVariable(id="v1", name="V1", description="desc", parents=["missing"]),
        ]
        with pytest.raises(MissingReferenceError) as exc_info:
            validate_parent_references(elements)
        assert "missing" in exc_info.value.missing_ids


# ---------------------------------------------------------------------------
# validate_list_references
# ---------------------------------------------------------------------------

class TestValidateListReferences:
    def test_valid_references(self):
        elements = [
            DugVariable(id="v1", name="V1", description="desc"),
            DugStudy(id="s1", name="Study", description="desc", variable_list=["v1"]),
        ]
        validate_list_references(elements)  # Should not raise

    def test_raises_on_missing_reference(self):
        elements = [
            DugStudy(id="s1", name="Study", description="desc", variable_list=["missing"]),
        ]
        with pytest.raises(MissingReferenceError):
            validate_list_references(elements)
