#!/usr/bin/env bash
# Prints a paste-and-run command block that creates/updates the Foundry
# Code Repository's transform file to match transform/all_orders.py, then
# commits and pushes it inside Foundry's own git.
#
# Why this exists: Foundry's Code Repository git remote
# (stemma-git, see scripts/foundry_resources.md) is only reachable from
# inside Foundry's cluster network — this machine has no route to it, and
# the public Foundry API has no endpoint to write files into a Code
# Repository. So GitHub (this repo) is the source of truth; this script
# is the manual "promote to Foundry" step, run after every change to
# transform/all_orders.py.
#
# Usage: run this script, then paste its output into the Foundry Code
# Workspace's terminal (Terminal > New Terminal in the browser VS Code).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TRANSFORM_FILE="$REPO_ROOT/transform/all_orders.py"
FOUNDRY_TARGET_PATH="transforms-python/src/myproject/datasets/all_orders.py"

if [ ! -f "$TRANSFORM_FILE" ]; then
    echo "ERROR: $TRANSFORM_FILE not found" >&2
    exit 1
fi

echo "cat > $FOUNDRY_TARGET_PATH << 'PYEOF'"
cat "$TRANSFORM_FILE"
echo "PYEOF"
echo "git add $FOUNDRY_TARGET_PATH"
echo "git commit -m 'Sync all_orders transform from GitHub (fmlin0429712024/foundry-poc)'"
echo "git push"
