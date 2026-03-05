from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from .base import DugElement

STUDY_TYPE = "study"


class DugStudy(DugElement):
    type: Literal["study"] = STUDY_TYPE
    publications: list[str] = Field(default_factory=list)
    variable_list: list[str] = Field(default_factory=list)
    section_list: list[str] = Field(default_factory=list)
    abstract: str = ""

    def get_searchable_dict(self) -> dict[str, Any]:
        es_elem = super().get_searchable_dict()
        return {
            **es_elem,
            "publications": self.publications,
            "variable_list": self.variable_list,
            "section_list": self.section_list,
            "abstract": self.abstract,
        }
