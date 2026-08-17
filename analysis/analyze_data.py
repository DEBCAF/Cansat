#!/usr/bin/env python3
"""
analyze_data.py

Reads a CSV (telemetry), chunks it into manageable pieces, runs the base model + LoRA adapter
on each chunk to produce per-chunk analyses, then aggregates those analyses into a single
in-depth report using iterative summarization to avoid context limits.

Usage:
  python analyze_data.py --model-dir ./mistral-7b --adapter-path mistral-7b-cansat-lora-final \
    --input data_table29.csv --chunk-size 30 --out report.jsonl

Output:
  - <out>_chunks.jsonl : per-chunk analyses
  - <out>_final.txt    : aggregated in-depth analysis

Notes:
- This assumes you have a base model directory and a saved PEFT adapter.
- If your model+adapter are large, device_map="auto" will place weights on available devices.
"""
import argparse
import json
import os
import math
from typing import List

import pandas as pd
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel


def chunk_dataframe(df: pd.DataFrame, chunk_size: int):
    for i in range(0, len(df), chunk_size):
        yield df.iloc[i : i + chunk_size]


def build_prompt_for_chunk(records: List[dict]):
    # Use the same instruction text used for training so the model sees consistent format
    return (
        "### Instruction:\n"
        "Analyse the following telemetry data. Identify anomalies, summarise system behaviour, "
        "and provide useful insights. Present a clear summary, detected anomalies, potential causes, "
        "and recommended next steps. Be concise but thorough.\n\n"
        "### Telemetry:\n"
        f"{json.dumps(records, indent=2)}\n\n"
        "### Response:\n"
    )


def estimate_tokens(text: str, tokenizer) -> int:
    toks = tokenizer.encode(text, return_tensors="pt", add_special_tokens=False)
    return toks.shape[-1]


def iterative_summary(model, tokenizer, texts: List[str], device, max_tokens_out=800):
    """
    Summarize a list of texts into a single summary, using iterative grouping to respect model context.
    """
    model_max = tokenizer.model_max_length

    # Start with raw texts
    items = texts

    while len(items) > 1:
        grouped = []
        cur_group = []
        cur_tok = 0

        for t in items:
            t_tok = estimate_tokens(t, tokenizer)
            # if adding this item would exceed a safe fraction of model_max, flush current group
            if cur_tok + t_tok + 512 > model_max:  # keep 512 tokens free for summary output
                if cur_group:
                    grouped.append("\n\n".join(cur_group))
                cur_group = [t]
                cur_tok = t_tok
            else:
                cur_group.append(t)
                cur_tok += t_tok

        if cur_group:
            grouped.append("\n\n".join(cur_group))

        # For each group, create a summarization prompt and produce a summary
        new_items = []
        for g in grouped:
            prompt = (
                "### Instruction:\nCombine and condense the following chunk-level analyses into a concise, high-quality "
                "summary that highlights the most important anomalies, likely root causes and recommended next steps.\n\n"
                "### ChunkAnalyses:\n"
                f"{g}\n\n"
                "### Summary:\n"
            )
            inputs = tokenizer(prompt, return_tensors="pt")
            inputs = {k: v.to(device) for k, v in inputs.items()}

            with torch.no_grad():
                out = model.generate(**inputs, max_new_tokens=max_tokens_out, do_sample=False)
            text = tokenizer.decode(out[0], skip_special_tokens=True)
            new_items.append(text)

        items = new_items

    # items now length 1
    return items[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", default="./llama-3.1-8b")
    parser.add_argument("--adapter-path", default="llama-3.1-8b-cansat-lora-final")
    parser.add_argument("--input", default="data_table29.csv")
    parser.add_argument("--chunk-size", type=int, default=30)
    parser.add_argument("--out", default="mistral_analysis")
    parser.add_argument("--max-new-tokens", type=int, default=400)
    args = parser.parse_args()

    # load CSV
    df = pd.read_csv(args.input, on_bad_lines="skip", engine="python")

    # device selection
    if torch.cuda.is_available():
        device = torch.device("cuda")
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")

    print(f"Using device: {device}")

    print("Loading base model...")
    base = AutoModelForCausalLM.from_pretrained(
        args.model_dir, device_map="auto", trust_remote_code=True, low_cpu_mem_usage=True
    )
    print("Loading adapter (local only)...")
    model = PeftModel.from_pretrained(base, args.adapter_path, device_map="auto", local_files_only=True)
    tokenizer = AutoTokenizer.from_pretrained(args.model_dir)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    chunk_out_file = args.out + "_chunks.jsonl"
    final_txt = args.out + "_final.txt"

    chunk_results = []

    print(f"Processing {len(df)} rows in chunks of {args.chunk_size}...")
    for idx, chunk in enumerate(chunk_dataframe(df, args.chunk_size)):
        records = chunk.to_dict(orient="records")
        prompt = build_prompt_for_chunk(records)

        inputs = tokenizer(prompt, return_tensors="pt")
        inputs = {k: v.to(model.device) for k, v in inputs.items()}

        print(f"Generating analysis for chunk {idx+1} (rows {idx*args.chunk_size}..)")
        with torch.no_grad():
            out = model.generate(**inputs, max_new_tokens=args.max_new_tokens, do_sample=False)
        text = tokenizer.decode(out[0], skip_special_tokens=True)

        entry = {"chunk_idx": idx, "rows": len(records), "analysis": text}
        chunk_results.append(entry)

        # append to chunks file incrementally
        with open(chunk_out_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    print(f"Wrote per-chunk analyses → {chunk_out_file}")

    # Aggregate per-chunk analyses into final report
    analyses = [c["analysis"] for c in chunk_results]

    print("Aggregating chunk analyses into final in-depth report (may be iterative)...")
    final = iterative_summary(model, tokenizer, analyses, model.device, max_tokens_out=800)

    with open(final_txt, "w") as f:
        f.write(final)

    print(f"Final aggregated report written to {final_txt}")


if __name__ == "__main__":
    main()
