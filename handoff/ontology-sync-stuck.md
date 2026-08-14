# Handoff: Foundry Ontology object sync stuck

For an agent with browser control (e.g. Codex with browser access) picking this up cold. You have no prior
context on this repo or this Foundry account — everything you need is below or linked.

## What this repo is

A Palantir Foundry learning PoC. Repo root: `/Users/fmlin/Documents/Palantir-labs/foundry-poc`. Read
[`README.md`](../README.md) for the full architecture/concept picture and [`CLAUDE.md`](../CLAUDE.md) for repo
conventions. This file only covers one specific, currently-blocking problem.

## Foundry account / where to log in

- Stack: `https://fmlin0429712024.usw-16.palantirfoundry.com`
- You'll need to log in with the account owner's credentials in the browser yourself (ask the user) — this repo's
  `.env` file only holds an API token for SDK calls, not a browser login.
- Project: `foundry-poc`, path `/fmlin0429712024-16d385/foundry-poc`
- Ontology: display name **"fmlin0429712024 Ontology"**, api_name `ontology-177da4f8-ccba-41fe-856a-59440eb5a8e4`,
  rid `ri.ontology.main.ontology.f59e7a44-6bd0-4dcf-b8a6-a67cbcc4ddb8`

## The problem

An `Order` object type was created in Ontology Manager (backed by the `all_orders` dataset, primary key
`order_id`), and the Ontology save succeeded — independently confirmed via SDK
(`client.ontologies.Ontology.ObjectType.list(...)` returns `Order` with the correct primary key and properties).

However, querying actual object instances fails and has kept failing for 20+ minutes:

```python
client.ontologies.OntologyObject.list(ontology, 'Order', page_size=3)
# → ConflictError: errorName "OntologySyncingObjectTypes", parameters: {"objectTypes": ["Order"]}
```

This means Foundry has not finished materializing the dataset's 206 rows into queryable Ontology object
instances. **This duration is abnormal** for a 206-row synthetic dataset — should be well under a minute in a
healthy state, not 20+.

## What's already confirmed (don't re-check these)

- `all_orders` dataset itself is healthy: 206 rows, correct schema, `due_date` cast to timestamp — verified via
  `client.datasets.Dataset.read_table(..., format="ARROW")`.
- `Order` and `Customer` object type definitions, the Link between them, and all four Action types
  (`create-order`, `edit-order`, `delete-order`, `assign`) all saved successfully and are independently visible
  via `client.ontologies.Ontology.ObjectType.list()` / `.ActionType.list()`.
- The public `foundry-platform-sdk` (v2 API) has **no endpoint found** for checking sync/materialization job
  status or logs directly — only the object-query call above, which just returns the same conflict error
  repeatedly with no more detail.

## What hasn't been checked yet — this is the actual ask

Use the browser to find out **why** the sync is stuck / how long it's actually expected to take / whether it
failed silently. Specifically:

1. Log into the Foundry stack above, open **Ontology Manager**, navigate to the `Order` object type.
2. Check its **"Observability"** tab (left nav within the object type page) — likely shows materialization/sync
   job status and history.
3. Back on the Ontology Manager **Discover** page, check **"Health issues"** in the left nav — may surface errors
   tied to `Order` or the underlying dataset link.
4. Check whether `Customer` (the other object type, backed by `consolidated_customers`) has the same stuck-sync
   symptom, or only `Order` — this narrows down whether it's an `Order`-specific issue or account/tier-wide.
5. Look for any explicit "sync now" / "reindex" / "rebuild" action in the object type's UI (e.g. under an
   "Actions" dropdown on its overview page) and try it if one exists.
6. If there's a genuine error surfaced anywhere in the UI, capture the exact text.

## How to report back

Append findings to [`../scripts/foundry_resources.md`](../scripts/foundry_resources.md) under a new
`## Order object sync investigation` heading — root cause if found, whether retriggering helped, and current
status. Keep it factual/terse (root cause + fix), not a narrative of what was clicked in what order.
