"""Type definitions for the Dug data model.

This module provides utilities for working with Dug elements.

After adding your own element subclasses, you should define:

1. An Indexable union of all your element types:

    Indexable = DugConcept | DugVariable | DugStudy | DugSection

2. A discriminated version for polymorphic parsing:

    DiscriminatedIndexable = Annotated[Indexable, Field(discriminator="type")]

3. A TypeAdapter for deserializing mixed lists:

    DugElementParsedList = TypeAdapter(list[DiscriminatedIndexable])

See the example at the bottom of this file.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Annotated, Any

from pydantic import Field, TypeAdapter

from .concept import DugConcept

# ---------------------------------------------------------------------------
# Utility types
# ---------------------------------------------------------------------------

InputFile = str | Path
"""A file path, either as a string or Path object."""


# ---------------------------------------------------------------------------
# Example: Defining your own types after adding element subclasses
# ---------------------------------------------------------------------------
#
# from typing import Annotated
# from pydantic import Field, TypeAdapter
#
# from .concept import DugConcept
# from .variable import DugVariable  # your custom subclass
# from .study import DugStudy        # your custom subclass
#
# # 1. Define a union of all indexable types
# Indexable = DugConcept | DugVariable | DugStudy
#
# # 2. Create a discriminated union for polymorphic parsing
# DiscriminatedIndexable = Annotated[Indexable, Field(discriminator="type")]
#
# # 3. Create a TypeAdapter for parsing lists
# DugElementParsedList: TypeAdapter[list[DiscriminatedIndexable]] = TypeAdapter(
#     list[DiscriminatedIndexable]
# )
#
# # 4. Define parser type aliases (optional)
# Parser = Callable[[Any], Iterable[Indexable]]
# FileParser = Callable[[InputFile], Iterable[Indexable]]
