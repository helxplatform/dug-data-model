# Resource kinds

What each recommended value of `DugResource.resource_type` means, and how to choose between
neighbours. The values themselves are `RESOURCE_KINDS` in
[`src/dug_data_model/v2/resource.py`](../src/dug_data_model/v2/resource.py), in the order of
the headings below; `tests/test_model.py` fails if the two disagree, so a new kind is added to
both.

`resource_type` says what a resource *is*, whether it is a landing page or a single file. It is
a free string, so a new kind needs no model release, but a producer should use these values so
that a filter on `resource_type` finds the same things from every producer. The list is coarse
on purpose. A finer kind, such as one of PubMed's
[publication types](https://pubmed.ncbi.nlm.nih.gov/help/#publication-types) ("Review",
"Randomized Controlled Trial"), goes in `tags` as `{"category": "publication_type", "value":
...}`, which an index can filter on, rather than in a longer list here. A producer that needs a
kind nobody has listed uses its own lower-case value and proposes it here; `other` is for what
nobody would filter on.

## A file's kind

A file that is its parent in one format has its parent's kind. The PDF of a publication is a
`publication` with `mime_type="application/pdf"` under the `publication` that is the work; a
protocol's PDF is a `protocol` under the protocol; a dataset published as a single CSV is a
`dataset`. So "the full text" needs no flag of its own: it is the child whose kind matches its
parent's.

A file that is something of its own has its own kind, whatever its parent: a `readme` under a
dataset, a `supplementary_table` under a publication, `data` under a dataset.

## Published works

### `publication`

A work published after peer review or editorial selection: a journal article, a conference
paper, a book or chapter, a data paper, a thesis or dissertation.

- **Not a preprint.** A work posted without peer review is a `preprint`, even on a server
  that later links it to the published version. When the work is published, the publication
  is a second resource with its own DOI; the preprint keeps its kind. Crossref links the two
  with an `is-preprint-of` relation, which goes in the preprint's
  `metadata["related_identifiers"]` as the README's producer conventions describe.
- **Not a report.** A document an organisation issues itself, outside a journal or press, is
  a `report`.

### `preprint`

A work posted publicly without (or before) peer review: bioRxiv, medRxiv, arXiv, SSRN,
Research Square, OSF Preprints. See `publication` for what happens when it is published.

### `report`

A document issued by an organisation rather than a publisher: a technical or progress report,
a white paper, a project deliverable, a working paper, a policy brief.

### `poster`

A conference poster, as a landing page or as a file.

### `presentation`

Slides from a talk, or a recording of one.

### `patent`

A patent or a patent application.

## Data and code

### `dataset`

A published collection of data with its own landing page, usually a repository deposit with a
DOI: a Figshare item, a Zenodo record, an OpenNeuro or Dataverse dataset. A deposit is a
`dataset` even when it also holds a README or code, since that is what it was deposited as;
one deposited as software is `software`.

- **Not `data`.** A `dataset` is never one file of a dataset, and `data` is never a collection.
  A dataset published as a single file is still a `dataset` (see "A file's kind").

### `data`

One data file that a producer chose to emit as a resource: a spreadsheet, a CSV, an archive, a
recording, an image. Its parent is usually the `dataset` it was downloaded from, or the study
when it came from no known deposit. A producer may instead count data files only in their
deposit's `metadata`; the reference producer does.

### `supplementary_table`

A table published as a supplement to a publication, usually as its child. A supplement that is
not a table has the kind of what it is: supplementary methods are `methods`, a supplementary
data file is `data`.

### `software`

Source code or a packaged tool: a GitHub repository, a software deposit on Zenodo, a script or
notebook file.

## Documentation

### `readme`

The file that introduces a deposit or a code repository, usually named `README`.

### `protocol`

The plan a study follows, written before or while it runs: a clinical or IRB-approved protocol,
a protocols.io entry, a registration on ClinicalTrials.gov or OSF, a data management plan.

- **Not `methods`.** A protocol says what will be done; `methods` says what was done.

### `methods`

How data were actually collected or processed, written to accompany them: a methods document,
a processing or analysis description, a deviation log.

### `manual`

Instructions for using something: a user guide, an instrument or equipment manual, a codebook
or data dictionary distributed as a file. (A data dictionary that Dug ingests becomes
`DugVariable`s; its file can still be a `manual` resource.)

## On the web

### `website`

A site or page that is none of the kinds above: a program or project site, an NIH RePORTER
project page, a lab page, a Zenodo community, an interactive tool.

### `press_release`

A news item about the study or its results, whether issued by the institution or funder or
published by the press.

## Anything else

### `other`

None of the kinds above, and nothing a user would filter on.

## Mapping from DOI metadata

A producer that resolves a DOI can take the kind from the registry's type. These tables give
the usual mapping; when the resource itself says otherwise, the resource wins.

**DataCite `resourceTypeGeneral`**, served for Figshare, Zenodo, Dataverse and OSF DOIs; read
from the DataCite Metadata Schema 4.7 (`datacite-resourceType-v4.xsd`, 2026-03-03) on
2026-10-15.

| DataCite | Kind |
|---|---|
| `JournalArticle`, `ConferencePaper`, `Book`, `BookChapter`, `DataPaper`, `Dissertation` | `publication` |
| `Preprint` | `preprint` |
| `Report` | `report` |
| `Poster` | `poster` |
| `Presentation` | `presentation` |
| `Dataset`, `Collection` of datasets | `dataset` |
| `Image`, `Sound`, `Audiovisual` | `data` (a recorded talk is a `presentation`) |
| `Software`, `ComputationalNotebook`, `Workflow` | `software` |
| `StudyRegistration`, `OutputManagementPlan` | `protocol` |
| `InteractiveResource`, `Service`, `Project` | `website` |
| `Text` | whichever kind the text is |
| `Award`, `ConferenceProceeding`, `Event`, `Instrument`, `Journal`, `Model`, `PeerReview`, `PhysicalObject`, `Standard`, `Other` | `other` |

**Crossref `type`**, served for most journal and preprint DOIs; read from
`https://api.crossref.org/types` on 2026-10-15.

| Crossref | Kind |
|---|---|
| `journal-article`, `proceedings-article`, `book`, `edited-book`, `monograph`, `reference-book`, `book-chapter`, `book-section`, `book-part`, `book-track`, `reference-entry`, `dissertation` | `publication` |
| `posted-content` (subtype `preprint`) | `preprint` |
| `report`, `report-component` | `report` |
| `dataset`, `database` | `dataset` |
| `component` | whichever kind it is: often a `supplementary_table` or `data` under its publication |
| `peer-review`, `grant`, `standard`, `other`, and the containers (`journal`, `journal-volume`, `journal-issue`, `proceedings`, `proceedings-series`, `book-set`, `book-series`, `report-series`) | `other` |
