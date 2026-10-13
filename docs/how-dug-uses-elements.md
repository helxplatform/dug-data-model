# How Dug uses an element

What the [Dug](https://github.com/helxplatform/dug) engine (the search behind HEAL Semantic
Search) does with the elements this model describes, as read from its source in October 2026
(`helxplatform/dug` at `7f04f28`). Line numbers are from that commit. None of this is a
contract, but it is what a field has to survive to be useful, and it decided several of this
model's shapes: why content is its own element, why `studies` exists, and why nothing lists
its children.

## One element at a time

A parser yields elements; the crawler annotates each one and the indexer writes each one as
one Elasticsearch document.

- **Annotation** (`src/dug/core/crawler.py:109-158`). `annotate_element()` sends
  `element.ml_ready_desc` to the annotator (Monarch, SAPBERT, ...) as one text and turns the
  identifiers that come back into `DugConcept`s linked to the element; `set_search_terms()`
  then folds the concepts' names into the element's `search_terms`. Nothing else on the
  element is read. So the text that should find an element has to be in its
  `ml_ready_desc`, and it goes to the annotator in one piece: that is why a document's
  text is split into `DugContent` elements, each a bounded section with its own
  `ml_ready_desc` (heading and body), rather than held on the resource.
- **Indexing** (`src/dug/core/__init__.py:75-82`, `src/dug/core/index.py:105-130`). The crawl
  loop routes elements to indices by class: `DugVariable` to the variables index,
  `DugStudy` to the studies index, `DugSection` to the sections index; concepts and their
  knowledge-graph answers go to their own indices. **An element of any other class is not
  indexed at all**, so `DugResource` and `DugContent` reach an index only when Dug is taught
  about them. `index_element()` writes `get_searchable_dict()` as the document, keyed by the
  element's `id`. If the ID is already in the index, it does not replace the document: it
  merges `search_terms`, `optional_terms`, `parents`, `programs`, `tags` and `identifiers`
  (deduplicated) and leaves every other field as it was. A second producer can therefore add
  a parent or a program to an element, but cannot change its name or description.
- **Mappings are strict** (`src/dug/core/index_init.py`). Every index is created with
  `"dynamic": "strict"`, so a document with a field the mapping does not list is rejected.
  The variables mapping lists `id`, `name`, `element_type`, `description`, `action`,
  `search_terms`, `optional_terms`, `identifiers`, `parents`, `programs`, `is_cde`,
  `data_type`, `metadata` (a dynamic object, so anything goes under it) and `tags` (nested
  `category`/`value`). `parents` and `programs` are text with a `.keyword` sub-field;
  `element_type` is a keyword. Every field this model adds -- `resource_type`,
  `repository`, `authors`, `doi`, `license`, `file_name`, `mime_type`, `studies`, `content`,
  `position`, `level`, `page` -- needs a mapping before an element carrying it can be
  indexed, in an extended mapping or a new index. `metadata` is the one place a producer can
  put a new key without a Dug change, which is why the reference producer keeps a file
  inventory, a PubMed ID and related identifiers there.

## Searching

- **Filtering** (`src/dug/core/async_search.py:412-571`, `1220-1260`). Element searches match
  `query` against the text fields and can restrict to a concept (`identifiers`), to parents
  (a `terms` filter on `parents.keyword`) or to element IDs (`id.keyword`). A filter on
  `parents` reaches exactly one hop: the direct children of the given IDs. From a study,
  that is its resources; the files under them, and the content under those, are two and
  three queries away. `studies` on every resource and content element is the one-query
  answer, once it has a keyword mapping.
- **Grouping** (`_make_result()`, `src/dug/core/async_search.py:573-634`). Hits are grouped
  into "collections" for the UI by `collection_id` from the old schema or, for this model,
  by **`parents[0]`**, and bucketed by `_source["data_type"]`. Each hit contributes its
  `id`, `name`, `description`, `action` and `metadata`. So a content hit is grouped under
  its file, a file under its deposit, a deposit under its study; a UI that wants resources
  and content grouped by study needs Dug to group by `studies` where present. The order of
  `parents` matters: an element with several parents is shown under the first.
- **What comes back.** The endpoints return each hit's `_source` as indexed, with
  `search_terms` and `optional_terms` stripped by the API layer and nothing else. So a
  field in `get_searchable_dict()` is a field the user can see, which is why content exists
  only under a licence that allows it instead of behind a display flag, and why a document's
  text is not stored on the resource whose every hit would return it.
- `src/dug/server.py:654` accepts only the studies, variables and sections index names for
  the generic query endpoint; a resources index would need adding there too.

## What this means for a producer

- Put search text in `description` (or in a type's `ml_ready_desc`), one bounded piece per
  element.
- Put anything Dug has no mapping for under `metadata`.
- Write `parents` with the element that should group the hit first.
- Write `studies` on every element below a study, so that one filter can find them once
  Dug maps it.
- Expect re-runs to merge list fields and keep the first-written scalars.
