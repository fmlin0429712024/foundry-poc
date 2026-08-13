# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

This repository currently contains only [foundry-poc-brief.md](foundry-poc-brief.md) — no code, data, or Foundry
project scaffolding exists yet. It is not (yet) a git repository. Treat any architecture, commands, or file
structure beyond what's below as **not yet built** — don't assume prior sessions created it unless you can see it
in the working tree.

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

## Working with this repo

Since there is no established structure yet, check the current working tree before assuming file locations for
synthetic data, transform code, or Ontology-as-Code definitions — don't reuse paths from memory of a previous
session without verifying they still exist.
