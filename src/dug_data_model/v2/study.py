from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import Field

from .base import DugElement, References

STUDY_TYPE = "study"


class DugStudy(DugElement):
    """A research study.

    Its publications are `DugResource`s with `resource_type` 'publication' or 'preprint' in
    `resource_list`; `document_list` and `resource_list` list every document and resource in
    the study, whatever their immediate parent. An earlier version had a `publications` list
    of bare strings; nothing read it, and a file that still carries it loads without it.
    """

    type: Literal["study"] = STUDY_TYPE
    variable_list: Annotated[list[str], References("variable")] = Field(default_factory=list)
    section_list: Annotated[list[str], References("section")] = Field(default_factory=list)
    document_list: Annotated[list[str], References("document")] = Field(default_factory=list)
    resource_list: Annotated[list[str], References("resource")] = Field(default_factory=list)
    abstract: str = ""

    def get_searchable_dict(self) -> dict[str, Any]:
        es_elem = super().get_searchable_dict()
        return {
            **es_elem,
            "variable_list": self.variable_list,
            "section_list": self.section_list,
            "document_list": self.document_list,
            "resource_list": self.resource_list,
            "abstract": self.abstract,
        }
