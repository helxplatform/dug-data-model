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
links to a file; if the file's text can be read, and the document's licence allows the
text to be incorporated, it is split into DugContent children, one per heading (or a
single one when there are no headings). `name` is the heading and `content` is the text
under it. `description` is metadata about the piece, as on every other element, and is
usually empty. `parents` holds the ID of the containing document, with `parent_type` set
to 'document'; `studies` holds the ID of the study, as on `DugCitable`, so that the study
can be found without climbing through the document.

Content carries no licence or display flag of its own: the licence is stated once, on the
document, and content exists only when that licence permits it (see `licenses.py`). A
document whose text may not be incorporated has no content, so the case shows in the
shape of the data rather than in a flag that an index or a UI has to remember to honour.

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
| `content` | `str` | Yes | - | The text under the heading. Required, so that a file written when the text was held in `description` fails to load instead of loading with no text. |
| `studies` | `list[str]` | No | - | IDs of the studies this content belongs to, as on DugCitable. |

## DugDocument

One file in one format: a README, a protocol PDF, a paper's PDF, a data XLSX, ...

A `DugResource` is the thing with a URL (a deposit, a publication, a web page); a document
is one file of it. Its parent is that resource or, when it came from no known resource,
its study. Like a resource, a document has a title (`name`), a summary (`description`), a
landing or download URL (`action`), and the citation fields `repository`, `authors`, `doi`
and `license`, which both get from `DugCitable`; it adds what only a file has:
`file_name`, `mime_type` and `document_type`. A web page captured as text is a document
with `mime_type="text/html"` and no `file_name`, under the page's resource. A document is
not a resource: `isinstance(x, DugResource)` is false for it, so code that picks out
deposits by class does not pick up their files too.

A document holds no text of its own. Whatever could be read out of the file lives in its
`DugContent` children, which name it in `parents` and order themselves by `position`
(the document does not list them), so that every piece of text is searchable and
annotatable in the same way. The document's `license` decides whether there is any
content at all: a producer emits content only when the licence allows the text to be
incorporated (`can_include_content()` in `licenses.py`). A document is still a document
when it has no content, whether because its text could not be read -- a scanned PDF, or a
file the curator named that no parser handles -- or because its licence does not allow
it: it is listed and linked to, and found by its title and description. Whether a producer
emits a document for every file in a deposit, or only for the ones a person would read, is
the producer's choice: the reference producer inventories data files (recordings, scans,
spreadsheets of primary data) in the resource's `metadata` and emits no document for them.

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
| `repository` | `str` | No | `""` | Slug of the repository hosting this item; recommended values are listed in REPOSITORY_KINDS. |
| `authors` | `list[str]` | No | - | Author names in citation order. |
| `doi` | `str` | No | `""` | Bare DOI of this item, without a resolver prefix; empty when unknown. |
| `license` | `str` | No | `""` | SPDX licence identifier, or a `LicenseRef-` name for terms SPDX does not list (e.g. all rights reserved); empty when unknown. |
| `studies` | `list[str]` | No | - | IDs of the studies this item belongs to, at any depth below them; `parents` names only the element directly above. |
| `file_name` | `str` | No | `""` | Original file name, e.g. 'README.pdf'. |
| `mime_type` | `str` | No | `""` | IANA media type, e.g. 'application/pdf'. |
| `document_type` | `str` | No | `""` | Kind of document; recommended values are listed in DOCUMENT_KINDS. |

## DugResource

Anything outside Dug that has a URL, at whatever size.

A program website, a project's page on an NIH site, a press release, a Zenodo community,
the Zenodo or Figshare deposit a study's files came from, a dataset with or without a DOI,
a publication: each is a resource. `name` is its title, `description` its description,
`action` its landing page; a resource with a DOI is citable. The dividing line from a
`DugDocument` is format: a resource is the thing, a document is one file of it in one
format. A deposit's README, a paper's PDF, a dataset's XLSX and the HTML of a press release
are documents, which share the citation fields (`repository`, `authors`, `doi`, `license`)
through `DugCitable` but are not resources.

A resource's parent is its study or, for a deposit in a Zenodo community or a page on a
website, the enclosing resource (`parent_type="resource"`). A resource lists neither its
documents nor the resources inside it: they name it in `parents`, as resources name the
study, and `studies` takes a consumer straight to the study from any depth. Earlier
versions had `document_list` and `resource_list`; a file that still carries them loads
without them.

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
| `repository` | `str` | No | `""` | Slug of the repository hosting this item; recommended values are listed in REPOSITORY_KINDS. |
| `authors` | `list[str]` | No | - | Author names in citation order. |
| `doi` | `str` | No | `""` | Bare DOI of this item, without a resolver prefix; empty when unknown. |
| `license` | `str` | No | `""` | SPDX licence identifier, or a `LicenseRef-` name for terms SPDX does not list (e.g. all rights reserved); empty when unknown. |
| `studies` | `list[str]` | No | - | IDs of the studies this item belongs to, at any depth below them; `parents` names only the element directly above. |
| `resource_type` | `str` | No | `"dataset"` | Kind of resource; recommended values are listed in RESOURCE_KINDS. |

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

A research study.

A study does not list its resources and documents; they name it in `parents`, and
`build_parent_map()` or a query on `parents` finds them. That is because the study and
its resources need not come from the same producer (DUG-796: the non-data-dictionary
producer emits resources and documents for a study the MDS ingest emits), so a list on
the study would be complete only by luck. Its publications are `DugResource`s with
`resource_type` 'publication' or 'preprint'. Earlier versions had `publications`, a list
of bare strings nothing read, then `document_list` and `resource_list`; a file that still
carries any of them loads without it.

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
