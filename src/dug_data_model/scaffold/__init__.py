"""Dug Data Model Scaffold - Bootstrap new data model versions.

This package provides a CLI tool for generating new data model versions
inside the dug_data_model package (e.g., v3/, v4/).

CLI Usage
---------
Generate a new data model version::

    python -m dug_data_model.scaffold new <version>

Examples::

    # Create v3 of the data model
    python -m dug_data_model.scaffold new v3

    # Overwrite an existing version
    python -m dug_data_model.scaffold new v3 --force

Generated Structure
-------------------
The scaffold creates a new version directory inside dug_data_model::

    src/dug_data_model/v3/
    ├── __init__.py      # Package exports
    ├── base.py          # DugElement base class
    ├── concept.py       # DugConcept class
    ├── types.py         # Utility types and examples
    ├── utils.py         # Helper functions
    └── py.typed         # PEP 561 marker

Customizing the Generated Version
---------------------------------
After generation, you need to:

1. **Add element subclasses** (e.g., in a new ``variable.py``)::

       from typing import Literal, Any
       from .base import DugElement

       class DugVariable(DugElement):
           type: Literal["variable"] = "variable"
           data_type: str = "text"

           def get_searchable_dict(self) -> dict[str, Any]:
               base = super().get_searchable_dict()
               return {**base, "data_type": self.data_type}

2. **Define your Indexable union** in ``types.py``::

       from typing import Annotated
       from pydantic import Field, TypeAdapter

       from .concept import DugConcept
       from .variable import DugVariable
       from .study import DugStudy

       # Union of all element types that can be indexed
       Indexable = DugConcept | DugVariable | DugStudy

       # Discriminated union for polymorphic JSON parsing
       DiscriminatedIndexable = Annotated[Indexable, Field(discriminator="type")]

       # TypeAdapter for deserializing mixed lists from JSON
       DugElementParsedList = TypeAdapter(list[DiscriminatedIndexable])

3. **Export your classes** from ``__init__.py`` and call ``model_rebuild()``::

       from .variable import DugVariable

       DugVariable.model_rebuild()  # Required for each subclass

Identifier and KG Answer Objects
--------------------------------
DugConcept accepts identifier and KG answer objects with duck typing (Any).

Identifier objects should have:
    - ``id``: Unique identifier string
    - ``search_text``: List of search terms
    - ``synonyms``: List of synonym strings
    - ``add_search_text(text)``: Method to add a search term
    - ``get_searchable_dict()``: Method returning a dict for indexing

KG answer objects should have:
    - ``nodes``: Dict mapping node IDs to node data
    - ``get_node_names()``: Method returning list of node names
    - ``get_node_synonyms()``: Method returning list of node synonyms
"""

from .base import DugElement
from .concept import CONCEPT_TYPE, DugConcept
from .types import InputFile
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
    find_missing_references,
    validate_references,
    validate_unique_ids,
)

# Resolve forward references. Call model_rebuild() on all DugElement subclasses.
DugElement.model_rebuild()
DugConcept.model_rebuild()

__all__ = [
    # Core classes
    "DugElement",
    "DugConcept",
    # Constants
    "CONCEPT_TYPE",
    # Utility types
    "InputFile",
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
    "find_missing_references",
    "validate_references",
    "validate_unique_ids",
]
