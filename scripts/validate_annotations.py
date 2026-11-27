"""Check two completed annotation packets against each other and the blank source packet."""

from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MASTER_PATH = ROOT / "data" / "annotation_packet.csv"
ANNOTATOR_A_PATH = ROOT / "data" / "annotations" / "annotation_packet_filled_nagasai.csv"
ANNOTATOR_B_PATH = ROOT / "data" / "annotations" / "annotation_packet_rahul.csv"
REQUIRED_COLUMNS = {"chunk_id", "source_text"}
SOURCE_COLUMNS = {"chunk_id", "source_text"}


def read_packet(path: Path) -> tuple[list[str], dict[str, dict[str, str]]]:
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        missing = REQUIRED_COLUMNS.difference(columns)
        if missing:
            raise ValueError(f"{path.name} is missing required columns: {sorted(missing)}")

        rows: dict[str, dict[str, str]] = {}
        for line_number, row in enumerate(reader, start=2):
            chunk_id = (row.get("chunk_id") or "").strip()
            if not chunk_id:
                raise ValueError(f"{path.name} has a blank chunk_id on line {line_number}")
            if chunk_id in rows:
                raise ValueError(f"{path.name} has duplicate chunk_id {chunk_id!r}")
            rows[chunk_id] = row

    return columns, rows


def main() -> int:
    try:
        master_columns, master = read_packet(MASTER_PATH)
        columns_a, packet_a = read_packet(ANNOTATOR_A_PATH)
        columns_b, packet_b = read_packet(ANNOTATOR_B_PATH)

        print(f"Annotator A ({ANNOTATOR_A_PATH.name}): {len(packet_a)} rows")
        print(f"Annotator B ({ANNOTATOR_B_PATH.name}): {len(packet_b)} rows")
        print(f"Blank master packet: {len(master)} rows")

        ids_a, ids_b, ids_master = set(packet_a), set(packet_b), set(master)
        if ids_a != ids_b:
            raise ValueError(
                f"Annotator chunk IDs differ: A-only={len(ids_a - ids_b)}, "
                f"B-only={len(ids_b - ids_a)}"
            )
        if ids_a != ids_master:
            raise ValueError(
                f"Annotator IDs differ from master: annotator-only={len(ids_a - ids_master)}, "
                f"master-only={len(ids_master - ids_a)}"
            )

        for chunk_id in ids_master:
            master_text = (master[chunk_id].get("source_text") or "").strip()
            text_a = (packet_a[chunk_id].get("source_text") or "").strip()
            text_b = (packet_b[chunk_id].get("source_text") or "").strip()
            if text_a != master_text or text_b != master_text:
                raise ValueError(f"Source text changed for chunk_id {chunk_id!r}")

        annotation_columns = [
            column for column in master_columns if column not in SOURCE_COLUMNS
        ]
        filled_a = sum(
            bool((row.get(column) or "").strip())
            for row in packet_a.values()
            for column in annotation_columns
        )
        filled_b = sum(
            bool((row.get(column) or "").strip())
            for row in packet_b.values()
            for column in annotation_columns
        )

        print(f"Chunk IDs: {len(ids_master)} unique IDs, matching across all three files.")
        print("Source text: matches the blank master packet for every chunk.")
        print(f"Filled annotation cells: A={filled_a}, B={filled_b}.")
        print("Annotation packet integrity validation passed.")
        return 0
    except (OSError, csv.Error, ValueError) as exc:
        print(f"Annotation validation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
