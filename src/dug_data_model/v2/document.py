from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from .base import DugElement

DOCUMENT_TYPE = "document"

DOCUMENT_KINDS: tuple[str, ...] = (
    "publication",
    "preprint",
    "report",
    "protocol",
    "manual",
    "readme",
    "methods",
    "poster",
    "presentation",
    "patent",
    "supplementary_table",
    "other",
)
"""Recommended values for `DugDocument.document_type`.

`document_type` is deliberately a free string, like `DugVariable.data_type`, so that a new
kind of document does not need a model release. Producers should prefer these values.
"""


class DugDocument(DugElement):
    """A textual file attached to a study, such as a README, protocol, report or poster.

    `name` is the display title (the file name when no curated title is known), `description`
    is a summary of the document, and `action` is the URL to link out to. The document's text
    lives in its `DugDocumentSection` children rather than on the document itself, so that
    every piece of text is searchable and annotatable in the same way.
    """

    type: Literal["document"] = DOCUMENT_TYPE

    file_name: str = Field("", description="Original file name, e.g. 'README.pdf'.")
    mime_type: str = Field("", description="IANA media type, e.g. 'application/pdf'.")
    document_type: str = Field(
        "", description="Kind of document; recommended values are listed in DOCUMENT_KINDS."
    )
    authors: list[str] = Field(default_factory=list, description="Author names in citation order.")
    doi: str | None = Field(None, description="Bare DOI of this document, without a resolver prefix.")
    license: str = Field("", description="SPDX licence identifier; empty when unknown.")
    can_display_content: bool = Field(
        False,
        description=(
            "True only when the licence permits showing section text in a user interface; "
            "otherwise the text may be indexed but users should be sent to `action`."
        ),
    )
    section_list: list[str] = Field(
        default_factory=list, description="IDs of this document's DugDocumentSections, in reading order."
    )

    def get_searchable_dict(self) -> dict[str, Any]:
        es_elem = super().get_searchable_dict()
        return {
            **es_elem,
            "file_name": self.file_name,
            "mime_type": self.mime_type,
            "document_type": self.document_type,
            "authors": self.authors,
            "doi": self.doi,
            "license": self.license,
            "can_display_content": self.can_display_content,
            "section_list": self.section_list,
        }
