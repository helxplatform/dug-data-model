"""Tests for dug_data_model utility functions."""

import pytest
from dug_data_model.v2 import (
    DugConcept,
    DugVariable,
    DugStudy,
    DugSection,
    filter_by_type,
    group_by_type,
    group_by_id,
    count_by_type,
    get_element_by_id,
    get_all_ids,
    build_parent_map,
    get_children,
    dedupe_and_sort,
)


# ---------------------------------------------------------------------------
# Filtering and grouping
# ---------------------------------------------------------------------------

@pytest.fixture
def mixed_elements():
    """Create a mixed list of elements for testing."""
    return [
        DugVariable(id="v1", name="Var 1", description="desc"),
        DugVariable(id="v2", name="Var 2", description="desc"),
        DugStudy(id="s1", name="Study 1", description="desc"),
        DugSection(id="sec1", name="Section 1", description="desc"),
        DugConcept(id="c1", name="Concept 1", description="desc"),
    ]


class TestFilterByType:
    def test_filter_variables(self, mixed_elements):
        result = filter_by_type(mixed_elements, "variable")
        assert len(result) == 2
        assert all(e.type == "variable" for e in result)

    def test_filter_studies(self, mixed_elements):
        result = filter_by_type(mixed_elements, "study")
        assert len(result) == 1
        assert result[0].id == "s1"

    def test_filter_nonexistent_type(self, mixed_elements):
        result = filter_by_type(mixed_elements, "nonexistent")
        assert result == []

    def test_filter_empty_list(self):
        result = filter_by_type([], "variable")
        assert result == []


class TestGroupByType:
    def test_groups_correctly(self, mixed_elements):
        grouped = group_by_type(mixed_elements)
        assert len(grouped["variable"]) == 2
        assert len(grouped["study"]) == 1
        assert len(grouped["section"]) == 1
        assert len(grouped["concept"]) == 1

    def test_empty_list(self):
        grouped = group_by_type([])
        assert grouped == {}


class TestGroupById:
    def test_groups_correctly(self, mixed_elements):
        by_id = group_by_id(mixed_elements)
        assert len(by_id) == 5
        assert all(len(elems) == 1 for elems in by_id.values())

    def test_finds_duplicates(self):
        elements = [
            DugVariable(id="v1", name="Var 1", description="desc"),
            DugVariable(id="v1", name="Var 1 dup", description="desc"),
            DugVariable(id="v2", name="Var 2", description="desc"),
        ]
        by_id = group_by_id(elements)
        assert len(by_id["v1"]) == 2
        assert len(by_id["v2"]) == 1


class TestCountByType:
    def test_counts_correctly(self, mixed_elements):
        counts = count_by_type(mixed_elements)
        assert counts["variable"] == 2
        assert counts["study"] == 1
        assert counts["section"] == 1
        assert counts["concept"] == 1

    def test_empty_list(self):
        counts = count_by_type([])
        assert counts == {}


class TestGetElementById:
    def test_finds_element(self, mixed_elements):
        result = get_element_by_id(mixed_elements, "v1")
        assert result is not None
        assert result.id == "v1"

    def test_returns_none_if_not_found(self, mixed_elements):
        result = get_element_by_id(mixed_elements, "nonexistent")
        assert result is None

    def test_empty_list(self):
        result = get_element_by_id([], "v1")
        assert result is None


class TestGetAllIds:
    def test_returns_all_ids(self, mixed_elements):
        ids = get_all_ids(mixed_elements)
        assert ids == {"v1", "v2", "s1", "sec1", "c1"}

    def test_empty_list(self):
        ids = get_all_ids([])
        assert ids == set()


# ---------------------------------------------------------------------------
# Hierarchy utilities
# ---------------------------------------------------------------------------

@pytest.fixture
def hierarchical_elements():
    """Create elements with parent relationships."""
    study = DugStudy(id="s1", name="Study", description="desc")
    section = DugSection(id="sec1", name="Section", description="desc", parents=["s1"])
    var1 = DugVariable(id="v1", name="Var 1", description="desc", parents=["sec1"])
    var2 = DugVariable(id="v2", name="Var 2", description="desc", parents=["sec1"])
    var3 = DugVariable(id="v3", name="Var 3", description="desc", parents=["s1"])
    return [study, section, var1, var2, var3]


class TestBuildParentMap:
    def test_builds_map(self, hierarchical_elements):
        parent_map = build_parent_map(hierarchical_elements)
        assert len(parent_map["s1"]) == 2  # section and var3
        assert len(parent_map["sec1"]) == 2  # var1 and var2

    def test_empty_list(self):
        parent_map = build_parent_map([])
        assert parent_map == {}


class TestGetChildren:
    def test_gets_children(self, hierarchical_elements):
        children = get_children(hierarchical_elements, "sec1")
        assert len(children) == 2
        assert all(c.id in ("v1", "v2") for c in children)

    def test_no_children(self, hierarchical_elements):
        children = get_children(hierarchical_elements, "v1")
        assert children == []

    def test_nonexistent_parent(self, hierarchical_elements):
        children = get_children(hierarchical_elements, "nonexistent")
        assert children == []


# ---------------------------------------------------------------------------
# Other utilities
# ---------------------------------------------------------------------------

class TestDedupeAndSort:
    def test_deduplicates(self):
        result = dedupe_and_sort(["b", "a", "b", "c", "a"])
        assert result == ["a", "b", "c"]

    def test_already_unique(self):
        result = dedupe_and_sort(["c", "b", "a"])
        assert result == ["a", "b", "c"]

    def test_empty_list(self):
        result = dedupe_and_sort([])
        assert result == []
