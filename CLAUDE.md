# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

Ingestion and the `all_orders` transform are built and verified end-to-end. The simplified Ontology contains one
healthy `Order` object type backed by `all_orders`; it uses Object Storage v1/Phonograph because V2 initial sync
fails on this Developer stack. SDK queries return 203 objects (206 rows minus three duplicate primary keys).
Actions are defined but edits are disabled; the writeback/edit dataset, operational view, and end-to-end Assign
test remain. See `scripts/foundry_resources.md` for resource RIDs and the full indexing workaround.

This repo is pushed to GitHub at `fmlin0429712024/foundry-poc` (public). Foundry's own Code Repository
(a *separate* git repo, hosted inside Foundry — see "Two repositories" below) is not derived from it automatically.

## Environment setup

- Python venv at `.venv/`, `pip install -r requirements.txt` (`foundry-platform-sdk`, `python-dotenv`).
- Credentials in `.env` (gitignored; template at `.env.example`): `FOUNDRY_URL`, `FOUNDRY_TOKEN`. Never read or
  print `FOUNDRY_TOKEN`'s value into chat/logs — verify it's set with `grep`, not `cat`.
- Standard client construction used throughout `scripts/`:
  ```python
  from foundry_sdk import FoundryClient, UserTokenAuth
  client = FoundryClient(auth=UserTokenAuth(token=token), hostname=hostname)
  ```
- Foundry stack: `fmlin0429712024.usw-16.palantirfoundry.com`, a personal Developer account (no org admin).

## Two repositories — this is not a mistake, it's a platform constraint

This project spans **two independent git repositories that do not sync automatically**:

1. **This repo** (`~/Documents/Palantir-labs/foundry-poc`, pushed to GitHub) — the source of truth. All authoring
   happens here: synthetic data generator, SDK scripts (ingestion, schema, build triggering), and a mirrored copy
   of the transform code at `transform/all_orders.py`.
2. **Foundry's Code Repository** (RID in `scripts/foundry_resources.md`) — a git repo hosted *inside* Foundry's
   own cluster. This is what Foundry's build system actually executes. Its git remote resolves to a
   `*.svc.cluster.local` address — reachable only from inside a Foundry-hosted VS Code workspace, never from this
   machine or from GitHub Actions. There is no public git URL, and the public Foundry API (`foundry-platform-sdk`)
   has no endpoint to write files into a Code Repository. Confirmed no way to bind this repo to an external
   provider like GitHub either (checked Settings → Repository/Webhooks in the Foundry UI — no such option exists
   on this account tier).

**Consequence**: after editing `transform/all_orders.py` here, run `scripts/sync_transform_to_foundry.sh` — it
prints a paste-and-run command block (heredoc + git add/commit/push) to execute in the Foundry Code Workspace's
own browser terminal. This is the only way to get code changes into Foundry; there is no way to automate it
further from this machine. Always keep `transform/all_orders.py` and the Foundry-side file in sync this way.

## What this project is

A learning exercise to get hands-on with Palantir Foundry's core architecture — datasets → transforms → Ontology
(objects, links, actions) → operational application — using a synthetic "merged office supply companies" order
data use case. The full use case, data spec, build steps, and success criteria are in
[foundry-poc-brief.md](foundry-poc-brief.md); read it in full before starting work, since it is the source of truth
for scope.

Key constraints from the brief, worth repeating because they shape every implementation decision:

- **CLI/SDK-first, GUI as fallback only.** The GUI (Ontology Manager, Workshop, Pipeline Builder) should only be
  used where the platform genuinely requires it. Every time a step can't be done via CLI/SDK/code, say so
  explicitly and flag it — don't silently fall back to GUI instructions.
- **This is a learning exercise, not a production build.** Favor clarity and mirroring real Foundry mechanics over
  robustness, scale, or polish. All source data is synthetic and generated intentionally messy (nulls, mismatched
  keys, inconsistent casing/date formats) so the transform step is meaningful practice.
- **Ontology mental model**: objects are nodes, links are edges, actions are graph-mutating operations. Prioritize
  getting this structure right over UI polish in the operational view.
- Keep a running note of any "had to use GUI here because ___" cases — this list is part of the deliverable.

## Confirmed CLI/SDK gaps (flag these per the brief's guardrail, don't silently use GUI)

- **Object Type / Action Type definition**: `foundry_sdk.v2.ontologies` clients (`ObjectType`, `ActionType`) are
  read-only (`get`/`list`/`get_full_metadata`/`get_edits_history` — no `create`). No "Ontology as Code" template
  exists in this project's Developer Tools wizard either. Defining the `Order` object type and its actions
  requires the Ontology Manager GUI.
- **Build failure diagnostics**: the public API returns build/job/transaction *status* (e.g. `FAILED`/`ABORTED`)
  but no logs or error detail. Diagnosing failures requires reasoning from symptoms (see `foundry_resources.md`
  for two examples: missing dataset schema, and a header row read as data) rather than reading stack traces.
- **CSV header-row handling**: `Dataset.put_schema` has no field for declaring a header row exists (a
  `custom_metadata` key was tried and rejected server-side). Workaround: strip the header line before upload.
