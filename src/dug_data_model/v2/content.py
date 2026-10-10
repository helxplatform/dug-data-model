from __future__ import annotations

from typing import Annotated, Any, Literal, override

from pydantic import Field, computed_field

from .base import DugElement, References

CONTENT_TYPE = "content"


class DugContent(DugElement):
    """A piece of a `DugDocument`'s text: a heading and the body under it.

    Content is the only element that holds a document's text. A `DugDocument` describes and
    links to a file; if the file's text can be read, and the document's licence allows the
    text to be incorporated, it is split into DugContent children, one per heading (or a
    single one when there are no headings). `name` is the heading and `content` is the text
    under it. `description` is metadata about the piece, as on every other element, and is
    usually empty. `parents` holds the ID of the containing document, with `parent_type` set
    to 'document'; `studies` holds the ID of the study, as on `DugCitable`, so that the study
    can be found without climbing through the document.

    Content carries no licence or display flag of its own: the licence is stated once, on the
    document, and content exists only when that licence permits it (see `licenses.py`). A
    document whose text may not be incorporated has no content, so the case shows in the
    shape of the data rather than in a flag that an index or a UI has to remember to honour.
    """

    type: Literal["content"] = CONTENT_TYPE

    position: int = Field(0, ge=0, description="0-based order of this content within its document.")
    level: int | None = Field(
        None, ge=1, description="Heading depth (1 = top level) when the source format exposes it."
    )
    page: int | None = Field(
        None, ge=1, description="1-based page this content starts on, for paginated formats."
    )
    content: str = Field(
        description=(
            "The text under the heading. Required, so that a file written when the text was "
            "held in `description` fails to load instead of loading with no text."
        )
    )
    studies: Annotated[list[str], References("study")] = Field(
        default_factory=list,
        description="IDs of the studies this content belongs to, as on DugCitable.",
    )

    @override
    @computed_field
    @property
    def ml_ready_desc(self) -> str:
        """Return the heading and the body text together, as the heading is part of the meaning."""
        if self.name and self.content:
            return f"{self.name}: {self.content}"
        return self.name or self.content

    def get_searchable_dict(self) -> dict[str, Any]:
        es_elem = super().get_searchable_dict()
        return {
            **es_elem,
            "position": self.position,
            "level": self.level,
            "page": self.page,
            "content": self.content,
            "studies": self.studies,
        }
