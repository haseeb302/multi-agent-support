#!/usr/bin/env bash
# One-time embed of policy docs and upload to Pinecone.
# Loads .env from project root and runs the Python script.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Load .env if present
if [ -f .env ]; then
  set -a
  # shellcheck source=/dev/null
  source .env
  set +a
fi

# Use project venv if it exists
if [ -d .venv ]; then
  source .venv/bin/activate
fi

export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH:-}"
exec python scripts/embed_and_upload.py "$@"
