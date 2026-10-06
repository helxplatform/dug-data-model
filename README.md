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

### Documents and the resources they come from

Studies often come with files that are not data dictionaries: READMEs, protocols, final
reports, posters. Three element types describe them, one per level:

- **`DugResource`** — something outside Dug with a URL: chiefly the repository deposit (e.g. a
  Zenodo dataset) that a study's files were downloaded from, but also a program website, a
  software repository or a publication.
- **`DugDocument`** — a single file. Like a resource it has a title, description and link,
  and it shares the citation fields `repository`, `authors`, `doi` and `license` with
  `DugResource` through their common base class, `DugCitable`; it adds `file_name`,
  `mime_type` and `document_type`. A document is not a resource, so
  `isinstance(x, DugResource)` picks out deposits only (`isinstance(x, DugCitable)` picks out
  both). A document holds **no text of its own**.
- **`DugContent`** — a piece of a document's text: a heading (`name`) and the body under it
  (`content`). This is the only element that carries text, and it exists only when the
  document's licence allows the text to be incorporated.

The example below is a shortened copy of HEAL study
[HDP00009](https://healdata.org/portal/discovery/HDP00009) as the reference producer (see
below) writes it; the whole record is in
[`tests/fixtures/heal_hdp00009.json`](tests/fixtures/heal_hdp00009.json). The study has two
Figshare deposits, each with a PDF README; only the first deposit is shown here, and long
descriptions and the author list are cut short.

```python
from dug_data_model.v2 import DugContent, DugDocument, DugResource, DugStudy

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
    document_list=["HDP00009/assets/24867198/README.pdf"],
)

readme = DugDocument(
    id="HDP00009/assets/24867198/README.pdf",
    name="README: behavior assessments and analyses",  # display title
    description="",
    action=dataset.action,                   # the deposit, as the file has no DOI of its own
    repository="figshare",                   # a DugCitable field, like license
    license="CC-BY-4.0",                     # the deposit's licence unless the file states its own;
                                             # it allows the text below, see CONTENT_LICENSES
    file_name="README.pdf",
    mime_type="application/pdf",
    document_type="readme",                  # see DOCUMENT_KINDS
    metadata={"page_count": 2},
    parents=[dataset.id], parent_type="resource",
    content_list=["HDP00009/assets/24867198/README.pdf/readmepdf"],
)

section = DugContent(
    id="HDP00009/assets/24867198/README.pdf/readmepdf",
    name="README.pdf",                       # the heading; this PDF has none, so its file name
    description="",                          # metadata about this piece, as on every element
    content="README\n\nThis readme document describes the organized behavior "
            "assessment with analysis. ...",  # the text under the heading
    action=readme.action,                    # where to read the text at its source
    position=0, page=1,
    parents=[readme.id], parent_type="document",
)

study = DugStudy(
    id="HDP00009",
    name="Treating pain in sickle cell disease by means of focused ultrasound neuromodulation",
    description="Researchers will develop a novel transcranial focused ultrasound (tFUS) ...",
    metadata={"appl_id": 9932691},
    resource_list=[dataset.id], document_list=[readme.id],
)
```

An element has a single `parent_type`, so a document's parent is either its resource or,
when it did not come from a known resource, its study. `DugStudy.document_list` lists every
document in the study either way. `validate_references()` checks that all of these IDs
resolve within a collection, that each points at the right type of element (a `content_list`
names content, a `parents` entry has the element's `parent_type`), and that a document's
`content_list` and a resource's `document_list` agree with their children's `parents`.
`DugStudy.document_list` is not held to that last rule, since it also lists documents whose
parent is a resource.

Going the other way, from a piece of content up to its study, follows `parents` through the
document and then the resource: three hops, or two when the document hangs off the study
directly. That is deliberate. A content element records only its document, and a document
only where it came from; the study lists its documents and resources directly, so a consumer
that starts from the study never has to climb. `build_parent_map()` and `get_children()` in
`dug_data_model.v2` walk the chain in either direction.

Text is only ever incorporated under a licence that allows it, and the licence is stated once,
on the document. A producer emits `DugContent` for a document only when
`can_include_content(document.license)` is true; the licences that count are listed in
`CONTENT_LICENSES`, so that every producer draws the line in the same place, and NonCommercial
and NoDerivatives licences are left for a person to decide. So if content exists, its text may
be indexed and shown, and nothing downstream has to check a flag. A document whose licence does
not allow it is still a document, with its `license` and no content: it is found by its title
and description, and the UI sends the user to `action` to read it at the source. A file whose
format nothing can read is a document with no content in the same way. An earlier version of
this model kept the text of every document in the index behind a `can_display_content` flag on
the content; that stated permission without enforcing it, since Dug's endpoints return the
indexed `_source` as is, and was dropped for the shape above.

`document_type` and `resource_type` are free strings; `DOCUMENT_KINDS` and `RESOURCE_KINDS`
list the recommended values. The one value a resource may not have is `resource_type="document"`:
a single file is a `DugDocument`.

#### Reference producer conventions

The model leaves several things to the producer. These are the conventions of the reference
producer,
[heal-non-data-dictionaries](https://github.com/heal-data-stewards/heal-non-data-dictionaries),
recorded so that a second producer, or a UI, does not have to reinvent or guess them. They are
not schema: nothing here is validated.

- **IDs.** A resource is `<study>/resources/<url-slug>` (the URL's host and path, lower-cased,
  non-alphanumerics collapsed to `-`); a document is `<study>/assets/<path under assets/>`; a
  content element is `<document>/<heading-slug>`, with `_2`, `_3` on repeated headings and
  `section-N` (N = 1-based position) when a heading has nothing sluggable in it.
- **`action`.** A resource links to its landing page. A document links to an explicit curated
  URL, else `https://doi.org/<doi>` when it has its own DOI, else the deposit URL it was
  downloaded from. Each content element copies its document's `action`.
- **Licence.** A document takes its own curated licence, else its resource's, else a
  study-level default; its text becomes content only when
  `can_include_content(document.license)` is true, else the document is emitted with no
  content.
- **`metadata` keys.** On a resource: `files = {"count": N, "bytes": B, "by_extension":
  {".nev": 13, ...}}`, an inventory of every file in the deposit including those that became no
  document (`.nii.gz` keeps its double extension; files without one are `"(none)"`). On a
  document: `page_count` for paginated formats; `embedded` (`title`, `author`, `creator`,
  `created`, `modified`, as stored in the file, for provenance only, since they are usually an
  OS account name or blank); `text_extraction` when a document has no content: `"none"` (no
  text layer), `"no_handler"` (a curated file no parser handles) or `"not_licensed"` (the
  licence does not allow the text to be incorporated). On a study: `appl_id` (NIH
  application id), `notes` (curator's notes), and anything else from the study's curated
  metadata.
- **Which files become documents.** Files a parser can read (Word, PDF, Markdown, plain text;
  spreadsheets and CSV when asked for). A curated file no parser handles becomes a document
  with no content. Everything else -- recordings, scans, images, primary data -- is counted in
  its resource's `files` inventory and nothing more.
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
| `DugStudy` | `"study"` | A research study; a dataset it draws on is a `DugResource` |
| `DugSection` | `"section"` | A section or instrument within a study |
| `DugResource` | `"resource"` | Something external with a URL and a description, usually the repository deposit (dataset) a study's files came from |
| `DugDocument` | `"document"` | A single file (README, protocol, report, poster, ...), with the same citation fields as a `DugResource`; holds no text itself |
| `DugContent` | `"content"` | A headed piece of a `DugDocument`'s text, held in `content`; the only element with text, present only under a licence that allows it |

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
