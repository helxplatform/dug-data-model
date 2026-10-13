from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import Field

from .base import DugElement, References

RESOURCE_TYPE = "resource"

RESOURCE_KINDS: tuple[str, ...] = (
    "dataset",
    "software",
    "publication",
    "preprint",
    "website",
    "press_release",
    "readme",
    "protocol",
    "manual",
    "methods",
    "report",
    "poster",
    "presentation",
    "patent",
    "supplementary_table",
    "data",
    "other",
)
"""Recommended values for `DugResource.resource_type`: what the resource is, whether it is a
landing page or a file.

A free string, like `DugVariable.data_type`, so that a new kind does not need a model
release; producers should prefer these. The list is coarse on purpose: a finer kind, such as
one of PubMed's publication types ("Review", "Randomized Controlled Trial"), belongs in
`tags` as `{"category": "publication_type", "value": ...}`, which an index can filter on.

A file that is its parent in one format has its parent's kind: the PDF of a publication is
a `publication` with `mime_type="application/pdf"` under the `publication` that is the work,
and a protocol's PDF is a `protocol` under the protocol. A file that is something of its own
-- a `supplementary_table` under a publication, a `readme` under a dataset -- has its own
kind. So "the full text" needs no field of its own: it is the child whose kind matches its
parent's. ('article' was that child's kind when a file was a separate `DugDocument` type,
and went with it.) 'data' is a data file (a spreadsheet, an archive, a recording) that a
producer chose to emit as a resource rather than only count in its deposit's inventory.
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
    """Anything outside Dug that has a URL, at whatever size.

    A program website, a project's page on an NIH site, a press release, a Zenodo community,
    the Zenodo or Figshare deposit a study's files came from, a dataset with or without a DOI,
    a publication; and each file of any of these: the deposit's README, the paper's PDF, the
    dataset's XLSX, the HTML of the press release. `name` is its title, `description` its
    description, `action` its landing or download page. `resource_type` says what it is (see
    `RESOURCE_KINDS`); `repository`, `authors`, `doi` and `license` say where it is published
    and how to cite it. A resource that is one file in one format also has `file_name` and
    `mime_type`; a landing page has neither, and a web page captured as text has
    `mime_type="text/html"` and no `file_name`. A UI renders every resource the same way --
    a title, a link, a kind and a format -- in a tree or in a flat list.

    Resources form a tree. A resource's parent is its study (`parent_type="study"`) or the
    resource it is part of (`parent_type="resource"`): a file hangs off the deposit it was
    downloaded from, a deposit off its Zenodo community, a press release page off the project
    website, a supplementary table off the paper. A file that came from no known resource
    hangs off the study. A resource lists nothing: its children name it in `parents`, and
    `studies` names the study from any depth. So a UI that shows only the resources whose
    parent is the study loses nothing, and one that follows `parents` can show the whole
    tree. A resource with the wrong parent is found by `studies` and by search, but shown in
    the wrong place.

    A resource holds no text of its own. Whatever can be read out of a file lives in its
    `DugContent` children, under the file's `license`: a producer emits content only when
    `can_include_content(resource.license)` is true (see `licenses.py`), so a file whose text
    could not be read -- a scanned PDF, a format no parser handles -- or may not be
    incorporated is a resource with no content, still listed, linked to, and found by its
    title and description. Whether a producer emits a resource for every file in a deposit
    or only for the ones a person would read is its choice: the reference producer
    inventories data files in the deposit's `metadata` and emits no resource for them.

    Earlier versions had a separate `DugDocument` type for a file, with a `DugCitable` base
    class for the fields it shared with `DugResource`. Every awkward case -- a press release
    page captured as text, a PDF report with a DOI of its own, a document hanging off a study
    because no deposit was known -- came from drawing that line, and a UI had to render two
    types; one type in a tree needs neither. A file written with `"type": "document"` does
    not load.
    """

    type: Literal["resource"] = RESOURCE_TYPE

    resource_type: str = Field(
        "",
        description="Kind of resource; recommended values are listed in RESOURCE_KINDS. A file "
        "that is its parent in one format has its parent's kind.",
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
    license: str = Field(
        "",
        description="SPDX licence identifier, or a `LicenseRef-` name for terms SPDX does not "
        "list (e.g. all rights reserved); empty when unknown. Governs the DugContent under it.",
    )
    file_name: str = Field(
        "",
        description="Original file name when the resource is one file, e.g. 'README.pdf'; "
        "empty for a landing page.",
    )
    mime_type: str = Field(
        "",
        description="IANA media type when the resource is one file, e.g. 'application/pdf'; "
        "empty for a landing page.",
    )
    studies: Annotated[list[str], References("study")] = Field(
        default_factory=list,
        description="IDs of the studies this resource belongs to, at any depth below them; "
        "`parents` names only the element directly above.",
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
            "file_name": self.file_name,
            "mime_type": self.mime_type,
            "studies": self.studies,
        }
