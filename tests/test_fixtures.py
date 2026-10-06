"""A real producer output, loaded and checked end to end.

tests/fixtures/heal_hdp00009.json is HEAL study HDP00009 as written by the reference producer,
heal-data-stewards/heal-non-data-dictionaries: a copy of its examples/HDP00009/HDP00009.json
(commit 8b52af1, on the model-conventions branch): one study, two Figshare deposits
as resources, one PDF README in each as a document with a single content element, and a file
inventory on each resource. The extracted text is CC-BY-4.0, from Min Gon Kim, Kai Yu, Bin He et
al. and Kai Yu, Samantha Schmitt, Bin He et al. (Carnegie Mellon University). It is a frozen
example of the shape, refreshed when the model changes, not a contract with that producer.
Since that commit it has been re-written with this package's compact_dump(), which now always
writes fields whose default says something (`resource_type`, `position`).
"""

import json
from pathlib import Path

import pytest
from dug_data_model.v2 import (
    CONTENT_TYPE,
    DOCUMENT_TYPE,
    RESOURCE_TYPE,
    DugDocument,
    DugElementParsedList,
    DugResource,
    DugStudy,
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


class TestRealOutput:
    def test_loads_with_every_type_in_the_document_hierarchy(self, elements):
        assert count_by_type(elements) == {"study": 1, "resource": 2, "document": 2, "content": 2}
        assert [type(e) for e in elements[:2]] == [DugStudy, DugResource]

    def test_ids_are_unique_and_every_reference_resolves(self, elements):
        validate_unique_ids(elements)
        validate_references(elements)

    def test_parent_chain_is_content_document_resource_study(self, elements):
        study = elements[0]
        for content in filter_by_type(elements, CONTENT_TYPE):
            document = get_element_by_id(elements, content.parents[0])
            assert isinstance(document, DugDocument) and content.parent_type == "document"
            resource = get_element_by_id(elements, document.parents[0])
            assert type(resource) is DugResource and document.parent_type == "resource"
            assert resource.parents == [study.id] and resource.parent_type == "study"
            assert content.id in document.content_list
            assert document.id in resource.document_list
            assert document.id in study.document_list

    def test_content_carries_its_documents_action_and_display_flag(self, elements):
        for content in filter_by_type(elements, CONTENT_TYPE):
            document = get_element_by_id(elements, content.parents[0])
            assert content.action == document.action
            assert document.license == "CC-BY-4.0"
            assert content.can_display_content is True

    def test_documents_hold_no_text_and_share_their_resources_fields(self, elements):
        for document in filter_by_type(elements, DOCUMENT_TYPE):
            resource = get_element_by_id(elements, document.parents[0])
            assert document.description == ""
            assert document.repository == resource.repository == "figshare"
            assert document.mime_type == "application/pdf"
            assert document.metadata["page_count"] >= 1

    def test_resources_inventory_every_file_in_the_deposit(self, elements):
        inventories = [e.metadata["files"] for e in filter_by_type(elements, RESOURCE_TYPE)]
        assert all(set(inv) == {"count", "bytes", "by_extension"} for inv in inventories)
        assert sum(inv["by_extension"].get(".pdf", 0) for inv in inventories) == 2
        assert any(".nev" in inv["by_extension"] for inv in inventories)

    def test_compact_dump_round_trips_byte_for_byte(self, raw, elements):
        assert [compact_dump(e) for e in elements] == raw
