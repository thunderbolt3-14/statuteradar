"""Deprecated parser retained to explain the replacement command.

The older implementation expected obsolete columns such as ``outcome_a`` and silently
produced a flat 56-row structure that the evaluator cannot consume. Use
``scripts/build_adjudicated_eval.py`` instead. Its canonical output is
``data/extraction_eval_adjudicated.json`` and it validates JSON fields, field counts, and source
evidence quotes. The existing legacy file is intentionally left untouched.
"""

if __name__ == "__main__":
    raise SystemExit(
        "This parser is deprecated. Run: python scripts/build_adjudicated_eval.py "
        "--output data/annotations/extraction_eval_adjudicated_rebuilt.json"
    )
