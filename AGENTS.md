# Working on dug-data-model

Notes for agents and people. The README is the reference; this is what is easy to miss.

## Commands

The `dev` extra installs pytest but not mypy or ruff, so run those through uv:

```bash
uv run pytest
uv run pytest tests/test_model.py::TestDugVariable::test_default_type
uv run --with mypy mypy src
uvx ruff check src tests
```

mypy is strict and has long-standing errors (25 on `main` when this was written): the
`type: Literal["x"] = X_TYPE` pattern in every subclass, `@computed_field` on a property, and
the untyped jsonpickle hooks in `base.py`. Compare the count against the parent branch rather
than expecting zero. Ruff is configured but not enforced, and has findings of its own.

## How the package fits together

- **`scaffold/` is the template for a model version.** `python -m dug_data_model.scaffold new v3`
  copies `base.py`, `concept.py`, `types.py`, `utils.py` and `validation.py` into
  `src/dug_data_model/v3/`, and takes `scaffold/__init__.py` from its first import line
  down (the docstring is replaced). So scaffold files are both working code and templates.
- **`v2/` is the shipped model.** `v2/concept.py`, `v2/utils.py` and `v2/validation.py` are
  still identical to the scaffold's, so a fix goes in both. `v2/base.py` differs on
  purpose (v2 has `tags`), and `v2/types.py` fills in the `Indexable` union that the
  scaffold's `types.py` only describes in a comment.
- **Adding an element type to a version** takes all of: a subclass with
  `type: Literal["..."]` (the discriminator), an entry in `Indexable` in `types.py` (or
  `DugElementParsedList` will reject it), a `model_rebuild()` call in `__init__.py` (the
  `DugConcept` forward reference in `DugElement.concepts` needs it), and an export.
- **`get_searchable_dict()` is the Elasticsearch document Dug indexes.** Dug's index
  mappings are strict, so a new key there needs a matching change in Dug.
- **Do not remove `__setattr__`, `__getattr__` or `__getstate__` from `base.py`.** Dug
  round-trips elements through jsonpickle, which rebuilds them with `__new__` and skips
  Pydantic's `__init__`; the comments in those methods say what each case handles.

## Schemas

`src/dug_data_model/schemas/v2_schema.{json,md}` are committed, and the hatch build hook
(`scaffold/build_hook.py`) regenerates them on every build for each `v<N>/` directory that
exports `DugElementParsedList`. Nothing checks that the committed copies are current, so
regenerate them after any model change:

```bash
uv run python -m dug_data_model.scaffold schema v2 -o src/dug_data_model/schemas/v2_schema.json
uv run python -m dug_data_model.scaffold schema v2 --format markdown -o src/dug_data_model/schemas/v2_schema.md
```

## Where notes go

Keep agent notes in this file, not in `AGENTS.md` files under `src/dug_data_model/`:
hatch packages everything in that directory, so they would ship in the wheel.
