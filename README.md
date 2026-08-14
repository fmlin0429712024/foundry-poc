# Foundry Foundations PoC

A hands-on lab covering Palantir Foundry's core architecture — **datasets → transforms → Ontology → operational
application** — built CLI/SDK-first, GUI only where the platform genuinely requires it. Full requirements in
[foundry-poc-brief.md](foundry-poc-brief.md).

## Core concept: what the Ontology actually is

The standard framing is: **objects are nodes, links are edges, actions are operations that mutate the graph.**
True, but incomplete on its own — the part that actually explains how Foundry behaves is this:

**Foundry's Ontology is a semantic layer declared over tabular data, not a native graph database.** Unlike Neo4j
(where a relationship is physically stored as an edge), a Foundry Link is a declared **foreign-key join**: when
building the `Order ↔ Customer` link in this lab, the relationship type offered was literally called *"Object
type foreign keys"* — "this column on Order equals that column on Customer." Traversal (`order.customer.get()`)
resolves that join at query time; nothing is stored as a graph edge under the hood. Object types backed by a
dataset (as both of ours are) sit on top of ordinary columnar/Spark-backed storage.

This explains the one piece of real *value* the Ontology adds over just querying the merged dataset directly.
A Foundry transform is a **batch, deterministic recomputation** — its output dataset gets fully rebuilt from the
same source data every run. If you hand-edited a row in that output (e.g. reassigning an order), the next
pipeline run would silently overwrite it, because the transform has no memory of your edit. An Ontology **Action**
writes to a separate, durable edit layer that survives re-runs of the underlying transform — that's the actual
job it does: it turns a recomputed, overwrite-prone table into something with a safe, persistent, governed way to
make one-off changes. Everything else (permissions on who can submit an action, audit trail) rides on top of that
same mechanism.

## Architecture

| Layer | Job |
|---|---|
| **Data** (raw datasets) | Land the two legacy systems' orders + the customer crosswalk, unmodified |
| **Transform** (PySpark) | Deterministically clean, standardize, join, and union into one dataset |
| **Ontology** (`Order`, `Customer`, Link, Actions) | Declare the semantic model over that dataset, and add a durable, governed edit layer on top of it |
| **Operational app** (Workshop) | The human-facing door to that edit layer — list orders, trigger an Action |

## The use case

Two office supply companies merged; their legacy order systems don't agree on format, and reassigning orders to
a new handler post-merger has no safe, persistent place to happen. This lab builds: a unified `all_orders`
dataset from both legacy systems plus a consolidated customer list, an `Order` object type modeling it in the
Ontology, and (eventually) an operational view to reassign orders. All source data is **synthetic**, generated
with intentional messiness (null IDs, mixed date formats, mismatched keys, inconsistent casing) so the transform
step is real practice, not a no-op.

## The lab, step by step

### Step 1 — Ingest (`scripts/generate_synthetic_data.py`, `scripts/ingest_datasets.py`)

Fully CLI/SDK: the three CSVs are generated locally, then created as Foundry datasets and uploaded via
`client.datasets.Dataset.create()` / `.File.upload()` — no GUI upload involved.

**Lesson**: a raw upload is untyped bytes until a schema is explicitly applied
(`Dataset.put_schema(..., dataframe_reader="CSV")`), and that schema is bound to a specific dataset *transaction*
— re-uploading data (a new transaction) drops it, so it must be reapplied after every re-upload. There's also no
API field for "this CSV has a header row"; the fix is to strip the header line client-side before upload, since
column names are already supplied explicitly via the schema call.

### Step 2 — Transform (`transform/all_orders.py`)

A Python Transforms (PySpark) job in a Foundry Code Repository, per the brief — not the Pipeline Builder GUI. It
casts due dates to timestamp (handling three different input formats), filters null/empty `order_id`, drops the
irrelevant `order_placement_date` column, normalizes column names to snake_case, joins each legacy dataset to
`consolidated_customers`, and unions both into `all_orders`.

**This repo (pushed to GitHub) is the source of truth for that file.** Foundry's Code Repository is a *separate*
git server reachable only from inside Foundry's own network, with no public URL and no API for writing files into
it — so `scripts/sync_transform_to_foundry.sh` generates a one-time paste-and-run command to promote a change
into Foundry's copy. Not fully automated, but a single copy-paste rather than editing code in the browser.

Builds are triggered and polled from the terminal (`client.orchestration.Build.create()` / `.get()`).

**Lesson**: the build API returns terminal status (`SUCCEEDED`/`FAILED`) but no logs — verify results by reading
the output data back directly (`Dataset.read_table(..., format="ARROW")`), not by trusting the status alone.

**Result**: `all_orders` — 206 rows (106 from system A, 100 from system B), no empty `order_id`s, `due_date` cast
to timestamp, 15 rows with intentionally-unmatched customer keys.

### Step 3 — Ontology (Ontology Manager)

Built: `Order` (backed by `all_orders`, primary key `order_id`) and `Customer` (backed by
`consolidated_customers`, primary key `consolidated_customer_id`); a many-to-one Link between them on
`consolidated_customer_id`; standard `Create`/`Modify`/`Delete` actions on `Order`; and a custom `Assign` action
(sets `assignee` from input, sets `status` to a fixed `"assigned"`) — the durable-edit mechanism described above.

**Defining this structure is GUI-only on this account tier** — confirmed two ways, not assumed: the
`foundry_sdk.v2.ontologies` clients (`ObjectType`, `ActionType`) expose only read methods (no `create`), and the
project's Developer Tools wizard has no Ontology-authoring template (only a read-only relationship explorer).
*Using* an already-defined Ontology — querying objects, invoking an action like `Assign` — is CLI/SDK-capable
(`client.ontologies.OntologyObject`, `client.ontologies.Action.apply`); the GUI requirement is specifically for
authoring the schema, not operating it afterward.

Re-verified the saved structure independently from the terminal:

```python
client.ontologies.Ontology.ObjectType.list(ontology)  # → Order (pk: orderId), Customer (pk: consolidatedCustomerId)
client.ontologies.Ontology.ActionType.list(ontology)   # → create-order, edit-order, delete-order, assign
```

### Step 4 — Operational app (Workshop)

Not yet built. Its job is narrow given the architecture above: it's just the human-facing front door to the
`Assign` action — a table of orders with a button that calls the same edit mechanism already fully defined in
step 3. None of the durability/governance logic lives here.

## Current status

- Done: ingestion, transform (`all_orders` verified), Ontology structure (`Order`, `Customer`, Link, actions
  — verified via SDK).
- Not done: Ontology object materialization for `Order` (dataset rows → queryable object instances) has not yet
  been confirmed complete; the operational app; the end-to-end Assign test.
- Known limitation, cause not yet established: on this account tier, the public API surfaces no sync-job-status
  or log endpoint for diagnosing why object materialization is slow — Ontology Manager's own Health panel is the
  only place with more detail, if any exists.

## GUI-only steps (per the brief's own guardrail)

- Creating the first Foundry Project and Code Repository resource (one-time bootstrapping; no SDK/API path
  found).
- All Ontology structure definition (Step 3 above).
- Getting code into the Foundry Code Repository's actual git history (Step 2 above).

## Repo layout

- `data/raw/` — generated synthetic CSVs
- `scripts/` — everything run from the local terminal: data generation, ingestion, schema application, build
  triggering, the GitHub→Foundry sync helper, and `foundry_resources.md` (resource RIDs + a technical gotchas
  log, more granular than this README)
- `transform/all_orders.py` — the PySpark transform, mirrored into Foundry's Code Repository
- `CLAUDE.md` — orientation notes for an AI coding agent picking this repo up cold
