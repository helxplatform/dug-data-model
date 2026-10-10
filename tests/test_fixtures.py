"""A real producer output, loaded and checked end to end.

tests/fixtures/heal_hdp00009.json is HEAL study HDP00009 as the reference producer,
heal-data-stewards/heal-non-data-dictionaries, writes it: one study, two Figshare deposits
as resources, one PDF README in each as a file resource under the deposit with a single
content element, and a file inventory on each deposit. The extracted text is CC-BY-4.0, from
Min Gon Kim, Kai Yu, Bin He et al. and Kai Yu, Samantha Schmitt, Bin He et al. (Carnegie
Mellon University). It is a frozen example of the shape, refreshed when the model changes,
not a contract with that producer.

It started as a copy of the producer's examples/HDP00009/HDP00009.json (commit 8b52af1, on
its model-conventions branch) and has been edited by hand since to follow the model: text
moved from content's `description` to `content`; the study's and the deposits' child lists
went; and the READMEs, written as `DugDocument`s, became `DugResource`s with a `file_name`
and `mime_type` under their deposits, with `studies` on everything below the study. The
producer has not caught up yet: once it emits this shape, replace the file with its output
and drop this paragraph.
"""

import json
from pathlib import Path

import pytest
from dug_data_model.v2 import (
    CONTENT_TYPE,
    RESOURCE_TYPE,
    DugElementParsedList,
    DugResource,
    DugStudy,
    can_include_content,
    compact_dump,
    count_by_type,
    filter_by_type,
    get_element_by_id,
    validate_references,
    validate_unique_ids,
)

FIXTURE = Path(__file__).parent / "fixtures" / "heal_hdp00009.json"


@pytest.fixture(scope="module")
def raw() -> list:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def elements(raw) -> list:
    return DugElementParsedList.validate_python(raw)


def _files(elements):
    return [e for e in filter_by_type(elements, RESOURCE_TYPE) if e.mime_type]


def _deposits(elements):
    return [e for e in filter_by_type(elements, RESOURCE_TYPE) if not e.mime_type]


class TestRealOutput:
    def test_loads_with_every_type_in_the_resource_tree(self, elements):
        assert count_by_type(elements) == {"study": 1, "resource": 4, "content": 2}
        assert [type(e) for e in elements[:2]] == [DugStudy, DugResource]
        assert len(_deposits(elements)) == len(_files(elements)) == 2

    def test_ids_are_unique_and_every_reference_resolves(self, elements):
        validate_unique_ids(elements)
        validate_references(elements)

    def test_parent_chain_is_content_file_deposit_study(self, elements):
        study = elements[0]
        for content in filter_by_type(elements, CONTENT_TYPE):
            file = get_element_by_id(elements, content.parents[0])
            assert file.mime_type == "application/pdf" and content.parent_type == "resource"
            deposit = get_element_by_id(elements, file.parents[0])
            assert deposit.resource_type == "dataset" and file.parent_type == "resource"
            assert deposit.parents == [study.id] and deposit.parent_type == "study"

    def test_everything_below_the_study_names_it_in_studies(self, elements):
        study, *rest = elements
        assert all(e.studies == [study.id] for e in rest)
        assert "studies" not in DugStudy.model_fields

    def test_content_holds_text_under_a_licence_that_allows_it(self, elements):
        for content in filter_by_type(elements, CONTENT_TYPE):
            file = get_element_by_id(elements, content.parents[0])
            assert content.action == file.action
            assert content.content and content.description == ""
            assert file.license == "CC-BY-4.0" and can_include_content(file.license)

    def test_files_hold_no_text_and_share_their_deposits_fields(self, elements):
        for file in _files(elements):
            deposit = get_element_by_id(elements, file.parents[0])
            assert file.description == ""
            assert file.resource_type == "readme" and file.file_name == "README.pdf"
            assert file.repository == deposit.repository == "figshare"
            assert file.metadata["page_count"] >= 1

    def test_deposits_inventory_every_file_in_them(self, elements):
        inventories = [e.metadata["files"] for e in _deposits(elements)]
        assert all(set(inv) == {"count", "bytes", "by_extension"} for inv in inventories)
        assert sum(inv["by_extension"].get(".pdf", 0) for inv in inventories) == 2
        assert any(".nev" in inv["by_extension"] for inv in inventories)

    def test_compact_dump_round_trips_byte_for_byte(self, raw, elements):
        assert [compact_dump(e) for e in elements] == raw
