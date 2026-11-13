"""Run the Phase 3 annotated extraction sample and report strict field-level metrics.

By default this calls the selected LLM provider once per annotated chunk and saves all
predictions, including rejected outputs, to data/extraction_eval_predictions.json.
Pass --reuse to calculate metrics from that saved prediction file without calling a model.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from statuteradar.extraction.extractor import (  # noqa: E402
    enrich_explicit_fields,
    generate_payload,
    validate_payload,
)
from statuteradar.extraction.providers import make_provider  # noqa: E402
from statuteradar.extraction.schema import EXTRACTION_PAYLOAD_ADAPTER  # noqa: E402
from statuteradar.retrieval.corpus import load_chunks  # noqa: E402

GOLD_PATH = ROOT / "data" / "extraction_eval.json"
DEFAULT_PREDICTIONS = ROOT / "data" / "extraction_eval_predictions.json"
DEFAULT_REPORT = ROOT / "data" / "extraction_eval_report.json"
FIELDS = ("modality", "actor", "action", "data_category", "condition", "constraint", "exceptions",
          "qualifier_kind", "qualifier_text", "qualifier_applies_to", "qualifier_condition")


def norm(value: str) -> str:
    value = value.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", value).strip().casefold()


def norm_actor(value: str) -> str:
    value = norm(value)
    roles = re.findall(
        r"\b(data fiduciary|data principal|data subject|central government|"
        r"supervisory authority|service provider|third party|controller|processor|"
        r"business|consumer|contractor|recipient|board)\b", value)
    if not roles:
        return value
    if "controller" in roles and "processor" in roles:
        return "controller or processor"
    return roles[0]


def _counter_for(cases: list[dict], field: str) -> Counter:
    values = Counter()
    for case in cases:
        is_qualifier = field.startswith("qualifier_")
        records = case.get("qualifiers", []) if is_qualifier else case.get("obligations", [])
        key = field.removeprefix("qualifier_") if is_qualifier else field
        for obligation in records:
            raw = obligation.get(key)
            items = raw if key == "exceptions" else [raw]
            for item in items or []:
                if item is not None and str(item).strip():
                    normalized = norm_actor(str(item)) if field == "actor" else norm(str(item))
                    values[(case["chunk_id"], normalized)] += 1
    return values


def _span_prf(gold_cases: list[dict], predicted_cases: list[dict], field: str) -> dict:
    """Token-overlap F1 with greedy per-chunk matching for multi-valued fields."""
    is_qualifier = field.startswith("qualifier_")
    key = field.removeprefix("qualifier_") if is_qualifier else field
    predicted_by_id = {case["chunk_id"]: case for case in predicted_cases}
    token_re = re.compile(r"[\w]+", re.UNICODE)
    tp = fp = fn = 0

    def counts(value):
        return Counter(token_re.findall(norm(str(value)))) if value else Counter()

    for gold_case in gold_cases:
        predicted_case = predicted_by_id.get(gold_case["chunk_id"], {})
        collection = "qualifiers" if is_qualifier else "obligations"
        gold_values = [row.get(key) for row in gold_case.get(collection, [])]
        pred_values = [row.get(key) for row in predicted_case.get(collection, [])]
        if key == "exceptions":
            gold_values = [v for row in gold_case.get("obligations", []) for v in row.get(key, [])]
            pred_values = [v for row in predicted_case.get("obligations", []) for v in row.get(key, [])]
        gold_tokens = [counts(value) for value in gold_values if value]
        pred_tokens = [counts(value) for value in pred_values if value]
        pairs = []
        for gi, gv in enumerate(gold_tokens):
            for pi, pv in enumerate(pred_tokens):
                overlap = sum((gv & pv).values())
                if overlap:
                    total = sum(gv.values()) + sum(pv.values())
                    pairs.append((2 * overlap / total, gi, pi, overlap))
        used_gold, used_pred = set(), set()
        for _, gi, pi, overlap in sorted(pairs, reverse=True):
            if gi in used_gold or pi in used_pred:
                continue
            used_gold.add(gi); used_pred.add(pi)
            tp += overlap
            fp += sum(pred_tokens[pi].values()) - overlap
            fn += sum(gold_tokens[gi].values()) - overlap
        fp += sum(sum(v.values()) for i, v in enumerate(pred_tokens) if i not in used_pred)
        fn += sum(sum(v.values()) for i, v in enumerate(gold_tokens) if i not in used_gold)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"tp_tokens": tp, "fp_tokens": fp, "fn_tokens": fn,
            "precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4)}


def _prf(gold: Counter, predicted: Counter) -> dict:
    true_positive = sum((gold & predicted).values())
    false_positive = sum((predicted - gold).values())
    false_negative = sum((gold - predicted).values())
    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"tp": true_positive, "fp": false_positive, "fn": false_negative,
            "precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4)}


def score(gold: dict, predictions: list[dict], split: str | None = None) -> dict:
    gold_cases = [case for case in gold["cases"] if split is None or case.get("split") == split]
    selected_ids = {case["chunk_id"] for case in gold_cases}
    predictions = [item for item in predictions if item["chunk_id"] in selected_ids]
    prediction_by_id = {item["chunk_id"]: item for item in predictions}
    accepted = [item for item in predictions if item.get("status") == "accepted"]
    schema_valid = [item for item in predictions if item.get("schema_valid")]
    schema_by_id = {item["chunk_id"]: item["draft_payload"] for item in schema_valid}
    outcome_correct = 0
    for case in gold_cases:
        result = schema_by_id.get(case["chunk_id"])
        if result is None:
            continue
        predicted_outcome = result["outcome"]
        outcome_correct += predicted_outcome == case["outcome"]

    gold_obligations = [
        {"chunk_id": case["chunk_id"], "obligations": case["obligations"],
         "qualifiers": case.get("qualifiers", [])}
        for case in gold_cases
    ]
    predicted_obligations = [
        {"chunk_id": item["chunk_id"],
         "obligations": schema_by_id.get(item["chunk_id"], {}).get("obligations", []),
         "qualifiers": schema_by_id.get(item["chunk_id"], {}).get("qualifiers", [])}
        for item in predictions
    ]
    fields = {field: _prf(_counter_for(gold_obligations, field),
                          _counter_for(predicted_obligations, field)) for field in FIELDS}
    span_fields = {
        field: _span_prf(gold_obligations, predicted_obligations, field)
        for field in ("action", "condition", "constraint", "exceptions", "qualifier_text",
                      "qualifier_applies_to", "qualifier_condition")
    }

    exact_gold = Counter()
    exact_predicted = Counter()
    for case in gold_cases:
        for obligation in case["obligations"]:
            exact_gold[(case["chunk_id"], norm(str(obligation.get("modality") or "")),
                        norm_actor(str(obligation.get("actor") or "")),
                        norm(str(obligation.get("action") or "")))] += 1
    for case in predicted_obligations:
        for obligation in case["obligations"]:
            exact_predicted[(case["chunk_id"], norm(str(obligation.get("modality") or "")),
                             norm_actor(str(obligation.get("actor") or "")),
                             norm(str(obligation.get("action") or "")))] += 1

    errors = Counter(item.get("error_type", "") for item in predictions if item.get("status") != "accepted")
    return {
        "sample_size": len(gold_cases),
        "annotator_count": gold.get("annotator_count", 1),
        "schema_valid_rate": round(len(schema_valid) / len(gold_cases), 4) if gold_cases else 0.0,
        "evidence_grounding_rate_among_schema_valid": round(
            sum(bool(item.get("all_quotes_grounded")) for item in schema_valid) / len(schema_valid), 4
        ) if schema_valid else 0.0,
        "pipeline_acceptance_rate": round(len(accepted) / len(gold_cases), 4) if gold_cases else 0.0,
        "outcome_accuracy_among_schema_valid": round(outcome_correct / len(schema_valid), 4) if schema_valid else 0.0,
        "exact_obligation_prf": _prf(exact_gold, exact_predicted),
        "field_exact_value_prf": fields,
        "field_token_overlap_prf": span_fields,
        "rejections": dict(errors),
        "per_chunk": [
            {"chunk_id": case["chunk_id"], "split": case.get("split"), "gold_outcome": case["outcome"],
             "prediction_status": prediction_by_id.get(case["chunk_id"], {}).get("status"),
             "predicted_outcome": schema_by_id.get(case["chunk_id"], {}).get("outcome"),
             "error": prediction_by_id.get(case["chunk_id"], {}).get("error")}
            for case in gold_cases
        ],
    }


def prepare_pipeline_predictions(predictions: list[dict], chunks: dict) -> list[dict]:
    """Apply source-only field completion and pipeline checks to saved raw model outputs."""
    prepared = []
    for original in predictions:
        item = dict(original)
        if not item.get("schema_valid") or "draft_payload" not in item:
            prepared.append(item)
            continue
        chunk = chunks[item["chunk_id"]]
        raw_payload = item.get("raw_payload", item["draft_payload"])
        payload = EXTRACTION_PAYLOAD_ADAPTER.validate_python(raw_payload)
        item["raw_payload"] = raw_payload
        payload = enrich_explicit_fields(chunk, payload)
        item["draft_payload"] = payload.model_dump(mode="json")
        item["all_quotes_grounded"] = all(
            norm(obligation.evidence_quote) in norm(chunk.text)
            for obligation in payload.obligations
        ) and all(norm(qualifier.evidence_quote) in norm(chunk.text)
                  for qualifier in payload.qualifiers)
        try:
            result = validate_payload(chunk, payload)
            item.update(status="accepted", result=result.model_dump(mode="json"))
            item.pop("error_type", None)
            item.pop("error", None)
        except Exception as exc:
            item.update(status="rejected", error_type=type(exc).__name__, error=str(exc))
            item.pop("result", None)
        prepared.append(item)
    return prepared


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path, default=DEFAULT_PREDICTIONS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--reuse", action="store_true", help="score an existing predictions file")
    args = parser.parse_args()
    gold = json.loads(GOLD_PATH.read_text(encoding="utf-8"))
    chunks = {chunk.chunk_id: chunk for chunk in load_chunks()}

    if args.reuse:
        predictions = json.loads(args.predictions.read_text(encoding="utf-8"))
    else:
        provider = make_provider()
        predictions = []
        for case in gold["cases"]:
            chunk_id = case["chunk_id"]
            record = {"chunk_id": chunk_id, "schema_valid": False}
            try:
                chunk = chunks[chunk_id]
                payload = generate_payload(chunk, provider)
                draft = payload.model_dump(mode="json")
                draft["obligations"] = draft.get("obligations", [])
                record.update(schema_valid=True, raw_payload=draft, draft_payload=draft)
            except Exception as exc:  # retain rejected cases in the denominator
                record.update(status="rejected", error_type=type(exc).__name__, error=str(exc))
            predictions.append(record)
            args.predictions.parent.mkdir(parents=True, exist_ok=True)
            args.predictions.write_text(json.dumps(predictions, ensure_ascii=False, indent=2) + "\n",
                                        encoding="utf-8")
            print(f"{chunk_id}: {'accepted' if record.get('schema_valid') else record.get('status', 'rejected')}", flush=True)

    predictions = prepare_pipeline_predictions(predictions, chunks)
    args.predictions.write_text(json.dumps(predictions, ensure_ascii=False, indent=2) + "\n",
                                encoding="utf-8")
    report = {
        "overall": score(gold, predictions),
        "splits": {
            split: score(gold, predictions, split=split)
            for split in ("dev", "test")
        },
    }
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report_text, encoding="utf-8")
    print(report_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
