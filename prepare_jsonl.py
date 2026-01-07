import pandas as pd
import json
import argparse
import math

def chunk_dataframe(df, chunk_size=30):
    for i in range(0, len(df), chunk_size):
        yield df.iloc[i:i+chunk_size]

def make_instruction_block(chunk, file_name):
    text_rows = chunk.to_dict(orient="records")

    return {
        "text": (
            "### Instruction:\n"
            "Analyse the following telemetry data. Identify anomalies, summarise system behaviour, "
            "and provide useful insights.\n\n"
            f"### Source file: {file_name}\n\n"
            f"### Telemetry:\n{json.dumps(text_rows, indent=2)}\n\n"
            "### Response:\n"
            "Normal operation observed. No major anomalies detected. (EDIT THIS BEFORE TRAINING)"
        )
    }

def convert_csv_to_jsonl(csv_file, output_file, chunk_size=30, limit=500):
    df = pd.read_csv(csv_file, on_bad_lines='skip', engine='python')
    items = []

    for idx, chunk in enumerate(chunk_dataframe(df, chunk_size)):
        if idx >= limit:
            break
        items.append(make_instruction_block(chunk, csv_file))

    with open(output_file, "w") as f:
        for ex in items:
            f.write(json.dumps(ex) + "\n")

    print(f"Wrote {len(items)} examples → {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--chunk_size", type=int, default=30)
    parser.add_argument("--limit", type=int, default=500)
    args = parser.parse_args()

    convert_csv_to_jsonl(args.input, args.output, args.chunk_size, args.limit)