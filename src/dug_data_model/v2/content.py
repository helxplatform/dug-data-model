from __future__ import annotations

from typing import Any, Literal, override

from pydantic import Field, computed_field

from .base import DugElement

CONTENT_TYPE = "content"


class DugContent(DugElement):
    """A piece of a `DugDocument`'s text: a heading and the body under it.

    Content is the only element that holds a document's text. A `DugDocument` describes and
    links to a file; if the file's text can be read, it is split into DugContent children, one
    per heading (or a single one when there are no headings). `name` is the heading and
    `description` is the text. `parents` holds the ID of the containing document, with
    `parent_type` set to 'document'.

    Because content is the only element with anything to display, it is also the only one
    that carries `can_display_content`. Producers set it from the document's licence; the
    document itself does not repeat it.
    """

    type: Literal["content"] = CONTENT_TYPE

    position: int = Field(0, ge=0, description="0-based order of this content within its document.")
    level: int | None = Field(
        None, description="Heading depth (1 = top level) when the source format exposes it."
    )
    page: int | None = Field(
        None, description="1-based page this content starts on, for paginated formats."
    )
    can_display_content: bool = Field(
        False,
        description=(
            "True only when the licence permits showing the text in a user interface. When "
            "False, the text is indexed but left out of API responses and users should be "
            "sent to `action` instead."
        ),
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
            "can_display_content": self.can_display_content,
        }

    def get_response_dict(self) -> dict[str, Any]:
        """Return the API response, with the body text blanked unless it may be displayed."""
        response = super().get_response_dict()
        if not self.can_display_content:
            response["description"] = ""
        return response
