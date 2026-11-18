"""Build a structured Phase 3 gold file from the two packets and adjudication CSV."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PACKET_A = ROOT / "data" / "annotations" / "annotation_packet_filled_nagasai.csv"
PACKET_B = ROOT / "data" / "annotations" / "annotation_packet_rahul.csv"
ADJUDICATION = ROOT / "data" / "annotations" / "annotation_adjudication.csv"
MASTER = ROOT / "data" / "annotation_packet.csv"
SOURCE_GOLD = ROOT / "data" / "extraction_eval.json"
DEFAULT_OUTPUT = ROOT / "data" / "extraction_eval_adjudicated.json"
JSON_FIELDS = {
    "modality": "modality",
    "actor": "actor",
    "action": "action",
    "data_category": "data_category",
    "condition_constraint_exception": "conditions",
    "scope_qualifier": "qualifiers",
    "evidence_quote": "evidence_quote",
}
ANNOTATION_FIELDS = set(JSON_FIELDS) | {"outcome"}
IDENTITY_FIELDS = {"chunk_id", "source_text"}
NOTE_FIELD = "uncertainty_notes"


def normalize(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip()).casefold()


def read_packet(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not {"chunk_id", "source_text"}.issubset(reader.fieldnames or []):
            raise ValueError(f"{path.name} needs chunk_id and source_text columns")
        records: dict[str, dict[str, str]] = {}
        for line_number, row in enumerate(reader, start=2):
            chunk_id = (row.get("chunk_id") or "").strip()
            if not chunk_id:
                raise ValueError(f"{path.name}: blank chunk_id on line {line_number}")
            if chunk_id in records:
                raise ValueError(f"{path.name}: duplicate chunk_id {chunk_id}")
            records[chunk_id] = row
    return records


def parse_json_cell(value: str, *, chunk_id: str, field: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{chunk_id} field {field}: invalid JSON in annotation value: {exc}") from exc


def build_case(
    chunk_id: str,
    split: str,
    values: dict[str, str],
    source_text: str,
) -> dict[str, Any]:
    outcome = values["outcome"].strip()
    if outcome not in {"obligations", "no_obligation"}:
        raise ValueError(f"{chunk_id}: unsupported outcome {outcome!r}")

    parsed = {
        target: parse_json_cell(values[source], chunk_id=chunk_id, field=source)
        for source, target in JSON_FIELDS.items()
    }
    if not isinstance(parsed["modality"], list):
        raise ValueError(f"{chunk_id}: modality must be a JSON list")
    for field in ("actor", "action", "data_category", "evidence_quote", "conditions", "qualifiers"):
        if not isinstance(parsed[field], list):
            raise ValueError(f"{chunk_id}: {field} must be a JSON list")

    def require_grounded_quote(quote: Any, label: str) -> None:
        if not isinstance(quote, str) or not quote.strip():
            raise ValueError(f"{chunk_id}: {label} must be a non-empty quote")
        if normalize(quote) not in normalize(source_text):
            raise ValueError(f"{chunk_id}: {label} is not present in the source provision")

    obligations: list[dict[str, Any]] = []
    if outcome == "obligations":
        modalities = parsed["modality"]
        fields_to_zip = [
            parsed["actor"],
            parsed["action"],
            parsed["data_category"],
            parsed["conditions"],
            parsed["evidence_quote"],
        ]
        expected = len(modalities)
        if expected == 0 or any(len(field) != expected for field in fields_to_zip):
            lengths = [len(modalities), *(len(field) for field in fields_to_zip)]
            raise ValueError(f"{chunk_id}: obligation field list lengths do not match: {lengths}")

        for i, modality in enumerate(modalities):
            if modality not in {"MUST", "MUST_NOT", "MAY"}:
                raise ValueError(f"{chunk_id}: unsupported modality {modality!r}")
            require_grounded_quote(parsed["evidence_quote"][i], f"evidence_quote[{i}]")
            condition_record = parsed["conditions"][i]
            if not isinstance(condition_record, dict):
                raise ValueError(f"{chunk_id}: conditions[{i}] must be an object")
            exceptions = condition_record.get("exceptions", [])
            if not isinstance(exceptions, list):
                raise ValueError(f"{chunk_id}: exceptions for obligation {i + 1} must be a list")
            obligations.append(
                {
                    "modality": modality,
                    "actor": parsed["actor"][i],
                    "action": parsed["action"][i],
                    "data_category": parsed["data_category"][i],
                    "condition": condition_record.get("condition"),
                    "constraint": condition_record.get("constraint"),
                    "exceptions": exceptions,
                }
            )
    elif any(parsed[field] for field in ("modality", "actor", "action", "data_category", "conditions", "evidence_quote")):
        raise ValueError(f"{chunk_id}: no_obligation outcome must have empty obligation fields")

    for i, qualifier in enumerate(parsed["qualifiers"]):
        if not isinstance(qualifier, dict):
            raise ValueError(f"{chunk_id}: qualifier {i + 1} must be a JSON object")
        if qualifier.get("kind") not in {"exception", "scope"}:
            raise ValueError(f"{chunk_id}: qualifier {i + 1} has an unsupported kind")
        require_grounded_quote(qualifier.get("evidence_quote"), f"qualifier {i + 1} evidence_quote")

    return {
        "chunk_id": chunk_id,
        "split": split,
        "outcome": outcome,
        "obligations": obligations,
        "qualifiers": parsed["qualifiers"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--packet-a", type=Path, default=PACKET_A)
    parser.add_argument("--packet-b", type=Path, default=PACKET_B)
    parser.add_argument("--adjudication", type=Path, default=ADJUDICATION)
    parser.add_argument("--master", type=Path, default=MASTER)
    parser.add_argument("--manifest", type=Path,
                        help="case/split manifest for a new evaluation set; defaults to the original 16 cases")
    args = parser.parse_args()

    try:
        packet_a = read_packet(args.packet_a)
        packet_b = read_packet(args.packet_b)
        master = read_packet(args.master)
        adjudication_rows = list(
            csv.DictReader(args.adjudication.open("r", encoding="utf-8-sig", newline=""))
        )
        if args.manifest:
            manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
            gold_cases = manifest["cases"]
        else:
            source_gold = json.loads(SOURCE_GOLD.read_text(encoding="utf-8"))
            gold_cases = source_gold["cases"]
        gold_by_id = {case["chunk_id"]: case for case in gold_cases}

        if len(gold_by_id) != len(gold_cases):
            raise ValueError("Original extraction evaluation has duplicate chunk IDs")
        annotated_ids_a = {
            chunk_id for chunk_id, row in packet_a.items() if normalize(row.get("outcome"))
        }
        annotated_ids_b = {
            chunk_id for chunk_id, row in packet_b.items() if normalize(row.get("outcome"))
        }
        if annotated_ids_a != set(gold_by_id) or annotated_ids_b != set(gold_by_id):
            raise ValueError("Annotated packet IDs must match the selected evaluation manifest/cases")
        if set(packet_a) != set(packet_b):
            raise ValueError("The two annotator packets do not have identical chunk IDs")
        if not set(packet_a).issubset(master):
            raise ValueError("One or more annotator packet IDs are missing from the master packet")

        overrides: dict[tuple[str, str], str] = {}
        for row in adjudication_rows:
            chunk_id, field = (row.get("chunk_id") or "").strip(), (row.get("field") or "").strip()
            if not chunk_id or field not in ANNOTATION_FIELDS:
                raise ValueError(f"Invalid adjudication row: chunk_id={chunk_id!r}, field={field!r}")
            key = (chunk_id, field)
            if key in overrides:
                raise ValueError(f"Duplicate adjudication for {chunk_id}, {field}")
            value = row.get("adjudicated_value") or ""
            note = row.get("adjudication_note") or ""
            if not value.strip() or not note.strip():
                raise ValueError(f"Unresolved adjudication for {chunk_id}, {field}")
            overrides[key] = value

        expected_overrides: set[tuple[str, str]] = set()
        for chunk_id in sorted(gold_by_id):
            for field in ANNOTATION_FIELDS:
                value_a = packet_a[chunk_id].get(field) or ""
                value_b = packet_b[chunk_id].get(field) or ""
                if normalize(value_a) != normalize(value_b):
                    expected_overrides.add((chunk_id, field))
        if set(overrides) != expected_overrides:
            missing = len(expected_overrides - set(overrides))
            extra = len(set(overrides) - expected_overrides)
            raise ValueError(f"Adjudications do not exactly cover disagreements: missing={missing}, extra={extra}")

        output_cases = []
        for original in gold_cases:
            chunk_id = original["chunk_id"]
            values: dict[str, str] = {}
            for field in ANNOTATION_FIELDS:
                value_a = packet_a[chunk_id].get(field) or ""
                value_b = packet_b[chunk_id].get(field) or ""
                values[field] = overrides.get((chunk_id, field), value_a)
            for packet in (packet_a, packet_b):
                if (packet[chunk_id].get("source_text") or "").strip() != (
                    master[chunk_id].get("source_text") or ""
                ).strip():
                    raise ValueError(f"Source text mismatch for {chunk_id}")
            output_cases.append(
                build_case(
                    chunk_id,
                    original["split"],
                    values,
                    master[chunk_id].get("source_text") or "",
                )
            )

        if args.manifest:
            annotation_note = (
                "Two independent human annotation packets, with disagreements adjudicated. "
                "Fresh held-out diagnostic set; no model predictions were used for adjudication."
            )
        else:
            annotation_note = (
                "Two independent human annotation packets, with field disagreements adjudicated. "
                "This is the original 16-case diagnostic set, not a fresh test set or legal opinion."
            )
        output = {
            "title": "StatuteRadar Phase 3 adjudicated human annotations",
            "version": 3,
            "annotator_count": 2,
            "annotator_note": annotation_note,
            "cases": output_cases,
        }
        output_path = args.output if args.output.is_absolute() else ROOT / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_path.exists():
            raise FileExistsError(f"Refusing to overwrite existing output: {output_path}")
        output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Built {len(output_cases)} structured adjudicated cases: {output_path}")
        print("Original labels, annotator packets, and model predictions were left unchanged.")
        return 0
    except (OSError, csv.Error, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"Could not build adjudicated evaluation: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
