from __future__ import annotations

from typing import Annotated, Any

from pydantic import Field

from .base import DugElement, References


class DugCitable(DugElement):
    """The fields that `DugResource` and `DugDocument` share: where a thing is published and
    how to cite it.

    This is a base class, not an element type: it has no `type` of its own and is not in
    `Indexable`. `isinstance(x, DugCitable)` is true of resources and documents alike;
    `isinstance(x, DugResource)` is true of resources only. The two are siblings rather than
    one subclassing the other so that each can narrow `type` to its own literal, and so that
    code which picks out resources by class does not also pick up every document.

    `studies` names the studies an item belongs to, however far below them it sits. `parents`
    is containment and names only the next element up, so from a piece of content the study
    is up to three hops away, and Dug's index can only filter on `parents` one hop at a time
    (see docs/how-dug-uses-elements.md). The producer knows the study when it writes the
    element, even when it does not emit the study itself, so it writes the ID here and one
    query on `studies` finds everything in a study. Empty when no study is known.
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
    studies: Annotated[list[str], References("study")] = Field(
        default_factory=list,
        description="IDs of the studies this item belongs to, at any depth below them; "
        "`parents` names only the element directly above.",
    )

    def get_searchable_dict(self) -> dict[str, Any]:
        es_elem = super().get_searchable_dict()
        return {
            **es_elem,
            "repository": self.repository,
            "authors": self.authors,
            "doi": self.doi,
            "license": self.license,
            "studies": self.studies,
        }
