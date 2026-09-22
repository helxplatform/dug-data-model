"""Tests for dug_data_model.v2.model"""

import pytest
from dug_data_model.v2 import (
    DugElement,
    DugConcept,
    DugVariable,
    DugStudy,
    DugSection,
    DugDocument,
    DugDocumentSection,
    DugResource,
    DugElementParsedList,
    VARIABLE_TYPE,
    STUDY_TYPE,
    CONCEPT_TYPE,
    SECTION_TYPE,
    DOCUMENT_TYPE,
    DOCUMENT_SECTION_TYPE,
    DOCUMENT_KINDS,
    RESOURCE_TYPE,
    RESOURCE_KINDS,
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

    def test_document_and_resource_lists(self):
        s = DugStudy(id="s1", name="Study", description="A study",
                     document_list=["d1"], resource_list=["r1"])
        d = s.get_searchable_dict()
        assert d["document_list"] == ["d1"]
        assert d["resource_list"] == ["r1"]


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

    def test_content_is_not_displayable_by_default(self):
        d = DugDocument(id="d1", name="README", description="")
        assert d.can_display_content is False
        assert d.license == ""
        assert d.doi is None

    def test_recommended_kinds_are_not_enforced(self):
        assert "readme" in DOCUMENT_KINDS
        d = DugDocument(id="d1", name="Doc", description="", document_type="lab_notebook")
        assert d.document_type == "lab_notebook"

    def test_get_searchable_dict(self):
        d = DugDocument(
            id="d1", name="README", description="", file_name="README.pdf",
            mime_type="application/pdf", document_type="readme", authors=["A. Author"],
            doi="10.1234/abc", license="CC-BY-4.0", can_display_content=True,
            section_list=["d1/intro"],
        )
        es = d.get_searchable_dict()
        assert es["element_type"] == "document"
        assert es["file_name"] == "README.pdf"
        assert es["mime_type"] == "application/pdf"
        assert es["document_type"] == "readme"
        assert es["authors"] == ["A. Author"]
        assert es["doi"] == "10.1234/abc"
        assert es["license"] == "CC-BY-4.0"
        assert es["can_display_content"] is True
        assert es["section_list"] == ["d1/intro"]


class TestDugDocumentSection:
    def test_default_type(self):
        s = DugDocumentSection(id="d1/intro", name="Intro", description="Text")
        assert s.type == DOCUMENT_SECTION_TYPE

    def test_ml_ready_desc_joins_heading_and_text(self):
        s = DugDocumentSection(id="d1/intro", name="Methods", description="We did things.")
        assert s.ml_ready_desc == "Methods: We did things."

    def test_ml_ready_desc_with_empty_body(self):
        s = DugDocumentSection(id="d1/intro", name="Methods", description="")
        assert s.ml_ready_desc == "Methods"

    def test_ml_ready_desc_with_empty_heading(self):
        s = DugDocumentSection(id="d1/intro", name="", description="We did things.")
        assert s.ml_ready_desc == "We did things."

    def test_negative_position_rejected(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            DugDocumentSection(id="x", name="x", description="x", position=-1)

    def test_get_searchable_dict(self):
        s = DugDocumentSection(id="d1/intro", name="Intro", description="Text",
                               position=2, level=1, page=3)
        es = s.get_searchable_dict()
        assert es["element_type"] == "document_section"
        assert es["position"] == 2
        assert es["level"] == 1
        assert es["page"] == 3
        assert es["can_display_content"] is False

    def test_response_withholds_text_by_default(self):
        s = DugDocumentSection(id="d1/intro", name="Intro", description="Text")
        assert s.get_searchable_dict()["description"] == "Text"
        response = s.get_response_dict()
        assert response["description"] == ""
        assert response["name"] == "Intro"

    def test_response_includes_text_when_displayable(self):
        s = DugDocumentSection(id="d1/intro", name="Intro", description="Text",
                               can_display_content=True)
        assert s.get_response_dict()["description"] == "Text"


class TestDugResource:
    def test_default_type(self):
        r = DugResource(id="r1", name="Dataset", description="A dataset")
        assert r.type == RESOURCE_TYPE

    def test_is_a_dataset_by_default(self):
        r = DugResource(id="r1", name="Dataset", description="A dataset")
        assert r.resource_type == "dataset"
        assert "dataset" in RESOURCE_KINDS

    def test_get_searchable_dict(self):
        r = DugResource(
            id="r1", name="Dataset", description="A dataset", repository="zenodo",
            authors=["A. Author"], doi="10.5281/zenodo.1", license="CC0-1.0",
            document_list=["d1"], action="https://zenodo.org/records/1",
        )
        es = r.get_searchable_dict()
        assert es["element_type"] == "resource"
        assert es["resource_type"] == "dataset"
        assert es["repository"] == "zenodo"
        assert es["authors"] == ["A. Author"]
        assert es["doi"] == "10.5281/zenodo.1"
        assert es["license"] == "CC0-1.0"
        assert es["document_list"] == ["d1"]
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
            {"id": "d1/s", "name": "heading", "description": "desc", "type": "document_section"},
            {"id": "r1", "name": "resource1", "description": "desc", "type": "resource"},
        ]
        elements = DugElementParsedList.validate_python(data)
        types = {e.type for e in elements}
        assert types == {
            "study", "variable", "concept", "section", "document", "document_section", "resource",
        }
        assert isinstance(elements[4], DugDocument)
        assert isinstance(elements[5], DugDocumentSection)
        assert isinstance(elements[6], DugResource)

    def test_wrong_type_raises(self):
        from pydantic import ValidationError
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

    def test_roundtrip_document_hierarchy(self):
        import json
        original = [
            DugResource(id="r1", name="Dataset", description="desc", doi="10.1/x",
                        document_list=["d1"], parents=["s1"], parent_type="study"),
            DugDocument(id="d1", name="README", description="", mime_type="application/pdf",
                        section_list=["d1/intro"], parents=["r1"], parent_type="resource"),
            DugDocumentSection(id="d1/intro", name="Intro", description="Text", position=0,
                               page=1, parents=["d1"], parent_type="document"),
        ]
        restored = DugElementParsedList.validate_python(
            json.loads(json.dumps([e.model_dump() for e in original]))
        )
        assert restored == original
