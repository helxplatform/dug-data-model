"""Base element class for the Dug data model scaffold.

This module provides the core `DugElement` class that searchable
entities inherit from.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field, computed_field

from .utils import complex_handler, dedupe_and_sort

if TYPE_CHECKING:
    from .concept import DugConcept


class DugElement(BaseModel):
    """Base class for any object that should be searchable via Dug.

    This is the foundational class for the Dug data model. It can represent
    a DbGaP variable, DICOM image, application, or any other searchable entity.
    All domain-specific element types (variables, studies, sections, etc.)
    should inherit from this class.
    """

    id: str
    """Unique identifier for this element."""

    name: str
    """Human-readable name (e.g., variable name, study title)."""

    description: str
    """Description of the element, used for search and display."""

    type: str = ""
    """Element type discriminator. Subclasses should narrow this to a Literal."""

    programs: list[str] = Field(default_factory=list)
    """Programs or projects this element belongs to."""

    action: str = ""
    """URL or action identifier associated with this element."""

    parents: list[str] = Field(default_factory=list)
    """IDs of parent elements in the hierarchy."""

    parent_type: str = ""
    """Type of the parent elements (e.g., 'study', 'section')."""

    concepts: dict[str, "DugConcept"] = Field(default_factory=dict)
    """Mapping of concept IDs to DugConcept objects linked to this element."""

    search_terms: list[str] = Field(default_factory=list)
    """Primary search terms aggregated from linked concepts."""

    optional_terms: list[str] = Field(default_factory=list)
    """Secondary search terms derived from knowledge graph enrichment."""

    metadata: dict[str, Any] = Field(default_factory=dict)
    """Extensible key-value storage for additional properties."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra='ignore')

    def __setattr__(self, name, value):
        # jsonpickle reconstructs objects via __new__ (skipping __init__), so
        # __pydantic_fields_set__ may not exist yet, old serialized data may contain
        # removed fields (e.g. concept_action), and computed properties (e.g.
        # ml_ready_desc) have no setter. Handle all three cases gracefully.
        try:
            super().__setattr__(name, value)
        except (AttributeError, ValueError):
            try:
                object.__setattr__(self, name, value)
            except AttributeError:
                pass  # read-only computed property — skip silently

    def __getattr__(self, name):
        # jsonpickle reconstructs via __new__, leaving Pydantic fields unset in
        # __dict__. Return the field default so callers don't get AttributeError.
        from pydantic_core import PydanticUndefinedType
        fields = self.__class__.model_fields
        if name in fields:
            field_info = fields[name]
            # Check factory first (covers List/Dict fields like parents, programs, tags)
            if field_info.default_factory is not None:
                return field_info.default_factory()
            # Then check scalar default (covers action="", type="", etc.)
            if not isinstance(field_info.default, PydanticUndefinedType):
                return field_info.default
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __getstate__(self):
        # jsonpickle calls __getstate__ when re-encoding objects that were
        # reconstructed via __new__. Pydantic v2's __getstate__ needs
        # __pydantic_private__, __pydantic_fields_set__, and __pydantic_extra__
        # to exist.
        if not hasattr(self, '__pydantic_private__'):
            object.__setattr__(self, '__pydantic_private__', None)
        if not hasattr(self, '__pydantic_fields_set__'):
            object.__setattr__(self, '__pydantic_fields_set__', set())
        if not hasattr(self, '__pydantic_extra__'):
            object.__setattr__(self, '__pydantic_extra__', None)
        return super().__getstate__()

    @computed_field
    @property
    def ml_ready_desc(self) -> str:
        """Return a machine-learning-ready description.

        Override this in subclasses to provide custom preprocessing
        (e.g., expanding variable names, adding context).

        Returns:
            A description suitable for ML embedding or processing.
        """
        return self.description

    def add_concept(self, concept: DugConcept) -> None:
        """Link a concept to this element.

        Args:
            concept: The DugConcept to associate with this element.
        """
        self.concepts[concept.id] = concept

    def add_metadata(self, metadata: dict[str, Any]) -> None:
        """Set the metadata dictionary for this element.

        Args:
            metadata: Key-value pairs of additional properties.
        """
        self.metadata = metadata

    def add_parent(self, parent_id: str) -> None:
        """Add a parent element ID to the hierarchy.

        Args:
            parent_id: The ID of a parent element.
        """
        self.parents.append(parent_id)

    def add_program_name(self, program_name: str) -> None:
        """Associate this element with a program.

        Args:
            program_name: Name of the program to add.
        """
        self.programs.append(program_name)

    def jsonable(self) -> dict[str, Any]:
        """Return a JSON-serializable dict representation.

        Returns:
            A dictionary suitable for JSON serialization or pickling.
        """
        return self.model_dump()

    def get_searchable_dict(self) -> dict[str, Any]:
        """Return an Elasticsearch-compatible representation.

        This method transforms the element into a flat dictionary suitable
        for indexing in Elasticsearch. Subclasses should call `super()` and
        merge in their additional fields.

        Returns:
            A dictionary with fields formatted for Elasticsearch indexing.
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "search_terms": self.search_terms,
            "optional_terms": self.optional_terms,
            "action": self.action,
            "element_type": self.type,
            "metadata": self.metadata,
            "parents": self.parents,
            "programs": self.programs,
            "identifiers": list(self.concepts.keys()) if self.concepts else [],
        }

    def get_response_dict(self) -> dict[str, Any]:
        """Return a filtered representation for API responses.

        This excludes internal fields like search_terms and optional_terms
        that are used for indexing but not typically shown to end users.

        Returns:
            A dictionary suitable for API response serialization.
        """
        response = self.get_searchable_dict()
        hidden = {"search_terms", "optional_terms"}
        return {k: v for k, v in response.items() if k not in hidden}

    def get_id(self) -> str:
        """Return the element's unique identifier.

        Returns:
            The element ID.
        """
        return self.id

    def set_search_terms(self) -> None:
        """Aggregate search terms from all linked concepts.

        This traverses all concepts, triggers their search term aggregation,
        and collects the results. Terms are deduplicated and sorted.
        """
        search_terms: list[str] = []
        for concept in self.concepts.values():
            concept.set_search_terms()
            search_terms.extend(concept.search_terms)
            search_terms.append(concept.name)
        self.search_terms = dedupe_and_sort(search_terms)

    def set_optional_terms(self) -> None:
        """Aggregate optional terms from all linked concepts.

        This traverses all concepts, triggers their optional term aggregation
        (typically from knowledge graph answers), and collects the results.
        Terms are deduplicated and sorted.
        """
        optional_terms: list[str] = []
        for concept in self.concepts.values():
            concept.set_optional_terms()
            optional_terms.extend(concept.optional_terms)
        self.optional_terms = dedupe_and_sort(optional_terms)

    def clean(self) -> None:
        """Deduplicate and sort search terms and optional terms."""
        self.search_terms = dedupe_and_sort(self.search_terms)
        self.optional_terms = dedupe_and_sort(self.optional_terms)

    def __str__(self) -> str:
        """Return a JSON string representation of this element."""
        return json.dumps(self.jsonable(), indent=2, default=complex_handler)
