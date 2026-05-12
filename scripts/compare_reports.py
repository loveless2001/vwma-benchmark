#!/usr/bin/env python3
"""Compute VSTB report deltas required by the VWMA spec."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def overall(report: dict[str, Any]) -> float:
    return float(report["aggregate"]["overall"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-report", required=True)
    parser.add_argument("--state-report", required=True)
    parser.add_argument("--state-cleared-report", required=True)
    parser.add_argument("--no-gates-report", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    base = load(args.base_report)
    state = load(args.state_report)
    cleared = load(args.state_cleared_report)
    no_gates = load(args.no_gates_report)

    result = {
        "fixed_model_delta": overall(state) - overall(base),
        "state_use_delta": overall(state) - overall(cleared),
        "gate_use_delta": overall(state) - overall(no_gates),
        "trust_allocation_error_rate": 1.0 - state["aggregate"]["trust_allocation_correctness"],
        "explanation_faithfulness": state["aggregate"]["explanation_faithfulness"],
        "reports": {
            "base": args.base_report,
            "state": args.state_report,
            "state_cleared": args.state_cleared_report,
            "no_gates": args.no_gates_report,
        },
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
