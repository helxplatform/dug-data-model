"""Which licences allow a document's text to be shown in a user interface."""

from __future__ import annotations

DISPLAYABLE_LICENSES: frozenset[str] = frozenset(
    {"CC0-1.0", "PDDL-1.0", "CC-BY-3.0", "CC-BY-4.0", "CC-BY-SA-3.0", "CC-BY-SA-4.0"}
)
"""SPDX identifiers of licences under which extracted text may be displayed with attribution.

This is the rule behind `DugContent.can_display_content`, kept here so that every producer
sets the flag the same way. Like `DOCUMENT_KINDS` it is a recommendation, not a constraint:
a producer may widen it for a source whose terms it has checked. It is deliberately short.
NonCommercial and NoDerivatives variants are left out because whether a search index counts
as commercial use or a derivative is a question for a person, not a lookup table; and no
licence at all means the text may be indexed but not shown.
"""


def can_display(license: str) -> bool:
    """Return True if text under *license* (an SPDX identifier) may be shown in a UI.

    An empty or unknown licence gives False: the text can still be indexed, but users
    should be sent to the element's `action` to read it at the source.
    """
    return license in DISPLAYABLE_LICENSES
