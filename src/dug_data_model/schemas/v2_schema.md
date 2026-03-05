# Dug Data Model v2

This document describes the data model schema in a human-readable format.

## Table of Contents

- [DugConcept](#dugconcept)
- [DugSection](#dugsection)
- [DugStudy](#dugstudy)
- [DugVariable](#dugvariable)

## DugConcept

An ontological concept used to organise and link searchable elements.

Each concept maps to at least one DugElement and carries identifiers (e.g.
ontology CURIEs) and knowledge-graph query results.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | `str` | Yes | - |  |
| `name` | `str` | Yes | - |  |
| `description` | `str` | Yes | - |  |
| `type` | `"concept"` | No | `"concept"` |  |
| `programs` | `list[str]` | No | - |  |
| `action` | `str` | No | `""` |  |
| `parents` | `list[str]` | No | - |  |
| `parent_type` | `str` | No | `""` |  |
| `concepts` | `dict[str, object]` | No | - |  |
| `search_terms` | `list[str]` | No | - |  |
| `optional_terms` | `list[str]` | No | - |  |
| `metadata` | `dict[str, any]` | No | - |  |
| `tags` | `list[dict[str, str]]` | No | - |  |
| `identifiers` | `dict[str, any]` | No | - |  |
| `kg_answers` | `dict[str, any]` | No | - |  |
| `concept_type` | `str` | No | `""` |  |

## DugSection

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | `str` | Yes | - |  |
| `name` | `str` | Yes | - |  |
| `description` | `str` | Yes | - |  |
| `type` | `"section"` | No | `"section"` |  |
| `programs` | `list[str]` | No | - |  |
| `action` | `str` | No | `""` |  |
| `parents` | `list[str]` | No | - |  |
| `parent_type` | `str` | No | `""` |  |
| `concepts` | `dict[str, object]` | No | - |  |
| `search_terms` | `list[str]` | No | - |  |
| `optional_terms` | `list[str]` | No | - |  |
| `metadata` | `dict[str, any]` | No | - |  |
| `tags` | `list[dict[str, str]]` | No | - |  |
| `is_crf` | `bool` | No | `False` |  |
| `variable_list` | `list[str]` | No | - |  |

## DugStudy

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | `str` | Yes | - |  |
| `name` | `str` | Yes | - |  |
| `description` | `str` | Yes | - |  |
| `type` | `"study"` | No | `"study"` |  |
| `programs` | `list[str]` | No | - |  |
| `action` | `str` | No | `""` |  |
| `parents` | `list[str]` | No | - |  |
| `parent_type` | `str` | No | `""` |  |
| `concepts` | `dict[str, object]` | No | - |  |
| `search_terms` | `list[str]` | No | - |  |
| `optional_terms` | `list[str]` | No | - |  |
| `metadata` | `dict[str, any]` | No | - |  |
| `tags` | `list[dict[str, str]]` | No | - |  |
| `publications` | `list[str]` | No | - |  |
| `variable_list` | `list[str]` | No | - |  |
| `section_list` | `list[str]` | No | - |  |
| `abstract` | `str` | No | `""` |  |

## DugVariable

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | `str` | Yes | - |  |
| `name` | `str` | Yes | - |  |
| `description` | `str` | Yes | - |  |
| `type` | `"variable"` | No | `"variable"` |  |
| `programs` | `list[str]` | No | - |  |
| `action` | `str` | No | `""` |  |
| `parents` | `list[str]` | No | - |  |
| `parent_type` | `str` | No | `""` |  |
| `concepts` | `dict[str, object]` | No | - |  |
| `search_terms` | `list[str]` | No | - |  |
| `optional_terms` | `list[str]` | No | - |  |
| `metadata` | `dict[str, any]` | No | - |  |
| `tags` | `list[dict[str, str]]` | No | - |  |
| `data_type` | `str` | No | `"text"` |  |
| `is_cde` | `bool` | No | `False` |  |
