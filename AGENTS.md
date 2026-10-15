# Working on dug-data-model

Notes for agents and people. The README is the reference; this is what is easy to miss.

- **Regenerate the committed schemas after any model change**, or `tests/test_schemas.py`
  fails. The commands are in the README under "Schema Generation".
- **`v2/utils.py` and `v2/validation.py` are copies of the scaffold's.** A fix goes in both
  (`src/dug_data_model/v2/` and `src/dug_data_model/scaffold/`); `tests/test_scaffold_copies.py`
  fails if one is forgotten. `base.py` is also copied but may differ (v2 has `tags`).
- **Nothing lists its children.** A child names its parent in `parents`; `studies` on
  resources and content names the study from any depth. Do not add a `*_list` of children;
  the README's "Shapes that were tried and dropped" says why.
- **`tests/fixtures/heal_hdp00009.json` is a real producer output**, a copy of
  heal-non-data-dictionaries' `examples/HDP00009/HDP00009.json` (`tests/test_fixtures.py`
  says which branch and when). Keep it loading through `validate_references()` and
  round-tripping through `compact_dump()`; a model change that breaks it needs the producer
  changed too, or the fixture refreshed from it.
- **What each `RESOURCE_KINDS` value means is in `docs/resource-kinds.md`**, not the code.
  Adding, removing or reordering a kind means changing both; `tests/test_model.py` fails
  unless the doc's `###` headings are exactly the tuple, in order.
- **Dug consumes these elements one at a time with strict index mappings.** Before adding a
  field for the index's sake, read `docs/how-dug-uses-elements.md`.
- `pytest` and `mypy src` are the checks; mypy has long-standing errors in `base.py` and
  the `type: Literal[...]` narrowing pattern, so compare counts against the parent branch
  rather than expecting zero.
