# dug-data-model

Reusable data model for the [Dug](https://github.com/helxplatform/dug) semantic search system.

This package provides:
1. **Versioned data models** (e.g., `v2/`) - Ready-to-use Pydantic models for Dug-indexed data
2. **Scaffold** - A CLI tool for bootstrapping new data model versions
3. **Schema generation** - JSON Schema and Markdown documentation auto-generated on build

## Installation

```bash
pip install dug-data-model
```

## Requirements

- Python 3.12+
- Pydantic >= 2.0

## Quick Start

### Using a versioned model

```python
from dug_data_model.v2 import DugVariable, DugStudy, DugConcept

# Create a study
study = DugStudy(
    id="phs000001",
    name="My Study",
    description="A biomedical research study",
    abstract="This study investigates ...",
)

# Create a variable and attach it to the study
variable = DugVariable(
    id="phv00000001",
    name="BMI",
    description="Body mass index",
    parents=[study.id],
    parent_type="study",
)

print(variable.ml_ready_desc)
# -> "BMI: Body mass index"

print(variable.get_searchable_dict())
```

### Deserializing a mixed list

`DugElementParsedList` uses Pydantic's discriminated unions to correctly deserialize a JSON array containing a mix of element types:

```python
from dug_data_model.v2 import DugElementParsedList
import json

data = json.loads("""
[
  {"id": "s1", "name": "Study 1", "description": "...", "type": "study"},
  {"id": "v1", "name": "var1",    "description": "...", "type": "variable"}
]
""")

elements = DugElementParsedList.validate_python(data)
```

### Resources and their content

Studies come with more than data dictionaries: repository deposits, READMEs, protocols,
publications, project websites. Two element types describe them:

- **`DugResource`** — anything outside Dug that has a URL, at whatever size: a program website,
  a project's page on an NIH site, a press release, a Zenodo community, the Zenodo or Figshare
  deposit a study's files came from, a dataset with or without a DOI, a publication or
  preprint, and each file of any of these: the deposit's README, the paper's PDF, the
  dataset's XLSX, the HTML of the press release. `resource_type` says what it is (see
  `RESOURCE_KINDS`); `repository`, `authors`, `doi` and `license` say where it is published
  and how to cite it. A resource that is one file in one format also has `file_name` and
  `mime_type`; a landing page has neither. A resource holds **no text of its own**.
- **`DugContent`** — a piece of a resource's text: a heading (`name`) and the body under it
  (`content`). This is the only element that carries text, and it exists only when the
  resource's licence allows the text to be incorporated.

Resources form a tree under the study:

```
DugStudy
 ├─ DugResource   the deposit        parents=[study],   parent_type="study",    studies=[study]
 │   ├─ DugResource   its README       parents=[deposit], parent_type="resource", studies=[study]
 │   │   └─ DugContent   one heading    parents=[readme],  parent_type="resource", studies=[study]
 │   └─ DugResource   a data file      (if the producer chose to emit one)
 └─ DugResource   the paper          parents=[study],   parent_type="study"
     ├─ DugResource   its PDF          resource_type="publication", like its parent
     └─ DugResource   a supplement     resource_type="supplementary_table"
```

A resource's parent is its study or the resource it is part of: a file hangs off the
deposit it was downloaded from, a deposit off its Zenodo community, a press release page off
the project website, a supplement off its paper. A file that came from no known resource
hangs off the study. Content's parent is always the resource whose text it is. **Nothing
lists its children**: a child names its parent in `parents`, and a consumer finds children
with `build_parent_map()` or `get_children()` in `dug_data_model.v2`, or in an index with a
query on `parents`. That is because the study and its resources need not come from the same
producer: under [DUG-796](https://renci.atlassian.net/browse/DUG-796) the non-data-dictionary
producer emits resources for a study that the MDS ingest emits separately, so a list on the
study could never be complete, and the same holds one level down when text is re-extracted
or withheld after a licence review. `parents` is the one link that a producer emitting only
the children can write.

Going the other way, `parents` reaches only the next element up, so from a piece of content
the study is three hops away, and Dug's index can filter on `parents` only one hop at a
time. So every resource and content element also carries `studies`, the IDs of the studies
it belongs to at any depth, written by the producer, which knows the study even when it does
not emit it. One query on `studies` finds everything in a study; see
[docs/how-dug-uses-elements.md](docs/how-dug-uses-elements.md) for what Dug does with these
fields. `validate_references()` checks that every `parents`, `studies`, `variable_list` and
`section_list` ID resolves within a collection and points at the right type of element.

Which file is "the" publication? The child whose `resource_type` matches its parent's: the
PDF of a `publication` is a `publication` with `mime_type="application/pdf"`, a protocol's PDF
is a `protocol`. A file that is something of its own under the same parent -- a
`supplementary_table`, a `readme` -- has its own kind. There is no flag for this, and no
`article` kind: the convention covers every kind of resource the same way.

The example below is HEAL study [HDP00009](https://healdata.org/portal/discovery/HDP00009)
in the shape the reference producer (see below) writes; the whole record is in
[`tests/fixtures/heal_hdp00009.json`](tests/fixtures/heal_hdp00009.json). The study has two
Figshare deposits, each with a PDF README; only the first deposit is shown here, and long
descriptions and the author list are cut short. The preprint at the end is not in the
fixture: it is the paper the README asks users to cite, written as the HEAL Platform's
`primary_publications` would give it, and shows a publication as a resource with no file
under it.

```python
from dug_data_model.v2 import DugContent, DugResource, DugStudy

dataset = DugResource(
    id="HDP00009/resources/doi-org-10-6084-m9-figshare-24867198",
    name="Treating pain in sickle cell disease by means of focused ultrasound neuromodulation "
         "(Behavior assessments and analyses)",
    description="We have demonstrated a novel transcranial focused ultrasound technology ...",
    action="https://doi.org/10.6084/m9.figshare.24867198",  # landing page
    resource_type="dataset",                 # see RESOURCE_KINDS
    repository="figshare",
    authors=["Min Gon Kim", "Kai Yu", "Chih-Yu Yeh"],     # the first 3 of 12
    doi="10.6084/m9.figshare.24867198",
    license="CC-BY-4.0",
    metadata={"files": {"count": 9, "bytes": 410870, "by_extension": {".pdf": 1, ".xlsx": 8}}},
    parents=["HDP00009"], parent_type="study",
    studies=["HDP00009"],
)

readme = DugResource(
    id="HDP00009/assets/24867198/README.pdf",
    name="README: behavior assessments and analyses",  # display title
    description="",
    action=dataset.action,                   # the deposit, as the file has no DOI of its own
    resource_type="readme",                  # its own kind: it is not the deposit in PDF form
    repository="figshare",
    license="CC-BY-4.0",                     # the deposit's licence unless the file states its own;
                                             # it allows the text below, see CONTENT_LICENSES
    file_name="README.pdf",                  # what makes this resource a file
    mime_type="application/pdf",
    metadata={"page_count": 2},
    parents=[dataset.id], parent_type="resource",
    studies=["HDP00009"],
)

section = DugContent(
    id="HDP00009/assets/24867198/README.pdf/readmepdf",
    name="README.pdf",                       # the heading; this PDF has none, so its file name
    description="",                          # metadata about this piece, as on every element
    content="README\n\nThis readme document describes the organized behavior "
            "assessment with analysis. ...",  # the text under the heading
    action=readme.action,                    # where to read the text at its source
    position=0, page=1,
    parents=[readme.id], parent_type="resource",
    studies=["HDP00009"],
)

preprint = DugResource(
    id="HDP00009/resources/doi-org-10-1101-2022-12-07-519518",
    name="Low-intensity transcranial focused ultrasound changes pain-associated behaviors by "
         "modulating pain processing brain circuits",  # from Crossref; the DOI itself if unresolved
    description="",
    action="https://doi.org/10.1101/2022.12.07.519518",
    resource_type="preprint",                # its PDF, if fetched, would be a "preprint" with
    repository="biorxiv",                    # mime_type="application/pdf" under it
    authors=["Min Gon Kim", "Kai Yu", "Chih-Yu Yeh"],
    doi="10.1101/2022.12.07.519518",
    parents=["HDP00009"], parent_type="study",
    studies=["HDP00009"],
)

study = DugStudy(
    id="HDP00009",
    name="Treating pain in sickle cell disease by means of focused ultrasound neuromodulation",
    description="Researchers will develop a novel transcranial focused ultrasound (tFUS) ...",
    metadata={"appl_id": 9932691},
)   # the study lists nothing: its resources name it in `parents` and `studies`
```

Text is only ever incorporated under a licence that allows it, and the licence is stated once,
on the resource. A producer emits `DugContent` for a file only when
`can_include_content(resource.license)` is true; the licences that count are listed in
`CONTENT_LICENSES`, so that every producer draws the line in the same place, and NonCommercial
and NoDerivatives licences are left for a person to decide. So if content exists, its text may
be indexed and shown, and nothing downstream has to check a flag. A file whose licence does
not allow it is still a resource, with its `license` and no content: it is found by its title
and description, and the UI sends the user to `action` to read it at the source. A file whose
format nothing can read is a resource with no content in the same way.

`resource_type` is a free string; `RESOURCE_KINDS` lists the recommended values, coarse on
purpose. A finer kind, such as one of PubMed's
[publication types](https://pubmed.ncbi.nlm.nih.gov/help/#publication-types) ("Review",
"Randomized Controlled Trial"), belongs in `tags` as `{"category": "publication_type", "value":
...}`, which every element has and which an index can filter on, rather than in a longer
`RESOURCE_KINDS`.

#### Shapes that were tried and dropped

Recorded so that the next person does not go the same way.

- **A separate `DugDocument` type for a file**, sharing its citation fields with
  `DugResource` through a `DugCitable` base class. Every awkward case came from drawing the
  line between the two: a press release page captured as text was both; a PDF report with a
  DOI was either; a document whose deposit was unknown hung off the study while its siblings
  hung off a resource; and a UI had to render two types. One type in a tree needs none of
  that.
- **Child lists** (`document_list`, `resource_list`, `content_list`, and before them
  `DugStudy.document_list` and `resource_list`), validated in both directions against
  `parents`. Dug never read them, reading order is in `DugContent.position`, and the
  multi-producer argument that removed them from the study applies one level down too.
- **Content embedded in its resource** as a list, so that a producer emits one object per
  file. Dug annotates and indexes each element on its own, so embedded text would be sent
  to the annotator as one PDF-sized string (or not at all) and returned whole with every hit
  on the resource; a separate element is annotated as one bounded section and is its own hit.
- **Text behind a `can_display_content` flag** on the content, with every document's text in
  the index. That stated permission without enforcing it, since Dug's endpoints return the
  indexed `_source` as is; now content exists only when the licence allows it.

#### Reference producer conventions

The model leaves several things to the producer. These are the conventions of the reference
producer,
[heal-non-data-dictionaries](https://github.com/heal-data-stewards/heal-non-data-dictionaries),
recorded so that a second producer, or a UI, does not have to reinvent or guess them. They are
not schema: nothing here is validated. (The producer still writes the previous shape, with
`DugDocument`; this is the shape it is being moved to.)

- **IDs.** A resource with a URL is `<study>/resources/<url-slug>` (the URL's host and path,
  lower-cased, non-alphanumerics collapsed to `-`), or `<parent resource>/<url-slug>` when it
  is inside another resource. A file is `<study>/assets/<path under assets/>`, its place in
  the curated inputs, whichever resource it hangs off, so that re-curating where a file came
  from does not change its ID. A content element is `<file>/<heading-slug>`, with `_2`, `_3`
  on repeated headings and `section-N` (N = 1-based position) when a heading has nothing
  sluggable in it. A resource that belongs to several studies (a paper two studies cite)
  should get one ID that embeds neither study, with both in `parents` and `studies`; the
  producer does not do this yet, as it works one study at a time.
- **`action`.** A resource with a URL links to its landing page. A file links to an explicit
  curated URL, else `https://doi.org/<doi>` when it has its own DOI, else the deposit URL it
  was downloaded from. Each content element copies its resource's `action`.
- **Licence.** A file takes its own curated licence, else its deposit's, else a study-level
  default; its text becomes content only when `can_include_content(resource.license)` is
  true, else the file is emitted with no content.
- **`metadata` keys.** On a deposit: `files = {"count": N, "bytes": B, "by_extension":
  {".nev": 13, ...}}`, an inventory of every file in the deposit including those that became no
  resource (`.nii.gz` keeps its double extension; files without one are `"(none)"`). On a
  file: `page_count` for paginated formats; `embedded` (`title`, `author`, `creator`,
  `created`, `modified`, as stored in the file, for provenance only, since they are usually an
  OS account name or blank); `text_extraction` when a file has no content: `"none"` (no
  text layer), `"no_handler"` (a curated file no parser handles) or `"not_licensed"` (the
  licence does not allow the text to be incorporated). On a study: `appl_id` (NIH
  application id), `notes` (curator's notes), and anything else from the study's curated
  metadata.
- **Which files become resources.** Files a parser can read (Word, PDF, Markdown, plain text;
  spreadsheets and CSV when asked for). A curated file no parser handles becomes a resource
  with no content. Everything else -- recordings, scans, images, primary data -- is counted in
  its deposit's `files` inventory and nothing more. The model allows a resource for any file
  (`resource_type="data"`); this producer chooses not to emit one.
- **Publications.** The HEAL Platform's `study_metadata.findings.primary_publications` is a list
  of DOI URLs. Each becomes a `DugResource` with `resource_type="publication"` (or
  `"preprint"`), `action` the URL, `doi` the bare DOI, and `name` the title when the DOI
  resolves (Crossref) and the DOI itself when it does not, since `name` is required. No
  file is emitted under it unless the full text is fetched. A PubMed ID goes in
  `metadata["pmid"]`, so that a publication can be matched to the knowledge graph's PubMed
  nodes; the model has no field for it because only publications have one.
- **Links between resources that are not containment.** A paper is about a deposit, a deposit
  supplements a paper: DataCite's `relatedIdentifiers`, which Figshare and Zenodo serve. These
  are copied as given into `metadata["related_identifiers"]` on the resource (a list of
  `{"relation": "IsSupplementTo", "identifier": "10.1101/...", "type": "DOI"}`), not expressed
  through `parents`, which is for containment only. A field for them can come when a UI needs
  to show them.
- **Download counts** from a repository API go in `metadata["downloads"]` on the resource, as
  an integer, with `metadata["downloads_as_of"]` holding the ISO date they were read.

## Scaffold: Creating a New Model Version

Use the scaffold CLI to generate a new data model version inside the package. It copies the
scaffold's files rather than importing them, so a released version does not change when the
scaffold does. `utils.py` and `validation.py` do not depend on the version, so they are kept
identical in the scaffold and in `v2/`: make a fix in both, and `tests/test_scaffold_copies.py`
fails if one is forgotten.

```bash
# Create v3 of the data model
python -m dug_data_model.scaffold new v3

# Overwrite an existing version
python -m dug_data_model.scaffold new v3 --force
```

This creates a new version directory:

```
src/dug_data_model/v3/
├── __init__.py      # Package exports
├── base.py          # DugElement base class
├── concept.py       # DugConcept class
├── types.py         # Utility types and examples
├── utils.py         # Helper functions
└── py.typed         # PEP 561 marker
```

### What you get

The generated version includes:

- **`DugElement`** - Base class for any searchable entity
- **`DugConcept`** - An ontological concept that links elements to identifiers and knowledge graph answers

### What you need to add

After generating, you must customize the version for your use case:

#### 1. Add element subclasses

Create subclasses of `DugElement` for your domain (e.g., `variable.py`):

```python
from typing import Literal, Any
from .base import DugElement

class DugVariable(DugElement):
    type: Literal["variable"] = "variable"
    data_type: str = "text"

    def get_searchable_dict(self) -> dict[str, Any]:
        base = super().get_searchable_dict()
        return {**base, "data_type": self.data_type}
```

A field that holds the IDs of other elements should carry the `References` marker, with the
`type` those elements should have, so that `validate_references()` checks it. Its name does
not matter:

```python
from typing import Annotated
from pydantic import Field
from .base import DugElement, References

class DugStudy(DugElement):
    type: Literal["study"] = "study"
    variable_list: Annotated[list[str], References("variable")] = Field(default_factory=list)
```

#### 2. Define your Indexable union

In `types.py`, define a union of all element types that can be indexed:

```python
from typing import Annotated
from pydantic import Field, TypeAdapter

from .concept import DugConcept
from .variable import DugVariable
from .study import DugStudy

# Union of all element types
Indexable = DugConcept | DugVariable | DugStudy

# Discriminated union for polymorphic JSON parsing
DiscriminatedIndexable = Annotated[Indexable, Field(discriminator="type")]

# TypeAdapter for deserializing mixed lists
DugElementParsedList = TypeAdapter(list[DiscriminatedIndexable])
```

#### 3. Export your classes

Update `__init__.py` to export your new classes:

```python
from .variable import DugVariable
from .study import DugStudy
from .types import Indexable, DugElementParsedList

__all__ = [
    # ... existing exports ...
    "DugVariable",
    "DugStudy",
    "Indexable",
    "DugElementParsedList",
]
```

## Schema Generation

JSON Schema and Markdown documentation are automatically generated for each data model version during package builds. The generated files are included in the installed package under `dug_data_model/schemas/`.

You can also generate schemas manually via the CLI:

```bash
# Generate JSON Schema
python -m dug_data_model.scaffold schema v2 -o schema.json

# Generate Markdown documentation
python -m dug_data_model.scaffold schema v2 --format markdown -o SCHEMA.md
```

Copies are also committed in `src/dug_data_model/schemas/`, and `tests/test_schemas.py` fails
when they no longer match the models. After changing a model, regenerate them:

```bash
python -m dug_data_model.scaffold schema v2 -o src/dug_data_model/schemas/v2_schema.json
python -m dug_data_model.scaffold schema v2 --format markdown -o src/dug_data_model/schemas/v2_schema.md
```

## Data Model Reference

### Core classes

| Class | `type` field | Description |
|---|---|---|
| `DugElement` | *(base)* | Base class for any searchable entity |
| `DugConcept` | `"concept"` | Ontological concept; holds identifiers and KG answers |

### Versioned models (e.g., `v2/`)

| Class | `type` field | Description |
|---|---|---|
| `DugVariable` | `"variable"` | A data variable (e.g., dbGaP variable or CDE) |
| `DugStudy` | `"study"` | A research study; its resources name it in their `parents` and `studies` |
| `DugSection` | `"section"` | A section or instrument within a study |
| `DugResource` | `"resource"` | Anything external with a URL, at any size, in a tree: a website, a deposit, a publication, and each file of one (`file_name`, `mime_type`); holds no text itself |
| `DugContent` | `"content"` | A headed piece of a `DugResource`'s text, held in `content`; the only element with text, present only under a licence that allows it |

## Development

```bash
# Install in editable mode with dev extras
pip install -e ".[dev]"

# Run tests
pytest

# Run type checking
mypy src
```

## Versioning

This package follows [Semantic Versioning](https://semver.org/). The `v2/` subpackage corresponds to version 2 of the Dug data model.

## License

MIT License. See [LICENSE](LICENSE) for details.
