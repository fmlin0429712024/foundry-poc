# Foundry Foundations PoC — Use Case & Handoff Brief

## Purpose
This is a **learning exercise**, not a production build. The goal is to get hands-on with Palantir Foundry's core architecture — datasets → transforms → Ontology (objects, links, actions) → operational application — primarily through **CLI / SDK / code-based workflows**, using the GUI only where the platform genuinely requires it. This will later inform prep for the Foundry Foundations certification, but the exam is a secondary checkpoint, not the driver.

## Environment
- Foundry **Developer account** is available.
- CLI / API access should be enabled and used as the default interface.
- The GUI (Ontology Manager, Workshop, Pipeline Builder) is a fallback only — flag any step that cannot be done via CLI/SDK/code so the user can do it manually.

## Use Case
Two office supply companies have merged. Order tracking across the two legacy systems is inconsistent, causing dropped orders and unhappy customers. The goal is to:
1. Bring in raw order data from both legacy systems plus a consolidated customer list.
2. Clean, standardize, and merge this data into a single unified dataset.
3. Model it in the Ontology as an `Order` object type.
4. Build a simple operational view where someone can see all orders and reassign them to a handler.

This mirrors a realistic "operational inbox" pattern common in Foundry deployments (merger integration, fulfillment ops, exception handling).

## Data to Prepare
Since this is a learning exercise, all data should be **synthetic**, generated to intentionally include realistic messiness so the transform step is meaningful practice. Prepare three tabular files (CSV or Excel):

1. **orders_system_a.csv** (e.g. "Bureau" legacy system)
   - Columns: order_id, customer_id, item_name, order_due_date, status, assignee
   - Include: some null order_ids, a date column (not timestamp), inconsistent column casing

2. **orders_system_b.csv** (e.g. "Office Goods" legacy system)
   - Similar columns but with different naming conventions (e.g. `dueDateTime` instead of `order_due_date`), an extra irrelevant column (e.g. `order_placement_date`) that should get dropped, and some null order_ids

3. **consolidated_customers.csv**
   - Columns: consolidated_customer_id, customer_name, and a separate customer_id key per legacy system (e.g. `system_a_customer_id`, `system_b_customer_id`) to support the join

Add a handful of edge cases on purpose: duplicate customer IDs, mismatched keys with no match, empty strings vs. true nulls, mixed date formats. ~50–200 rows per file is plenty — this is about learning the mechanics, not scale.

If generating this data is more efficient to do directly (e.g. with a script) rather than handing it off, that's fine — output the files into the workspace folder either way.

## Build Steps (in priority order, CLI/SDK-first)

1. **Ingest** the three files into Foundry as datasets (CLI/API upload if supported by this account tier; otherwise note as a manual step).
2. **Transform** using a Foundry Code Repository (Python/PySpark transform), replicating:
   - Cast due-date columns to timestamp
   - Filter out rows with null/empty order_id
   - Drop unneeded columns
   - Rename columns for consistency
   - Normalize column names (snake_case)
   - Join each legacy dataset to the consolidated customer dataset
   - Union both cleaned+joined datasets into one output dataset (e.g. `all_orders`)
3. **Ontology**: define an `Order` object type backed by `all_orders`, with `order_id` as primary key. Add standard actions (create/modify/delete) plus a custom `Assign` action that sets `assignee` and auto-updates `status` to "assigned". Use Ontology-as-Code / SDK if this environment supports it; otherwise flag this as a manual Ontology Manager step and describe exactly what needs to be clicked.
4. **Operational view**: a minimal way to list orders (table with status/assignee/due date) and trigger the Assign action on a selected order — via Workshop if no code-based alternative exists, and clearly flagged as a GUI step if so.
5. **Test**: verify assigning an order actually updates the object and is reflected back.

## Guardrails
- Don't need external references beyond this brief — the use case and requirements above are sufficient to start.
- Prioritize understanding the Ontology's structure (objects as nodes, links as edges, actions as graph-mutating operations) over UI polish.
- Where CLI/SDK coverage is genuinely incomplete for a step, say so explicitly rather than silently falling back to GUI — the user wants to know where the platform's current limits are.

## Success Criteria
- An `all_orders` dataset built via code-based transforms (not Pipeline Builder GUI, unless unavoidable)
- A working `Order` object type in the Ontology
- A working `Assign` action, invokable end-to-end
- A short list of "had to use GUI here because ___" notes, if any
