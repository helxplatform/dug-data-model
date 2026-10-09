from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import Field, field_validator

from .base import References
from .citable import DugCitable

RESOURCE_TYPE = "resource"

RESOURCE_KINDS: tuple[str, ...] = (
    "dataset",
    "software",
    "publication",
    "preprint",
    "website",
    "other",
)
"""Recommended values for `DugResource.resource_type`.

A publication or preprint is a resource: the work, with its DOI, landing page and authors. The
PDF or HTML of its full text is a `DugDocument` under it, with `document_type="article"`, so
'publication' and 'preprint' are resource kinds and not document kinds.

'document' is not one of them, and `DugResource` rejects it: a single file is a `DugDocument`,
and a resource calling itself a document would be found by a filter on `resource_type` but not
by one on the element type.
"""

REPOSITORY_KINDS: tuple[str, ...] = (
    "figshare",
    "zenodo",
    "dataverse",
    "osf",
    "openneuro",
    "mendeley-data",
    "github",
    "sparc",
    "pennsieve",
)
"""Recommended values for `DugCitable.repository`, which resources and documents share: one
lower-case slug per repository.

A free string like `resource_type`, so a new repository does not need a model release, but
producers that infer the repository from a URL or DOI prefix should map to these slugs so
that a filter on `repository` finds every deposit from the same place.
"""


class DugResource(DugCitable):
    """Anything outside Dug that has a URL, at whatever size.

    A program website, a project's page on an NIH site, a press release, a Zenodo community,
    the Zenodo or Figshare deposit a study's files came from, a dataset with or without a DOI,
    a publication: each is a resource. `name` is its title, `description` its description,
    `action` its landing page; a resource with a DOI is citable. The dividing line from a
    `DugDocument` is format: a resource is the thing, a document is one file of it in one
    format. A deposit's README, a paper's PDF, a dataset's XLSX and the HTML of a press release
    are documents, which share the citation fields (`repository`, `authors`, `doi`, `license`)
    through `DugCitable` but are not resources.
    """

    type: Literal["resource"] = RESOURCE_TYPE

    resource_type: str = Field(
        "dataset", description="Kind of resource; recommended values are listed in RESOURCE_KINDS."
    )
    document_list: Annotated[list[str], References("document", children=True)] = Field(
        default_factory=list, description="IDs of the DugDocuments that came from this resource."
    )

    @field_validator("resource_type")
    @classmethod
    def _not_a_document(cls, value: str) -> str:
        if value.strip().casefold() == "document":
            raise ValueError("a single file is a DugDocument (type 'document'), not a DugResource")
        return value

    def get_searchable_dict(self) -> dict[str, Any]:
        es_elem = super().get_searchable_dict()
        return {
            **es_elem,
            "resource_type": self.resource_type,
            "document_list": self.document_list,
        }
