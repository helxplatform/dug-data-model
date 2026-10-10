"""Which licences allow a resource's text to be incorporated as `DugContent`."""

from __future__ import annotations

CONTENT_LICENSES: frozenset[str] = frozenset(
    {"CC0-1.0", "PDDL-1.0", "CC-BY-3.0", "CC-BY-4.0", "CC-BY-SA-3.0", "CC-BY-SA-4.0"}
)
"""SPDX identifiers of licences under which extracted text may be indexed and shown with
attribution.

A producer emits `DugContent` for a file only when its resource's licence is one of these;
under any other licence the resource is emitted alone, with no content. Keeping the rule here
means every producer draws the line in the same place. Like `RESOURCE_KINDS` it is a recommendation,
not a constraint: a producer may widen it for a source whose terms it has checked. It is
deliberately short. NonCommercial and NoDerivatives variants are left out because whether a
search index counts as commercial use or a derivative is a question for a person, not a lookup
table; and no licence at all means the text stays at the source.
"""

_CONTENT_LICENSES_CASEFOLDED = frozenset(lic.casefold() for lic in CONTENT_LICENSES)


def can_include_content(license: str) -> bool:
    """Return True if text under *license* (an SPDX identifier) may become `DugContent`.

    An empty or unknown licence gives False: the resource is still listed and linked to, so
    users can read the text at its `action`, but none of it is incorporated. Matching
    ignores case and surrounding whitespace, since SPDX identifiers are case-insensitive and
    licences copied from repository metadata are often written as `cc-by-4.0`.
    """
    return license.strip().casefold() in _CONTENT_LICENSES_CASEFOLDED
