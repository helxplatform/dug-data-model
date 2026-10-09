from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import Field

from .base import References
from .citable import DugCitable

DOCUMENT_TYPE = "document"

DOCUMENT_KINDS: tuple[str, ...] = (
    "article",
    "report",
    "protocol",
    "manual",
    "readme",
    "methods",
    "poster",
    "presentation",
    "patent",
    "supplementary_table",
    "press_release",
    "data",
    "other",
)
"""Recommended values for `DugDocument.document_type`.

`document_type` is deliberately a free string, like `DugVariable.data_type`, so that a new
kind of document does not need a model release. Producers should prefer these values.

'article' is the full text of a publication or preprint; which of the two, the document's
parent `DugResource` says in its `resource_type`, so neither is a document kind. 'data' is a
data file (a spreadsheet, an archive, a recording) that a producer chose to list as a document.
"""


class DugDocument(DugCitable):
    """One file in one format: a README, a protocol PDF, a paper's PDF, a data XLSX, ...

    A `DugResource` is the thing with a URL (a deposit, a publication, a web page); a document
    is one file of it. Its parent is that resource or, when it came from no known resource,
    its study. Like a resource, a document has a title (`name`), a summary (`description`), a
    landing or download URL (`action`), and the citation fields `repository`, `authors`, `doi`
    and `license`, which both get from `DugCitable`; it adds what only a file has:
    `file_name`, `mime_type` and `document_type`. A web page captured as text is a document
    with `mime_type="text/html"` and no `file_name`, under the page's resource. A document is
    not a resource: `isinstance(x, DugResource)` is false for it, so code that picks out
    deposits by class does not pick up their files too.

    A document holds no text of its own. Whatever could be read out of the file lives in its
    `DugContent` children (`content_list`), so that every piece of text is searchable and
    annotatable in the same way. The document's `license` decides whether there is any
    content at all: a producer emits content only when the licence allows the text to be
    incorporated (`can_include_content()` in `licenses.py`). A document is still a document
    when it has no content, whether because its text could not be read -- a scanned PDF, or a
    file the curator named that no parser handles -- or because its licence does not allow
    it: it is listed and linked to, and found by its title and description. Whether a producer
    emits a document for every file in a deposit, or only for the ones a person would read, is
    the producer's choice: the reference producer inventories data files (recordings, scans,
    spreadsheets of primary data) in the resource's `metadata` and emits no document for them.
    """

    type: Literal["document"] = DOCUMENT_TYPE

    file_name: str = Field("", description="Original file name, e.g. 'README.pdf'.")
    mime_type: str = Field("", description="IANA media type, e.g. 'application/pdf'.")
    document_type: str = Field(
        "", description="Kind of document; recommended values are listed in DOCUMENT_KINDS."
    )
    content_list: Annotated[list[str], References("content", children=True)] = Field(
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
