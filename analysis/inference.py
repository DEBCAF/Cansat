#!/usr/bin/env python3
"""
Simple inference script to load the base Mistral model + a saved PEFT (LoRA) adapter
and run generation for a prompt. Usage examples are shown below.
"""
import argparse
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model-dir", default="./llama-3.1-8b", help="Local base model directory")
    p.add_argument("--adapter-path", default="llama-3.1-8b-cansat-lora-final", help="Saved LoRA adapter directory")
    p.add_argument("--prompt", default=None, help="Prompt text to generate from")
    p.add_argument("--max-new-tokens", type=int, default=256)
    p.add_argument("--no-stream", action="store_true", help="Don't stream tokens; return full generation")
    args = p.parse_args()

    # Choose device
    if torch.cuda.is_available():
        device = "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"

    print(f"Using device: {device}")

    print("Loading base model...")
    base_model = AutoModelForCausalLM.from_pretrained(
        args.model_dir, device_map="auto", trust_remote_code=True, low_cpu_mem_usage=True
    )
    print("Attaching LoRA adapter (local only)...")
    model = PeftModel.from_pretrained(base_model, args.adapter_path, device_map="auto", local_files_only=True)

    tokenizer = AutoTokenizer.from_pretrained(args.model_dir)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    if args.prompt is None:
        print("No --prompt provided. Example usage:")
        print("python inference.py --prompt \"### Instruction:\nAnalyse telemetry...\" --max-new-tokens 200")
        return

    inputs = tokenizer(args.prompt, return_tensors="pt")
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    model.eval()
    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=args.max_new_tokens)

    text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(text)


if __name__ == "__main__":
    main()
