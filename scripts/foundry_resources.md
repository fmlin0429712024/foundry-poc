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

## Ontology Manager gotcha: "Incompatible parameter for 'Create or modify object' rule"

Hit this save error when adding a second Modify-type action (`Assign`) to the `Order` object type in the same
Ontology Manager session as the object types were being created. Root cause was never fully pinned down (the
referenced Action Type RID in the error resolved to "not found" both times, suggesting a validation-time
synthetic reference rather than a real corrupted resource) — some in-session state from the wizard interfered
when creating the second Modify action for the same object type. **Fix that worked**: delete the broken action
type from "Unsaved changes" (safe — new/unsaved resources delete immediately without affecting other pending
changes) and recreate it from scratch via the object type's own "Action types" panel → "+ New" (not while another
action's detail page is open). Recreating it this way, with `Modify object(s)` selected explicitly at step 1,
saved cleanly on the first attempt.

## Ontology Manager gotcha: object type sync delay

Immediately after saving a dataset-backed object type, querying it can temporarily return `ConflictError` /
`OntologySyncingObjectTypes`. A short delay is normal, but persistent errors are not. On this stack the V2 sync
eventually reported `Index failed`; the working fallback is documented below.

## Order object sync investigation

- **Root cause:** Object Storage V2 indexing is broken on this Developer stack. `Order`, `Customer`, and a
  disposable `OrderSimple` type with no edits, actions, or links all failed initial V2 syncs. This rules out the
  datasets, the customer link, and action/edit configuration as causes.
- **Fix:** Disabled edits on `Order`, deleted the disposable test type, switched `Order` to Object Storage v1
  (Phonograph), and manually updated its Phonograph registration. The sync succeeded. The unnecessary
  `Order`–`Customer` link and failed `Customer` object type were deleted.
- **Current status:** Ontology Manager reports `Order` as `Indexed` and Health issues reports `No health issues
  found`. SDK object queries succeed and return 203 Order objects. `all_orders` has 206 rows but only 203 unique
  `order_id` values, so the object count is correct for the configured primary key.

## Enabling Assign writeback

- In `Order` → `Datasources` → `Edits`, clicked `Generate`; Foundry created `all_orders_edited` at
  `/fmlin0429712024-16d385/foundry-poc` with RID
  `ri.foundry.main.dataset.3c768c10-9ab3-4b5e-90a3-393ed7c3a828`.
- Saved with `Only allow edits via actions` enabled, then manually updated the Phonograph registration so it
  picked up the writeback dataset. Registration is `Registered`; index status is `Indexed`.
- Exact SDK verification output:

  ```text
  operation_id='ri.actions.main.action.4424142c-8a6b-45d0-82a8-ec3567b9d976' validation=ValidateActionResponseV2(result='VALID', submission_criteria=[], parameters={}) edits=None
  ```

- A fresh SDK object read confirmed the write: `{'orderId': 'B-ORD-20000', 'assignee': 'test-user', 'status':
  'assigned'}`.

**Independently re-verified** (separate session, separate order): applying `assign` on `A-ORD-10000` (before:
`assignee='dpatel'`, `status='Cancelled'`) with `assignee='claude-verification-test'` showed no change on an
immediate read, but the write was confirmed correct after an ~8s wait
(`assignee='claude-verification-test'`, `status='assigned'`). **Lesson**: the v1/Phonograph-backed edit layer has
a short (single-digit-seconds) propagation delay between `Action.apply` and the change being visible to
`OntologyObject.get`/`.list` — expected eventual consistency, not a failure; don't read-back immediately after
applying an action in future tests/automation.
