# Dug Data Model v2

This document describes the data model schema in a human-readable format.

## Table of Contents

- [DugConcept](#dugconcept)
- [DugContent](#dugcontent)
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

A piece of a `DugResource`'s text: a heading and the body under it.

Content is the only element that holds text. A `DugResource` describes and links to a
file; if the file's text can be read, and the resource's licence allows the text to be
incorporated, it is split into DugContent children, one per heading (or a single one
when there are no headings). `name` is the heading and `content` is the text under it.
`description` is metadata about the piece, as on every other element, and is usually
empty. `parents` holds the ID of the resource the text came from, with `parent_type`
'resource' (anything else is rejected); `studies` holds the ID of the study, as on
`DugResource`, so that the study can be found without climbing through the resource.

Content carries no licence or display flag of its own: the licence is stated once, on the
resource, and content exists only when that licence permits it (see `licenses.py`). A
file whose text may not be incorporated has no content, so the case shows in the shape
of the data rather than in a flag that an index or a UI has to remember to honour.

Content is a separate element, not a list inside its resource, because Dug annotates and
indexes each element on its own: a section is sent to the annotator as one bounded text
and comes back as its own search hit, with `page` and `position` to point at. Embedded
in the resource, the text would be annotated as one PDF-sized string, or not at all, and
returned whole with every hit on the resource (see docs/how-dug-uses-elements.md).

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
| `position` | `int` | No | `0` | 0-based order of this content within its resource. |
| `level` | `int` | No | `None` | Heading depth (1 = top level) when the source format exposes it. |
| `page` | `int` | No | `None` | 1-based page this content starts on, for paginated formats. |
| `content` | `str` | Yes | - | The text under the heading. Required, so that a file written when the text was held in `description` fails to load instead of loading with no text. |
| `studies` | `list[str]` | No | - | IDs of the studies this content belongs to, as on DugResource. |

## DugResource

Anything outside Dug that has a URL, at whatever size.

A program website, a project's page on an NIH site, a press release, a Zenodo community,
the Zenodo or Figshare deposit a study's files came from, a dataset with or without a DOI,
a publication; and each file of any of these: the deposit's README, the paper's PDF, the
dataset's XLSX, the HTML of the press release. `name` is its title, `description` its
description, `action` its landing or download page. `resource_type` says what it is (see
`RESOURCE_KINDS`); `repository`, `authors`, `doi` and `license` say where it is published
and how to cite it. A resource that is one file in one format also has `file_name` and
`mime_type`; a landing page has neither, and a web page captured as text has
`mime_type="text/html"` and no `file_name`. A UI renders every resource the same way --
a title, a link, a kind and a format -- in a tree or in a flat list.

Resources form a tree. A resource's parent is its study (`parent_type="study"`) or the
resource it is part of (`parent_type="resource"`): a file hangs off the deposit it was
downloaded from, a deposit off its Zenodo community, a press release page off the project
website, a supplementary table off the paper. A file that came from no known resource
hangs off the study. A resource lists nothing: its children name it in `parents`, and
`studies` names the study from any depth. So a UI that shows only the resources whose
parent is the study loses nothing, and one that follows `parents` can show the whole
tree. A resource with the wrong parent is found by `studies` and by search, but shown in
the wrong place.

A resource holds no text of its own. Whatever can be read out of a file lives in its
`DugContent` children, under the file's `license`: a producer emits content only when
`can_include_content(resource.license)` is true (see `licenses.py`), so a file whose text
could not be read -- a scanned PDF, a format no parser handles -- or may not be
incorporated is a resource with no content, still listed, linked to, and found by its
title and description. Whether a producer emits a resource for every file in a deposit
or only for the ones a person would read is its choice: the reference producer
inventories data files in the deposit's `metadata` and emits no resource for them.

Earlier versions had a separate `DugDocument` type for a file, with a `DugCitable` base
class for the fields it shared with `DugResource`. Every awkward case -- a press release
page captured as text, a PDF report with a DOI of its own, a document hanging off a study
because no deposit was known -- came from drawing that line, and a UI had to render two
types; one type in a tree needs neither. A file written with `"type": "document"` does
not load.

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
| `resource_type` | `str` | No | `""` | Kind of resource; recommended values are listed in RESOURCE_KINDS. A file that is its parent in one format has its parent's kind. |
| `repository` | `str` | No | `""` | Slug of the repository hosting this resource; recommended values are listed in REPOSITORY_KINDS. |
| `authors` | `list[str]` | No | - | Author names in citation order. |
| `doi` | `str` | No | `""` | Bare DOI of this resource, without a resolver prefix; empty when unknown. |
| `license` | `str` | No | `""` | SPDX licence identifier, or a `LicenseRef-` name for terms SPDX does not list (e.g. all rights reserved); empty when unknown. Governs the DugContent under it. |
| `file_name` | `str` | No | `""` | Original file name when the resource is one file, e.g. 'README.pdf'; empty for a landing page. |
| `mime_type` | `str` | No | `""` | IANA media type when the resource is one file, e.g. 'application/pdf'; empty for a landing page. |
| `studies` | `list[str]` | No | - | IDs of the studies this resource belongs to, at any depth below them; `parents` names only the element directly above. |

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

A study does not list its resources; they name it in `parents`, and `build_parent_map()`
or a query on `parents` finds them, while `studies` on every resource and content element
under the study finds them all at once. That is because the study and its resources need
not come from the same producer (DUG-796: the non-data-dictionary producer emits resources
for a study the MDS ingest emits), so a list on the study would be complete only by luck.
Its publications are `DugResource`s with `resource_type` 'publication' or 'preprint'.
Earlier versions had `publications`, a list of bare strings nothing read, then
`document_list` and `resource_list`; a file that still carries any of them loads without it.

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
