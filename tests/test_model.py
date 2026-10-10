"""Tests for dug_data_model.v2.model"""

import pytest
from pydantic import ValidationError

from dug_data_model.v2 import (
    DugElement,
    DugConcept,
    DugVariable,
    DugStudy,
    DugSection,
    DugContent,
    DugResource,
    DugElementParsedList,
    load_elements,
    serialize_elements,
    VARIABLE_TYPE,
    STUDY_TYPE,
    CONCEPT_TYPE,
    SECTION_TYPE,
    CONTENT_TYPE,
    RESOURCE_TYPE,
    RESOURCE_KINDS,
    REPOSITORY_KINDS,
    CONTENT_LICENSES,
    can_include_content,
)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestDugVariable:
    def test_default_type(self):
        v = DugVariable(id="v1", name="BMI", description="Body mass index")
        assert v.type == VARIABLE_TYPE

    def test_ml_ready_desc_plain_name(self):
        v = DugVariable(id="v1", name="BMI", description="Body mass index")
        assert v.ml_ready_desc == "BMI: Body mass index"

    def test_ml_ready_desc_camel_case(self):
        v = DugVariable(id="v1", name="bodyMassIndex", description="Body mass index")
        assert "body Mass Index" in v.ml_ready_desc

    def test_ml_ready_desc_snake_case(self):
        v = DugVariable(id="v1", name="body_mass_index", description="Body mass index")
        assert "body mass index" in v.ml_ready_desc

    def test_get_searchable_dict_includes_data_type(self):
        v = DugVariable(id="v1", name="BMI", description="desc", data_type="decimal")
        d = v.get_searchable_dict()
        assert d["data_type"] == "decimal"
        assert d["is_cde"] is False


class TestDugStudy:
    def test_default_type(self):
        s = DugStudy(id="s1", name="Study", description="A study")
        assert s.type == STUDY_TYPE

    def test_get_searchable_dict(self):
        s = DugStudy(id="s1", name="Study", description="A study", abstract="Abstract text")
        d = s.get_searchable_dict()
        assert d["abstract"] == "Abstract text"
        assert "variable_list" in d
        assert "section_list" in d

    def test_lists_no_publications_resources_or_documents(self):
        # Its resources name it in `parents`; see the docstring for why.
        dropped = {"publications", "document_list", "resource_list"}
        assert not dropped & set(DugStudy.model_fields)
        s = DugStudy.model_validate({"id": "s1", "name": "Study", "description": "",
                                     "publications": ["10.1234/abc"], "resource_list": ["r1"],
                                     "document_list": ["d1"]})  # an old file still loads
        assert not dropped & set(s.get_searchable_dict())


class TestDugConcept:
    def test_default_type(self):
        c = DugConcept(id="c1", name="Concept", description="A concept")
        assert c.type == CONCEPT_TYPE

    def test_get_searchable_dict_has_identifiers(self):
        c = DugConcept(id="c1", name="Concept", description="A concept")
        d = c.get_searchable_dict()
        assert "identifiers" in d
        assert "concept_type" in d


class TestDugSection:
    def test_default_type(self):
        s = DugSection(id="sec1", name="Section", description="A section")
        assert s.type == SECTION_TYPE

    def test_is_crf_default(self):
        s = DugSection(id="sec1", name="Section", description="A section")
        assert s.is_crf is False

    def test_get_searchable_dict(self):
        s = DugSection(
            id="sec1", name="Section", description="A section",
            is_crf=True, variable_list=["v1", "v2"]
        )
        d = s.get_searchable_dict()
        assert d["is_crf"] is True
        assert d["variable_list"] == ["v1", "v2"]


class TestDugContent:
    def test_default_type(self):
        c = DugContent(id="d1/intro", name="Intro", description="", content="Text")
        assert c.type == CONTENT_TYPE

    def test_text_is_required(self):
        # A file from when the text was held in `description` must not load with no text.
        with pytest.raises(ValidationError):
            DugContent(id="d1/intro", name="Intro", description="Text")

    def test_has_no_display_flag_or_licence_of_its_own(self):
        assert "can_display_content" not in DugContent.model_fields
        assert "license" not in DugContent.model_fields

    def test_its_parent_is_a_resource(self):
        DugContent(id="r/h", name="H", description="", content="t", parents=["r"],
                   parent_type="resource")
        DugContent(id="r/h", name="H", description="", content="t")  # no parent yet
        with pytest.raises(ValidationError, match="parent_type is 'resource'"):
            DugContent(id="r/h", name="H", description="", content="t", parents=["d"],
                       parent_type="document")

    @pytest.mark.parametrize("name, content, expected", [
        ("Methods", "We did things.", "Methods: We did things."),
        ("Methods", "", "Methods"),
        ("", "We did things.", "We did things."),
    ])
    def test_ml_ready_desc_joins_heading_and_text(self, name, content, expected):
        c = DugContent(id="d1/intro", name=name, description="ignored", content=content)
        assert c.ml_ready_desc == expected

    def test_level_and_page_are_one_based(self):
        DugContent(id="x", name="x", description="", content="x", level=1, page=1)

    @pytest.mark.parametrize("bad", [{"position": -1}, {"level": 0}, {"page": 0}])
    def test_out_of_range_position_level_or_page_rejected(self, bad):
        with pytest.raises(ValidationError):
            DugContent(id="x", name="x", description="", content="x", **bad)

    def test_searchable_and_response_dicts_carry_the_text(self):
        c = DugContent(id="d1/intro", name="Intro", description="", content="Text",
                       position=2, level=1, page=3, studies=["s1"])
        es = c.get_searchable_dict()
        assert es["element_type"] == "content"
        assert es["studies"] == ["s1"]
        assert es["position"] == 2
        assert es["level"] == 1
        assert es["page"] == 3
        assert es["content"] == "Text"
        assert es["description"] == ""
        assert "can_display_content" not in es
        assert c.get_response_dict()["content"] == "Text"


class TestDugResource:
    def test_default_type(self):
        r = DugResource(id="r1", name="Dataset", description="A dataset")
        assert r.type == RESOURCE_TYPE

    def test_kind_is_unknown_by_default(self):
        # "dataset" was the default when every resource was a deposit; a file would be
        # mis-typed by it, so an unset kind is now empty, and compact_dump() leaves it out.
        r = DugResource(id="r1", name="Dataset", description="A dataset")
        assert r.resource_type == ""
        assert "dataset" in RESOURCE_KINDS

    def test_recommended_kinds_are_not_enforced(self):
        assert "readme" in RESOURCE_KINDS
        r = DugResource(id="r1", name="Notebook", description="", resource_type="lab_notebook")
        assert r.resource_type == "lab_notebook"

    def test_a_file_is_a_resource_with_a_format(self):
        page = DugResource(id="r1", name="Deposit", description="", resource_type="dataset")
        pdf = DugResource(id="r1/readme", name="README", description="", resource_type="readme",
                          file_name="README.pdf", mime_type="application/pdf",
                          parents=["r1"], parent_type="resource")
        assert page.file_name == page.mime_type == ""
        assert type(page) is type(pdf) is DugResource
        assert "content" not in DugResource.model_fields

    def test_a_files_kind_matches_its_parents_when_it_is_the_whole_thing(self):
        # The convention that replaces an is_full_text flag and the old 'article' kind.
        assert "article" not in RESOURCE_KINDS
        assert {"publication", "preprint", "supplementary_table", "readme"} <= set(RESOURCE_KINDS)
        paper = DugResource(id="p", name="Paper", description="", resource_type="publication",
                            doi="10.1234/abc", parents=["s1"], parent_type="study")
        full_text = DugResource(id="p/pdf", name="Paper (PDF)", description="",
                                resource_type="publication", mime_type="application/pdf",
                                parents=["p"], parent_type="resource")
        table = DugResource(id="p/s1", name="Table S1", description="",
                            resource_type="supplementary_table", mime_type="text/csv",
                            parents=["p"], parent_type="resource")
        assert full_text.resource_type == paper.resource_type != table.resource_type

    def test_a_document_is_no_longer_a_type(self):
        assert "document" not in RESOURCE_KINDS
        with pytest.raises(ValidationError):
            DugElementParsedList.validate_python(
                [{"id": "d1", "name": "README", "description": "", "type": "document"}]
            )

    def test_repository_slugs_are_recommended_not_enforced(self):
        assert "zenodo" in REPOSITORY_KINDS
        r = DugResource(id="r1", name="Data", description="", repository="lab-server")
        assert r.repository == "lab-server"

    def test_get_searchable_dict(self):
        r = DugResource(
            id="r1", name="Dataset", description="A dataset", resource_type="dataset",
            repository="zenodo", authors=["A. Author"], doi="10.5281/zenodo.1",
            license="CC0-1.0", file_name="data.zip", mime_type="application/zip",
            action="https://zenodo.org/records/1", studies=["s1"],
        )
        es = r.get_searchable_dict()
        assert es["element_type"] == "resource"
        assert es["resource_type"] == "dataset"
        assert es["repository"] == "zenodo"
        assert es["authors"] == ["A. Author"]
        assert es["doi"] == "10.5281/zenodo.1"
        assert es["license"] == "CC0-1.0"
        assert es["file_name"] == "data.zip"
        assert es["mime_type"] == "application/zip"
        assert es["studies"] == ["s1"]
        assert not {"document_list", "resource_list", "content"} & set(es)
        assert es["action"] == "https://zenodo.org/records/1"


# ---------------------------------------------------------------------------
# DugElement shared behaviour
# ---------------------------------------------------------------------------

class TestDugElement:
    def test_add_parent(self):
        v = DugVariable(id="v1", name="var", description="desc")
        v.add_parent("study_1")
        assert "study_1" in v.parents

    def test_add_program_name(self):
        v = DugVariable(id="v1", name="var", description="desc")
        v.add_program_name("NHLBI")
        assert "NHLBI" in v.programs

    def test_add_metadata(self):
        v = DugVariable(id="v1", name="var", description="desc")
        v.add_metadata({"key": "value"})
        assert v.metadata["key"] == "value"

    def test_clean_deduplicates(self):
        v = DugVariable(id="v1", name="var", description="desc",
                        search_terms=["b", "a", "a"])
        v.clean()
        assert v.search_terms == ["a", "b"]

    def test_get_response_dict_hides_terms(self):
        v = DugVariable(id="v1", name="var", description="desc",
                        search_terms=["term"])
        d = v.get_response_dict()
        assert "search_terms" not in d
        assert "optional_terms" not in d

    def test_jsonable_returns_dict(self):
        v = DugVariable(id="v1", name="var", description="desc")
        assert isinstance(v.jsonable(), dict)

    def test_str_is_json(self):
        import json
        v = DugVariable(id="v1", name="var", description="desc")
        parsed = json.loads(str(v))
        assert parsed["id"] == "v1"

    def test_add_tag(self):
        v = DugVariable(id="v1", name="var", description="desc")
        v.add_tag("category", "value")
        assert len(v.tags) == 1
        assert v.tags[0] == {"category": "category", "value": "value"}

    def test_tags_in_searchable_dict(self):
        v = DugVariable(id="v1", name="var", description="desc")
        v.add_tag("category", "value")
        d = v.get_searchable_dict()
        assert "tags" in d
        assert d["tags"] == [{"category": "category", "value": "value"}]

    def test_get_id(self):
        v = DugVariable(id="v1", name="var", description="desc")
        assert v.get_id() == "v1"

    def test_element_type_in_searchable_dict(self):
        v = DugVariable(id="v1", name="var", description="desc")
        d = v.get_searchable_dict()
        assert d["element_type"] == "variable"


# ---------------------------------------------------------------------------
# Discriminated-union deserialization
# ---------------------------------------------------------------------------

class TestDugElementParsedList:
    def test_mixed_list(self):
        data = [
            {"id": "s1", "name": "Study 1", "description": "desc", "type": "study"},
            {"id": "v1", "name": "var1", "description": "desc", "type": "variable"},
            {"id": "c1", "name": "concept1", "description": "desc", "type": "concept"},
            {"id": "sec1", "name": "section1", "description": "desc", "type": "section"},
            {"id": "r1", "name": "resource1", "description": "desc", "type": "resource"},
            {"id": "r1/s", "name": "heading", "description": "", "content": "text",
             "type": "content"},
        ]
        elements = DugElementParsedList.validate_python(data)
        types = {e.type for e in elements}
        assert types == {"study", "variable", "concept", "section", "resource", "content"}
        assert type(elements[4]) is DugResource
        assert isinstance(elements[5], DugContent)

    def test_wrong_type_raises(self):
        data = [{"id": "x", "name": "x", "description": "x", "type": "unknown"}]
        with pytest.raises(ValidationError):
            DugElementParsedList.validate_python(data)

    def test_empty_list(self):
        elements = DugElementParsedList.validate_python([])
        assert elements == []

    def test_roundtrip_serialization(self):
        import json
        original = [
            DugVariable(id="v1", name="Var", description="desc", data_type="integer"),
            DugStudy(id="s1", name="Study", description="desc", abstract="text"),
        ]
        # Serialize to JSON
        json_data = [e.model_dump() for e in original]
        json_str = json.dumps(json_data)
        # Parse back
        parsed_data = json.loads(json_str)
        restored = DugElementParsedList.validate_python(parsed_data)
        # Verify
        assert len(restored) == 2
        assert restored[0].id == "v1"
        assert restored[0].data_type == "integer"
        assert restored[1].id == "s1"
        assert restored[1].abstract == "text"

    def test_roundtrip_resource_tree(self, tmp_path):
        original = [
            DugResource(id="r1", name="Dataset", description="desc", doi="10.1/x",
                        resource_type="dataset", parents=["s1"], parent_type="study",
                        studies=["s1"]),
            DugResource(id="r1/readme", name="README", description="", resource_type="readme",
                        mime_type="application/pdf", parents=["r1"], parent_type="resource",
                        studies=["s1"]),
            DugContent(id="r1/readme/intro", name="Intro", description="", content="Text",
                       position=0, page=1, parents=["r1/readme"], parent_type="resource",
                       studies=["s1"]),
        ]
        path = tmp_path / "out.json"
        serialize_elements(original, path)
        restored = load_elements(path, DugElementParsedList)
        assert restored == original
        assert [type(e) for e in restored] == [DugResource, DugResource, DugContent]


class TestCanIncludeContent:
    def test_listed_licences_are_spdx_identifiers(self):
        assert {"CC0-1.0", "CC-BY-4.0", "CC-BY-SA-4.0"} <= CONTENT_LICENSES

    @pytest.mark.parametrize("license", [
        "CC0-1.0", "CC-BY-4.0", "CC-BY-SA-4.0",
        # Matching ignores case and surrounding whitespace.
        "cc-by-4.0", "Cc0-1.0", " CC-BY-SA-4.0\n",
    ])
    def test_permissive_licences_allow_content(self, license):
        assert can_include_content(license) is True

    @pytest.mark.parametrize("license", [
        "CC-BY-NC-4.0", "CC-BY-ND-4.0", "cc-by-nc-4.0", "LicenseRef-all-rights-reserved", "",
    ])
    def test_restrictive_unknown_or_missing_licence_does_not(self, license):
        assert can_include_content(license) is False
