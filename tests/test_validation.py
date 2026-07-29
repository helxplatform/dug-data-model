"""Tests for dug_data_model validation functions."""

import pytest
from dug_data_model.v2 import (
    DugVariable,
    DuplicateIdError,
    find_duplicate_ids,
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


