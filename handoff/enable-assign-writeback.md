# Handoff: enable edits so the Assign action actually works

Follow-on to `handoff/ontology-sync-stuck.md` (that problem is resolved — read it for full background on the V2
indexing failure and the v1/Phonograph migration, don't redo that work).

## Current state (independently verified via SDK, not just Ontology Manager UI)

- `Order` object type is healthy: `client.ontologies.Ontology.ObjectType.list(...)` shows it with primary key
  `orderId`; `client.ontologies.OntologyObject.list(ontology, "Order", page_size=1000)` returns 203 objects
  without error.
- Action types `create-order`, `edit-order`, `delete-order`, `assign` all still exist.
- Edits are **disabled** on `Order` (this was intentionally turned off while debugging the V2 indexing failure).
  Confirmed via a live test: calling `client.ontologies.Action.apply(ontology, 'assign', parameters={'order':
  'B-ORD-20000', 'assignee': 'test-user'})` returns a validation result where the `order` parameter is `INVALID`
  with constraint type `objectQueryResult` — i.e. the action can't resolve a target object to edit because edits
  aren't enabled.

## The ask

In Ontology Manager, for the `Order` object type:

1. Re-enable **edits** (there's a toggle/setting for this, seen earlier as "Edits enabled: Yes/No" in the object
   type's General Information panel).
2. Since `Order` is now on Object Storage v1/Phonograph (not V2), enabling edits on this backend typically
   requires configuring a **writeback/edits dataset** — a place Foundry stores action-driven property changes
   separately from the source `all_orders` dataset. Find and complete whatever step Ontology Manager surfaces for
   this (may be automatic — Foundry can auto-generate this dataset — or may require picking/creating one
   explicitly; follow whatever the UI actually presents).
3. Save.

## How to verify it worked (do this yourself, don't just trust the UI)

From the repo's local Python env (`source .venv/bin/activate` in `/Users/fmlin/Documents/Palantir-labs/foundry-poc`,
`.env` already has credentials), run:

```python
from dotenv import load_dotenv
import os
load_dotenv()
from foundry_sdk import FoundryClient, UserTokenAuth
hostname = os.environ['FOUNDRY_URL'].replace('https://', '').replace('http://', '')
client = FoundryClient(auth=UserTokenAuth(token=os.environ['FOUNDRY_TOKEN']), hostname=hostname)
ontology = 'ontology-177da4f8-ccba-41fe-856a-59440eb5a8e4'

result = client.ontologies.Action.apply(
    ontology, 'assign',
    parameters={'order': 'B-ORD-20000', 'assignee': 'test-user'},
)
print(result)
```

If edits are properly enabled, the `order` parameter should validate (or the action should actually apply,
depending on whether this call defaults to a dry-run/validate mode). If it still comes back `INVALID` with the
same `objectQueryResult` constraint, edits aren't fully wired up yet — report the exact response.

## How to report back

Append findings to `scripts/foundry_resources.md` under a new `## Enabling Assign writeback` heading: what was
clicked, what Foundry auto-generated (if anything, note its RID), and the exact SDK verification output above.
Keep it factual/terse, not a narrative.
