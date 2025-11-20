#!/usr/bin/env python3
"""Stub executor that pretends to apply an OpenSpec plan.

This script lets ai-clean run end-to-end in local/dev environments where the
real `openspec apply` command is unavailable. It simply verifies the spec file
exists, prints a short message, and exits with success so downstream steps
(e.g., pytest) still run.
"""

from __future__ import annotations

import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: apply_spec_stub.py /path/to/spec.yaml", file=sys.stderr)
        return 2

    spec_path = Path(argv[1]).expanduser().resolve()
    if not spec_path.is_file():
        print(f"Spec file not found: {spec_path}", file=sys.stderr)
        return 3

    print(f"[stub] Would apply spec located at {spec_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
