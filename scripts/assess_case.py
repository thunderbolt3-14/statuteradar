"""Run the Phase 5 conservative triage engine on a structured JSON case.

Example:
  python scripts/assess_case.py examples/phase5/synthetic_conflict.json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from statuteradar.analysis.assessment import assess_case  # noqa: E402
from statuteradar.api import AssessmentRequestInput  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSON assessment request")
    parser.add_argument("--output", type=Path, help="optional result JSON path")
    args = parser.parse_args()
    try:
        request = AssessmentRequestInput.model_validate_json(args.input.read_text(encoding="utf-8"))
        result = json.dumps(asdict(assess_case(request.to_core())), ensure_ascii=False, indent=2)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"assessment input invalid: {exc}\n")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result + "\n", encoding="utf-8")
        print(f"Saved assessment to {args.output}")
    else:
        print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
