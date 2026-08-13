# Foundry resource RIDs

Created 2026-08-13 via `scripts/ingest_datasets.py` and console steps. Not sensitive (RIDs alone don't grant
access without the token), kept here so scripts/commands can reference them without re-querying every time.

- Project `foundry-poc`: `ri.compass.main.folder.736be223-228f-402a-8759-ad7063d17103`
  (path `/fmlin0429712024-16d385/foundry-poc`)
- Dataset `orders_system_a`: `ri.foundry.main.dataset.b2c83708-daa1-4cec-8d55-0de0433b8715`
- Dataset `orders_system_b`: `ri.foundry.main.dataset.626d4f8e-9930-4e03-9816-635a52c19e39`
- Dataset `consolidated_customers`: `ri.foundry.main.dataset.599a744c-248e-47b7-8256-b3e86362be64`
- Dataset `all_orders` (transform output): `ri.foundry.main.dataset.ce413301-99b5-43b5-ad2a-b9c3b3b605ba`
- Python Transforms Code Repository (git remote is cluster-internal only, see below):
  `ri.stemma.main.repository.ffa80828-82c2-4410-b499-e1382b7739f2`

## Notes / gotchas discovered

- Raw CSV file uploads via `Dataset.File.upload` are untyped; Python Transforms' `Input.dataframe()` needs a
  schema registered via `Dataset.put_schema(..., dataframe_reader="CSV")` before Spark can parse them as a table.
- `put_schema`'s `DatasetSchema` model has no accepted field for declaring "has header row" (a `custom_metadata`
  key was tried and rejected server-side as `UnknownField`). Workaround: strip the header line client-side before
  upload, since column names are already supplied explicitly via the schema API.
- Schema is tied to a transaction, not the dataset as a whole — re-uploading data (a new SNAPSHOT transaction)
  drops the previously applied schema. `put_schema` must be re-run after every re-upload.
- Builds can be triggered via `client.orchestration.Build.create(target=ManualTarget(target_rids=[...]))` and
  polled via `Build.get`. Failure detail (stack traces/logs) is **not** exposed through the public SDK/API as far
  as explored — `Job.get(..., preview=True)` and `Transaction.get` only return status (e.g. `FAILED`/`ABORTED`),
  not a reason. Diagnosing failures required reasoning from symptoms rather than reading logs; if a future
  failure can't be diagnosed this way, the Foundry browser UI (build's log panel) is the fallback.

## GUI-only step: Ontology object type / action definition

Confirmed via two independent checks that defining a new Object Type or Action Type has no CLI/SDK/code path on
this account:
1. `foundry_sdk.v2.ontologies` clients (`ObjectType`, `ActionType`) expose only read methods (`get`, `list`,
   `get_full_metadata`, `get_edits_history`, etc.) — no `create`.
2. The project's "+ New" → Developer Tools wizard, filtered to the "Ontology" category, offers only
   **Workflow Lineage** (an ontology/model/function relationship explorer) — no "Ontology as Code" or object-type
   authoring template exists in this environment.

So: the `Order` object type, its properties, standard actions, and the custom `Assign` action must all be defined
via the **Ontology Manager** application (GUI). This is the PoC's one unavoidable GUI step per the brief's own
guardrail ("say so explicitly rather than silently falling back to GUI").
