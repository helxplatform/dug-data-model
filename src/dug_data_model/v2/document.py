from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from .resource import DugResource

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


class DugDocument(DugResource):
    """A `DugResource` that is a single file: a README, protocol, report, poster, ...

    A repository deposit is a resource; one file in it is a document. Being a resource, a
    document has a title (`name`), a summary (`description`), a landing or download URL
    (`action`), and the citable `repository`, `authors`, `doi` and `license` fields; it adds
    what only a file has: `file_name`, `mime_type` and `document_type`. Its `resource_type`
    is always 'document', and `document_list`, inherited from the resource, is normally empty.

    A document holds no text of its own. Whatever could be read out of the file lives in its
    `DugContent` children (`content_list`), so that every piece of text is searchable and
    annotatable in the same way, and so that whether text may be shown is decided once, on the
    content that would be shown. A file in a format nothing can read is still a document: it
    is listed and linked to, with no content.
    """

    type: Literal["document"] = DOCUMENT_TYPE

    resource_type: str = Field("document", description="Always 'document' for a DugDocument.")
    file_name: str = Field("", description="Original file name, e.g. 'README.pdf'.")
    mime_type: str = Field("", description="IANA media type, e.g. 'application/pdf'.")
    document_type: str = Field(
        "", description="Kind of document; recommended values are listed in DOCUMENT_KINDS."
    )
    content_list: list[str] = Field(
        default_factory=list, description="IDs of this document's DugContent, in reading order."
    )

    def get_searchable_dict(self) -> dict[str, Any]:
        es_elem = super().get_searchable_dict()
        return {
            **es_elem,
            "file_name": self.file_name,
            "mime_type": self.mime_type,
            "document_type": self.document_type,
            "content_list": self.content_list,
        }
