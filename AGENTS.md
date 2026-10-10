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
- **`tests/fixtures/heal_hdp00009.json` is a real producer output**, hand-edited to the
  current shape until the producer (heal-non-data-dictionaries) catches up. Keep it loading
  through `validate_references()` and round-tripping through `compact_dump()`.
- **Dug consumes these elements one at a time with strict index mappings.** Before adding a
  field for the index's sake, read `docs/how-dug-uses-elements.md`.
- `pytest` and `mypy src` are the checks; mypy has long-standing errors in `base.py` and
  the `type: Literal[...]` narrowing pattern, so compare counts against the parent branch
  rather than expecting zero.
