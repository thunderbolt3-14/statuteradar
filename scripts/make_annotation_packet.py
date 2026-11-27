import json
import csv
import os

input_path = "data/processed/chunks.jsonl"
output_path = "data/annotation_packet.csv"

# Define columns: pre-filled with ID and text, rest left blank for the annotator
fieldnames = [
    "chunk_id",
    "source_text",
    "outcome",
    "modality",
    "actor",
    "action",
    "data_category",
    "condition_constraint_exception",
    "scope_qualifier",
    "evidence_quote",
    "uncertainty_notes"
]

if not os.path.exists(input_path):
    print(f"Error: Could not find {input_path}. Check your path.")
    exit(1)

with open(input_path, "r", encoding="utf-8") as infile, \
     open(output_path, "w", newline="", encoding="utf-8") as outfile:
    
    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
    writer.writeheader()

    for line in infile:
        if not line.strip():
            continue
        data = json.loads(line)
        
        # Adjust 'text' or 'content' depending on your JSON key name
        text_content = data.get("text", data.get("content", ""))
        
        writer.writerow({
            "chunk_id": data.get("chunk_id", ""),
            "source_text": text_content,
            "outcome": "",
            "modality": "",
            "actor": "",
            "action": "",
            "data_category": "",
            "condition_constraint_exception": "",
            "scope_qualifier": "",
            "evidence_quote": "",
            "uncertainty_notes": ""
        })

print(f"Successfully generated annotation packet at: {output_path}")