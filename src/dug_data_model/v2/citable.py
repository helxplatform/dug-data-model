from __future__ import annotations

from typing import Any

from pydantic import Field

from .base import DugElement


class DugCitable(DugElement):
    """The fields that `DugResource` and `DugDocument` share: where a thing is published and
    how to cite it.

    This is a base class, not an element type: it has no `type` of its own and is not in
    `Indexable`. `isinstance(x, DugCitable)` is true of resources and documents alike;
    `isinstance(x, DugResource)` is true of resources only. The two are siblings rather than
    one subclassing the other so that each can narrow `type` to its own literal, and so that
    code which picks out resources by class does not also pick up every document.
    """

    repository: str = Field(
        "",
        description="Slug of the repository hosting this item; recommended values are "
        "listed in REPOSITORY_KINDS.",
    )
    authors: list[str] = Field(default_factory=list, description="Author names in citation order.")
    doi: str = Field(
        "", description="Bare DOI of this item, without a resolver prefix; empty when unknown."
    )
    license: str = Field(
        "",
        description="SPDX licence identifier, or a `LicenseRef-` name for terms SPDX does not "
        "list (e.g. all rights reserved); empty when unknown.",
    )

    def get_searchable_dict(self) -> dict[str, Any]:
        es_elem = super().get_searchable_dict()
        return {
            **es_elem,
            "repository": self.repository,
            "authors": self.authors,
            "doi": self.doi,
            "license": self.license,
        }
