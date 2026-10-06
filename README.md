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
  (`description`). This is the only element that carries text, and therefore the only one
  with `can_display_content`.

```python
from dug_data_model.v2 import DugContent, DugDocument, DugResource, DugStudy, can_display

dataset = DugResource(
    id="HDP1/resources/zenodo-org-records-1",
    name="Pain behaviour in mice: data and methods",
    description="Behavioural data and analysis notes.",
    action="https://zenodo.org/records/1",   # landing page
    resource_type="dataset",                 # see RESOURCE_KINDS
    repository="zenodo",
    doi="10.5281/zenodo.1",
    license="CC-BY-4.0",
    parents=["HDP1"], parent_type="study",
    document_list=["HDP1/assets/README.docx"],
)

readme = DugDocument(
    id="HDP1/assets/README.docx",
    name="README.docx",                      # display title
    description="",
    action="https://zenodo.org/records/1",
    repository="zenodo",                     # a DugCitable field, like license
    license="CC-BY-4.0",                     # the deposit's licence unless the file states its own
    file_name="README.docx",
    mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    document_type="readme",                  # see DOCUMENT_KINDS
    parents=[dataset.id], parent_type="resource",
    content_list=["HDP1/assets/README.docx/general-methods"],
)

section = DugContent(
    id="HDP1/assets/README.docx/general-methods",
    name="General Methods",                  # the heading
    description="This repository contains ...",  # the text under it
    action=readme.action,                    # where to send a user who may not see the text
    position=0, level=1,
    can_display_content=can_display(readme.license),  # see DISPLAYABLE_LICENSES
    parents=[readme.id], parent_type="document",
)

study = DugStudy(
    id="HDP1", name="A study", description="...",
    resource_list=[dataset.id], document_list=[readme.id],
)
```

An element has a single `parent_type`, so a document's parent is either its resource or,
when it did not come from a known resource, its study. `DugStudy.document_list` lists every
document in the study either way. `validate_references()` checks that all of these IDs
resolve within a collection.

Going the other way, from a piece of content up to its study, follows `parents` through the
document and then the resource: three hops, or two when the document hangs off the study
directly. That is deliberate. A content element records only its document, and a document
only where it came from; the study lists its documents and resources directly, so a consumer
that starts from the study never has to climb. `build_parent_map()` and `get_children()` in
`dug_data_model.v2` walk the chain in either direction.

Text and the right to show it live in the same place. A document has nothing to display, so it
has no display flag; each `DugContent` says for itself whether its text may be shown, and its
`get_response_dict()` blanks `description` unless `can_display_content` is True. The text is
still indexed, so a search can find a document whose text may not be shown, and the UI can send
the user to `action` instead. Note that Dug's v2 endpoints (`/variables`, `/studies`, ...)
return each hit's Elasticsearch `_source` as indexed by `get_searchable_dict()` and do not call
`get_response_dict()`, so an endpoint that serves content has to apply the flag itself, or
leave it to the UI: the flag is a statement of permission, not an enforcement. A producer sets
the flag from the document's licence when it emits the content; there is no second copy to keep
in step. A file whose format nothing can read is still a document, just one with no content.
The licences that count are listed in `DISPLAYABLE_LICENSES`, and `can_display(license)`
applies them, so that every producer sets the flag the same way; NonCommercial and
NoDerivatives licences are left for a person to decide.

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
  study-level default; each content element's `can_display_content` is
  `can_display(document.license)`.
- **`metadata` keys.** On a resource: `files = {"count": N, "bytes": B, "by_extension":
  {".nev": 13, ...}}`, an inventory of every file in the deposit including those that became no
  document (`.nii.gz` keeps its double extension; files without one are `"(none)"`). On a
  document: `page_count` for paginated formats; `embedded` (`title`, `author`, `creator`,
  `created`, `modified`, as stored in the file, for provenance only, since they are usually an
  OS account name or blank); `text_extraction` when a document has no content: `"none"` (no
  text layer) or `"no_handler"` (a curated file no parser handles). On a study: `appl_id` (NIH
  application id), `notes` (curator's notes), and anything else from the study's curated
  metadata.
- **Which files become documents.** Files a parser can read (Word, PDF, Markdown, plain text;
  spreadsheets and CSV when asked for). A curated file no parser handles becomes a document
  with no content. Everything else -- recordings, scans, images, primary data -- is counted in
  its resource's `files` inventory and nothing more.
## Scaffold: Creating a New Model Version

Use the scaffold CLI to generate a new data model version inside the package:

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
| `DugContent` | `"content"` | A headed piece of a `DugDocument`'s text; the only element with text and a `can_display_content` flag |

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
