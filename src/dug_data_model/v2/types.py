from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Annotated, Any

from pydantic import Field, TypeAdapter

from .concept import DugConcept
from .variable import DugVariable
from .study import DugStudy
from .section import DugSection
from .document import DugDocument
from .document_section import DugDocumentSection

InputFile = str | Path

Indexable = DugConcept | DugVariable | DugStudy | DugSection | DugDocument | DugDocumentSection
Parser = Callable[[Any], Iterable[Indexable]]
FileParser = Callable[[InputFile], Iterable[Indexable]]

DiscriminatedIndexable = Annotated[Indexable, Field(discriminator="type")]
DugElementParsedList: TypeAdapter[list[DiscriminatedIndexable]] = TypeAdapter(
    list[DiscriminatedIndexable]
)
