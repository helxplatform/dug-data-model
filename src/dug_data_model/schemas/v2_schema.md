# Dug Data Model v2

This document describes the data model schema in a human-readable format.

## Table of Contents

- [DugConcept](#dugconcept)
- [DugContent](#dugcontent)
- [DugDocument](#dugdocument)
- [DugResource](#dugresource)
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

## DugContent

A piece of a `DugDocument`'s text: a heading and the body under it.

Content is the only element that holds a document's text. A `DugDocument` describes and
links to a file; if the file's text can be read, it is split into DugContent children, one
per heading (or a single one when there are no headings). `name` is the heading and
`description` is the text. `parents` holds the ID of the containing document, with
`parent_type` set to 'document'.

Because content is the only element with anything to display, it is also the only one
that carries `can_display_content`. Producers set it from the document's licence; the
document itself does not repeat it.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | `str` | Yes | - |  |
| `name` | `str` | Yes | - |  |
| `description` | `str` | Yes | - |  |
| `type` | `"content"` | No | `"content"` |  |
| `programs` | `list[str]` | No | - |  |
| `action` | `str` | No | `""` |  |
| `parents` | `list[str]` | No | - |  |
| `parent_type` | `str` | No | `""` |  |
| `concepts` | `dict[str, object]` | No | - |  |
| `search_terms` | `list[str]` | No | - |  |
| `optional_terms` | `list[str]` | No | - |  |
| `metadata` | `dict[str, any]` | No | - |  |
| `tags` | `list[dict[str, str]]` | No | - |  |
| `position` | `int` | No | `0` | 0-based order of this content within its document. |
| `level` | `int` | No | `None` | Heading depth (1 = top level) when the source format exposes it. |
| `page` | `int` | No | `None` | 1-based page this content starts on, for paginated formats. |
| `can_display_content` | `bool` | No | `False` | True only when the licence permits showing the text in a user interface. When False, the text is indexed but left out of API responses and users should be sent to `action` instead. |

## DugDocument

A `DugResource` that is a single file: a README, protocol, report, poster, ...

A repository deposit is a resource; one file in it is a document. Being a resource, a
document has a title (`name`), a summary (`description`), a landing or download URL
(`action`), and the citable `repository`, `authors`, `doi` and `license` fields; it adds
what only a file has: `file_name`, `mime_type` and `document_type`. Its `resource_type`
is always 'document', and `document_list`, inherited from the resource, is normally empty.

A document holds no text of its own. Whatever could be read out of the file lives in its
`DugContent` children (`content_list`), so that every piece of text is searchable and
annotatable in the same way, and so that whether text may be shown is decided once, on the
content that would be shown. A file in a format nothing can read is still a document: it
is listed and linked to, with no content.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | `str` | Yes | - |  |
| `name` | `str` | Yes | - |  |
| `description` | `str` | Yes | - |  |
| `type` | `"document"` | No | `"document"` |  |
| `programs` | `list[str]` | No | - |  |
| `action` | `str` | No | `""` |  |
| `parents` | `list[str]` | No | - |  |
| `parent_type` | `str` | No | `""` |  |
| `concepts` | `dict[str, object]` | No | - |  |
| `search_terms` | `list[str]` | No | - |  |
| `optional_terms` | `list[str]` | No | - |  |
| `metadata` | `dict[str, any]` | No | - |  |
| `tags` | `list[dict[str, str]]` | No | - |  |
| `resource_type` | `str` | No | `"document"` | Always 'document' for a DugDocument. |
| `repository` | `str` | No | `""` | Repository hosting this resource, e.g. 'figshare', 'zenodo', 'dataverse'. |
| `authors` | `list[str]` | No | - | Author names in citation order. |
| `doi` | `str` | No | `None` | Bare DOI of this resource, without a resolver prefix. |
| `license` | `str` | No | `""` | SPDX licence identifier; empty when unknown. |
| `document_list` | `list[str]` | No | - | IDs of the DugDocuments that came from this resource. |
| `file_name` | `str` | No | `""` | Original file name, e.g. 'README.pdf'. |
| `mime_type` | `str` | No | `""` | IANA media type, e.g. 'application/pdf'. |
| `document_type` | `str` | No | `""` | Kind of document; recommended values are listed in DOCUMENT_KINDS. |
| `content_list` | `list[str]` | No | - | IDs of this document's DugContent, in reading order. |

## DugResource

Something outside Dug that can be pointed to with a URL and a description.

The main use is the repository deposit that a study's files came from, e.g. a Figshare
article, a Zenodo or Dataverse dataset, or an OpenNeuro dataset. `name` is the deposit's
title, `description` is its description, and `action` is its landing page. A resource
with a DOI is citable. A single file within a deposit is a `DugDocument`, a subclass of
this class.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | `str` | Yes | - |  |
| `name` | `str` | Yes | - |  |
| `description` | `str` | Yes | - |  |
| `type` | `"resource"` | No | `"resource"` |  |
| `programs` | `list[str]` | No | - |  |
| `action` | `str` | No | `""` |  |
| `parents` | `list[str]` | No | - |  |
| `parent_type` | `str` | No | `""` |  |
| `concepts` | `dict[str, object]` | No | - |  |
| `search_terms` | `list[str]` | No | - |  |
| `optional_terms` | `list[str]` | No | - |  |
| `metadata` | `dict[str, any]` | No | - |  |
| `tags` | `list[dict[str, str]]` | No | - |  |
| `resource_type` | `str` | No | `"dataset"` | Kind of resource; recommended values are listed in RESOURCE_KINDS. |
| `repository` | `str` | No | `""` | Repository hosting this resource, e.g. 'figshare', 'zenodo', 'dataverse'. |
| `authors` | `list[str]` | No | - | Author names in citation order. |
| `doi` | `str` | No | `None` | Bare DOI of this resource, without a resolver prefix. |
| `license` | `str` | No | `""` | SPDX licence identifier; empty when unknown. |
| `document_list` | `list[str]` | No | - | IDs of the DugDocuments that came from this resource. |

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
| `document_list` | `list[str]` | No | - |  |
| `resource_list` | `list[str]` | No | - |  |
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
