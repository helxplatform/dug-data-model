"""Tests for dug_data_model.v2.model"""

import pytest
from pydantic import ValidationError

from dug_data_model.v2 import (
    DugElement,
    DugConcept,
    DugVariable,
    DugStudy,
    DugSection,
    DugDocument,
    DugContent,
    DugResource,
    DugCitable,
    DugElementParsedList,
    load_elements,
    serialize_elements,
    VARIABLE_TYPE,
    STUDY_TYPE,
    CONCEPT_TYPE,
    SECTION_TYPE,
    DOCUMENT_TYPE,
    CONTENT_TYPE,
    DOCUMENT_KINDS,
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
        # Its resources and documents name it in `parents`; see the docstring for why.
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


class TestDugDocument:
    def test_default_type(self):
        d = DugDocument(id="d1", name="README", description="")
        assert d.type == DOCUMENT_TYPE

    def test_holds_no_text(self):
        assert "content" not in DugDocument.model_fields

    def test_shares_the_citation_fields_but_is_not_a_resource(self):
        d = DugDocument(id="d1", name="README", description="", repository="zenodo",
                        license="CC-BY-4.0", doi="10.1234/abc")
        assert isinstance(d, DugCitable)
        assert not isinstance(d, DugResource)
        assert d.repository == "zenodo"
        assert "resource_type" not in DugDocument.model_fields

    def test_resources_by_class_are_not_documents(self):
        elements = DugElementParsedList.validate_python([
            {"id": "r1", "name": "Deposit", "description": "", "type": "resource"},
            {"id": "d1", "name": "README", "description": "", "type": "document"},
        ])
        assert [e.id for e in elements if isinstance(e, DugResource)] == ["r1"]
        assert [e.id for e in elements if isinstance(e, DugCitable)] == ["r1", "d1"]

    def test_recommended_kinds_are_not_enforced(self):
        assert "readme" in DOCUMENT_KINDS
        d = DugDocument(id="d1", name="Doc", description="", document_type="lab_notebook")
        assert d.document_type == "lab_notebook"

    def test_a_publication_is_a_resource_and_its_full_text_an_article(self):
        assert "article" in DOCUMENT_KINDS and "data" in DOCUMENT_KINDS
        assert not {"publication", "preprint"} & set(DOCUMENT_KINDS)
        assert {"publication", "preprint"} <= set(RESOURCE_KINDS)

    def test_get_searchable_dict(self):
        d = DugDocument(
            id="d1", name="README", description="", file_name="README.pdf",
            mime_type="application/pdf", document_type="readme", authors=["A. Author"],
            doi="10.1234/abc", license="CC-BY-4.0", studies=["s1"],
        )
        es = d.get_searchable_dict()
        assert es["element_type"] == "document"
        assert es["studies"] == ["s1"]
        assert "resource_type" not in es
        assert es["file_name"] == "README.pdf"
        assert es["mime_type"] == "application/pdf"
        assert es["document_type"] == "readme"
        assert es["authors"] == ["A. Author"]
        assert es["doi"] == "10.1234/abc"
        assert es["license"] == "CC-BY-4.0"
        assert "content" not in es
        assert "content_list" not in es


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

    def test_is_a_dataset_by_default(self):
        r = DugResource(id="r1", name="Dataset", description="A dataset")
        assert r.resource_type == "dataset"
        assert "dataset" in RESOURCE_KINDS

    @pytest.mark.parametrize("resource_type", ["document", " Document "])
    def test_a_resource_cannot_call_itself_a_document(self, resource_type):
        assert "document" not in RESOURCE_KINDS
        with pytest.raises(ValidationError, match="DugDocument"):
            DugResource(id="r1", name="README", description="", resource_type=resource_type)

    def test_repository_slugs_are_recommended_not_enforced(self):
        assert "zenodo" in REPOSITORY_KINDS
        r = DugResource(id="r1", name="Data", description="", repository="lab-server")
        assert r.repository == "lab-server"

    def test_get_searchable_dict(self):
        r = DugResource(
            id="r1", name="Dataset", description="A dataset", repository="zenodo",
            authors=["A. Author"], doi="10.5281/zenodo.1", license="CC0-1.0",
            action="https://zenodo.org/records/1", studies=["s1"],
        )
        es = r.get_searchable_dict()
        assert es["element_type"] == "resource"
        assert es["studies"] == ["s1"]
        assert es["resource_type"] == "dataset"
        assert es["repository"] == "zenodo"
        assert es["authors"] == ["A. Author"]
        assert es["doi"] == "10.5281/zenodo.1"
        assert es["license"] == "CC0-1.0"
        assert not {"document_list", "resource_list"} & set(es)
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
            {"id": "d1", "name": "document1", "description": "desc", "type": "document"},
            {"id": "d1/s", "name": "heading", "description": "", "content": "text",
             "type": "content"},
            {"id": "r1", "name": "resource1", "description": "desc", "type": "resource"},
        ]
        elements = DugElementParsedList.validate_python(data)
        types = {e.type for e in elements}
        assert types == {
            "study", "variable", "concept", "section", "document", "content", "resource",
        }
        assert type(elements[4]) is DugDocument
        assert isinstance(elements[5], DugContent)
        # Documents and resources share DugCitable, but each loads as its own class.
        assert type(elements[6]) is DugResource

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

    def test_roundtrip_document_hierarchy(self, tmp_path):
        original = [
            DugResource(id="r1", name="Dataset", description="desc", doi="10.1/x",
                        parents=["s1"], parent_type="study"),
            DugDocument(id="d1", name="README", description="", mime_type="application/pdf",
                        parents=["r1"], parent_type="resource"),
            DugContent(id="d1/intro", name="Intro", description="", content="Text",
                       position=0, page=1, parents=["d1"], parent_type="document"),
        ]
        path = tmp_path / "out.json"
        serialize_elements(original, path)
        restored = load_elements(path, DugElementParsedList)
        assert restored == original
        assert [type(e) for e in restored] == [DugResource, DugDocument, DugContent]


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
