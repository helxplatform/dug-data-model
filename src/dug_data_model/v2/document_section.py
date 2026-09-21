from __future__ import annotations

from typing import Any, Literal, override

from pydantic import Field, computed_field

from .base import DugElement

DOCUMENT_SECTION_TYPE = "document_section"


class DugDocumentSection(DugElement):
    """A headed section of a `DugDocument`.

    `name` is the heading and `description` is the body text under it. `parents` holds the ID
    of the containing document, with `parent_type` set to 'document'.
    """

    type: Literal["document_section"] = DOCUMENT_SECTION_TYPE

    position: int = Field(0, ge=0, description="0-based order of this section within its document.")
    level: int | None = Field(
        None, description="Heading depth (1 = top level) when the source format exposes it."
    )
    page: int | None = Field(
        None, description="1-based page this section starts on, for paginated formats."
    )

    @override
    @computed_field
    @property
    def ml_ready_desc(self) -> str:
        """Return the heading and the body text together, as the heading is part of the meaning."""
        if self.name and self.description:
            return f"{self.name}: {self.description}"
        return self.name or self.description

    def get_searchable_dict(self) -> dict[str, Any]:
        es_elem = super().get_searchable_dict()
        return {
            **es_elem,
            "position": self.position,
            "level": self.level,
            "page": self.page,
        }
