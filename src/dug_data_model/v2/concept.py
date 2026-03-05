"""Concept class for the Dug data model scaffold.

This module provides the `DugConcept` class that represents ontological
concepts used to organize and link searchable elements. Concepts carry
identifiers and knowledge graph enrichment data.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from .base import DugElement
from .utils import dedupe_and_sort

CONCEPT_TYPE = "concept"


class DugConcept(DugElement):
    """An ontological concept used to organise and link searchable elements.

    Each concept maps to at least one DugElement and carries identifiers (e.g.
    ontology CURIEs) and knowledge-graph query results.
    """

    type: Literal["concept"] = CONCEPT_TYPE
    """Element type discriminator, always 'concept'."""

    identifiers: dict[str, Any] = Field(default_factory=dict)
    """Mapping of identifier IDs to identifier objects (e.g., DugIdentifier).

    Identifier objects should have: id, search_text, synonyms, add_search_text(),
    and get_searchable_dict() attributes/methods.
    """

    kg_answers: dict[str, Any] = Field(default_factory=dict)
    """Mapping of answer IDs to KG answer objects (e.g., QueryKG instances).

    KG answer objects should have: nodes, get_node_names(), and get_node_synonyms()
    attributes/methods.
    """

    concept_type: str = ""
    """Optional subtype categorization (e.g., 'disease', 'phenotype')."""

    def add_identifier(self, ident: Any) -> None:
        """Add or merge an identifier into this concept.

        Args:
            ident: An identifier object with id, search_text, synonyms,
                and add_search_text() method (e.g., DugIdentifier).
        """
        if ident.id in self.identifiers:
            for search_text in ident.search_text:
                self.identifiers[ident.id].add_search_text(search_text)
        else:
            self.identifiers[ident.id] = ident

    def add_kg_answer(self, answer: Any, query_name: str) -> None:
        """Add a knowledge graph answer to this concept.

        Args:
            answer: A KG answer object with nodes dict, get_node_names(),
                and get_node_synonyms() methods (e.g., QueryKG).
            query_name: Name of the query that produced this answer.
        """
        answer_node_ids = list(answer.nodes.keys())
        answer_id = f'{"_".join(answer_node_ids)}_{query_name}'
        if answer_id not in self.kg_answers:
            self.kg_answers[answer_id] = answer

    def set_search_terms(self) -> None:
        """Aggregate search terms from all identifiers."""
        search_terms = list(self.search_terms)
        for ident in self.identifiers.values():
            search_terms.extend(ident.search_text)
            search_terms.extend(ident.synonyms)
        self.search_terms = dedupe_and_sort(search_terms)

    def set_optional_terms(self) -> None:
        """Aggregate optional terms from knowledge graph answers."""
        optional_terms = list(self.optional_terms)
        for kg_answer in self.kg_answers.values():
            optional_terms.extend(kg_answer.get_node_names())
            optional_terms.extend(kg_answer.get_node_synonyms())
        self.optional_terms = dedupe_and_sort(optional_terms)

    def get_searchable_dict(self) -> dict[str, Any]:
        """Return an Elasticsearch-compatible representation.

        Returns:
            A dictionary with fields formatted for Elasticsearch indexing.
        """
        base = super().get_searchable_dict()
        return {
            **base,
            "identifiers": [
                ident.get_searchable_dict() for ident in self.identifiers.values()
            ],
            "concept_type": self.concept_type,
        }
