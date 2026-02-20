#!/usr/bin/env python3
"""
Run the support agent for one user message (Phase 3).
Usage: python scripts/run_agent_cli.py "your message"
Requires: OPENAI_API_KEY or LLM_API_KEY in env; docs (customers.csv, retention_rules.json); optional Pinecone for RAG.
"""
from __future__ import annotations

import sys

from app.agents.runner import run_agent


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_agent_cli.py \"your message\"", file=sys.stderr)
        sys.exit(1)
    message = " ".join(sys.argv[1:]).strip()
    if not message:
        print("Usage: python scripts/run_agent_cli.py \"your message\"", file=sys.stderr)
        sys.exit(1)
    reply, result, _, _ = run_agent(message)
    print("[Route]", result.route)
    if result.tool_calls:
        print("[Tools]", [t.name for t in result.tool_calls])
    print("[Reply]", reply)


if __name__ == "__main__":
    main()
