from .base import DugElement
from .concept import CONCEPT_TYPE, DugConcept
from .variable import VARIABLE_TYPE, DugVariable
from .study import STUDY_TYPE, DugStudy
from .section import SECTION_TYPE, DugSection
from .document import DOCUMENT_KINDS, DOCUMENT_TYPE, DugDocument
from .document_section import DOCUMENT_SECTION_TYPE, DugDocumentSection
from .types import (
    InputFile,
    Indexable,
    Parser,
    FileParser,
    DiscriminatedIndexable,
    DugElementParsedList,
)
from .utils import (
    build_parent_map,
    complex_handler,
    count_by_type,
    dedupe_and_sort,
    filter_by_type,
    get_all_ids,
    get_children,
    get_element_by_id,
    group_by_id,
    group_by_type,
    load_elements,
    prepare_for_indexing,
    serialize_elements,
)
from .validation import (
    DuplicateIdError,
    MissingReferenceError,
    find_duplicate_ids,
    validate_unique_ids,
)

# Resolve forward references. Call model_rebuild() on all DugElement subclasses.
DugElement.model_rebuild()
DugConcept.model_rebuild()
DugVariable.model_rebuild()
DugStudy.model_rebuild()
DugSection.model_rebuild()
DugDocument.model_rebuild()
DugDocumentSection.model_rebuild()

__all__ = [
    # Core classes
    "DugElement",
    "DugConcept",
    "DugVariable",
    "DugStudy",
    "DugSection",
    "DugDocument",
    "DugDocumentSection",
    # Type definitions
    "Indexable",
    "Parser",
    "InputFile",
    "FileParser",
    "DiscriminatedIndexable",
    "DugElementParsedList",
    # Constants
    "VARIABLE_TYPE",
    "STUDY_TYPE",
    "CONCEPT_TYPE",
    "SECTION_TYPE",
    "DOCUMENT_TYPE",
    "DOCUMENT_SECTION_TYPE",
    "DOCUMENT_KINDS",
    # Filtering and grouping
    "filter_by_type",
    "group_by_type",
    "group_by_id",
    "count_by_type",
    "get_element_by_id",
    "get_all_ids",
    # Hierarchy utilities
    "build_parent_map",
    "get_children",
    # Batch operations
    "prepare_for_indexing",
    # Serialization
    "complex_handler",
    "dedupe_and_sort",
    "load_elements",
    "serialize_elements",
    # Validation
    "DuplicateIdError",
    "MissingReferenceError",
    "find_duplicate_ids",
    "validate_unique_ids",
]
