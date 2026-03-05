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
| `DugStudy` | `"study"` | A research study or dataset |
| `DugSection` | `"section"` | A section or instrument within a study |

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
