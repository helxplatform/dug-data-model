from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import Field

from .base import DugElement, References

STUDY_TYPE = "study"


class DugStudy(DugElement):
    """A research study.

    A study does not list its resources and documents; they name it in `parents`, and
    `build_parent_map()` or a query on `parents` finds them. That is because the study and
    its resources need not come from the same producer (DUG-796: the non-data-dictionary
    producer emits resources and documents for a study the MDS ingest emits), so a list on
    the study would be complete only by luck. Its publications are `DugResource`s with
    `resource_type` 'publication' or 'preprint'. Earlier versions had `publications`, a list
    of bare strings nothing read, then `document_list` and `resource_list`; a file that still
    carries any of them loads without it.
    """

    type: Literal["study"] = STUDY_TYPE
    variable_list: Annotated[list[str], References("variable")] = Field(default_factory=list)
    section_list: Annotated[list[str], References("section")] = Field(default_factory=list)
    abstract: str = ""

    def get_searchable_dict(self) -> dict[str, Any]:
        es_elem = super().get_searchable_dict()
        return {
            **es_elem,
            "variable_list": self.variable_list,
            "section_list": self.section_list,
            "abstract": self.abstract,
        }
