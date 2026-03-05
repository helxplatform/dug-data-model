from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from .base import DugElement

SECTION_TYPE = "section"


class DugSection(DugElement):
    type: Literal["section"] = SECTION_TYPE
    is_crf: bool = False
    variable_list: list[str] = Field(default_factory=list)

    def get_searchable_dict(self) -> dict[str, Any]:
        es_elem = super().get_searchable_dict()
        return {
            **es_elem,
            "variable_list": self.variable_list,
            "is_crf": self.is_crf,
        }
