"""Tests for dug_data_model validation functions."""

import pytest
from dug_data_model.v2 import (
    DugDocument,
    DugContent,
    DugStudy,
    DugVariable,
    DuplicateIdError,
    MissingReferenceError,
    find_duplicate_ids,
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
        elements = _document_tree()[:2]  # drop the section
        assert find_missing_references(elements) == {"content_list": {"d1/a"}}

    def test_validate_raises_with_all_missing_ids(self):
        elements = [_document_tree()[1]]
        with pytest.raises(MissingReferenceError) as exc_info:
            validate_references(elements)
        assert exc_info.value.missing_ids == {"s1", "d1/a"}
        assert exc_info.value.reference_type == "content_list/parents"

    def test_accepts_a_generator(self):
        assert find_missing_references(e for e in _document_tree()) == {}
