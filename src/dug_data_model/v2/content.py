from __future__ import annotations

from typing import Annotated, Any, Literal, override

from pydantic import Field, computed_field, field_validator

from .base import DugElement, FromParents, References

CONTENT_TYPE = "content"

UNLICENSED_VALUES: frozenset[str] = frozenset({"", "none", "noassertion"})
"""`license` values, casefolded and stripped, that can never permit content: empty (nobody
has checked), and SPDX's NONE (no licence declared) and NOASSERTION (not determined)."""


class DugContent(DugElement):
    """A piece of a `DugResource`'s text: a heading and the body under it.

    Content is the only element that holds text. A `DugResource` describes and links to a
    file; if the file's text can be read, and the resource's licence allows the text to be
    incorporated, it is split into DugContent children, one per heading (or a single one
    when there are no headings). `name` is the heading and `content` is the text under it.
    `description` is metadata about the piece, as on every other element, and is usually
    empty. `parents` holds the ID of the resource the text came from, and `parent_type` is
    'resource', its default (anything else, even empty, is rejected); `studies` holds the ID
    of the study, as on `DugResource`, so that the study can be found without climbing
    through the resource.

    Content exists only when its resource's licence permits it (see `licenses.py`): a file
    whose text may not be incorporated has no content, so the case shows in the shape of the
    data rather than in a flag that an index or a UI has to remember to honour. `license` is
    a copy of that licence, not a gate: Dug indexes and returns each element on its own, so
    a content hit carries the terms of its text, for attribution, without a lookup through
    `parents`. It is required, and `validate_references()` checks that it equals each
    parent's, so that the copy cannot drift from the resource it came from. Loading rejects
    the values in `UNLICENSED_VALUES`, which say that no licence permits the text. It does
    not check `can_include_content()`, because a producer may widen `CONTENT_LICENSES` for a
    source whose terms a person has checked; so a NonCommercial licence on content is that
    producer's decision, not an error.

    Content is a separate element, not a list inside its resource, because Dug annotates and
    indexes each element on its own: a section is sent to the annotator as one bounded text
    and comes back as its own search hit, with `order` and `location` to point at. Embedded
    in the resource, the text would be annotated as one PDF-sized string, or not at all, and
    returned whole with every hit on the resource (see docs/how-dug-uses-elements.md).
    """

    type: Literal["content"] = CONTENT_TYPE
    parent_type: Literal["resource"] = Field(
        "resource", description="Always 'resource': content is a piece of a DugResource's text."
    )

    order: int = Field(
        0, ge=0, description="0-based order of this content within its resource, for sorting."
    )
    location: str | None = Field(
        None,
        description=(
            "Where this content starts in the file, in whatever terms suit the format "
            "('page 3', 'line 17', 'Data!A1:F120'), for a person to find it; not parsed."
        ),
    )
    content: str = Field(
        description=(
            "The text under the heading. Required, so that a file written when the text was "
            "held in `description` fails to load instead of loading with no text."
        )
    )
    studies: Annotated[list[str], References("study", inherited=True)] = Field(
        default_factory=list,
        description="IDs of the studies this content belongs to, as on DugResource.",
    )
    license: Annotated[str, FromParents()] = Field(
        description=(
            "The licence of the resource this text came from, copied so that each hit carries "
            "it; must equal the parent's `license`."
        )
    )

    @field_validator("license")
    @classmethod
    def _license_permits_content(cls, value: str) -> str:
        if value.strip().casefold() in UNLICENSED_VALUES:
            raise ValueError(
                f"license {value!r} permits no content; a resource with no licence has none"
            )
        return value

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
            "order": self.order,
            "location": self.location,
            "content": self.content,
            "studies": self.studies,
            "license": self.license,
        }
