from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from .base import DugElement

RESOURCE_TYPE = "resource"

RESOURCE_KINDS: tuple[str, ...] = (
    "dataset",
    "software",
    "publication",
    "website",
    "document",
    "other",
)
"""Recommended values for `DugResource.resource_type`.

'document' is what a `DugDocument` -- a resource that is a single file -- always has.
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
"""Recommended values for `DugResource.repository`: one lower-case slug per repository.

A free string like `resource_type`, so a new repository does not need a model release, but
producers that infer the repository from a URL or DOI prefix should map to these slugs so
that a filter on `repository` finds every deposit from the same place.
"""


class DugResource(DugElement):
    """Something outside Dug that can be pointed to with a URL and a description.

    The main use is the repository deposit that a study's files came from, e.g. a Figshare
    article, a Zenodo or Dataverse dataset, or an OpenNeuro dataset. `name` is the deposit's
    title, `description` is its description, and `action` is its landing page. A resource
    with a DOI is citable. A single file within a deposit is a `DugDocument`, a subclass of
    this class.
    """

    type: Literal["resource"] = RESOURCE_TYPE

    resource_type: str = Field(
        "dataset", description="Kind of resource; recommended values are listed in RESOURCE_KINDS."
    )
    repository: str = Field(
        "",
        description="Slug of the repository hosting this resource; recommended values are "
        "listed in REPOSITORY_KINDS.",
    )
    authors: list[str] = Field(default_factory=list, description="Author names in citation order.")
    doi: str = Field(
        "", description="Bare DOI of this resource, without a resolver prefix; empty when unknown."
    )
    license: str = Field("", description="SPDX licence identifier; empty when unknown.")
    document_list: list[str] = Field(
        default_factory=list, description="IDs of the DugDocuments that came from this resource."
    )

    def get_searchable_dict(self) -> dict[str, Any]:
        es_elem = super().get_searchable_dict()
        return {
            **es_elem,
            "resource_type": self.resource_type,
            "repository": self.repository,
            "authors": self.authors,
            "doi": self.doi,
            "license": self.license,
            "document_list": self.document_list,
        }
