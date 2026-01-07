# ============================================================
# Fine-tuning Llama 3.1 (8B) using HuggingFace Trainer
# ============================================================

from peft import LoraConfig, get_peft_model
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    BitsAndBytesConfig,
)
import torch

# ------------------------------
# Configuration
# ------------------------------
MODEL_NAME = "./llama-3.1-8b"  # Local path for Llama 3.1 8B (downloaded via huggingface-cli)
MAX_SEQ_LENGTH = 512  # lowered to reduce memory usage on MPS
BATCH_SIZE = 1
GRAD_ACCUM = 8  # increase accumulation to keep effective batch size
LR = 2e-4

# ------------------------------
# Load Base Model (with LoRA)
# ------------------------------
print("Loading model...")
# select device early so we can choose loading options that avoid 'meta' params on MPS
if torch.cuda.is_available():
    _device = "cuda"
elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
    _device = "mps"
else:
    _device = "cpu"

# If running on MPS, avoid low_cpu_mem_usage because it may place params on 'meta' device
low_cpu_mem_usage = False if _device == "mps" else True

# If CUDA is available, load the model in 4-bit using bitsandbytes for much lower memory usage.
if _device == "cuda":
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
    )
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        device_map="auto",
        quantization_config=bnb_config,
        trust_remote_code=True,
        low_cpu_mem_usage=True,
    )
    # set dtype to float16 for CUDA paths
    dtype = torch.float16
else:
    dtype = torch.float32
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype=dtype,
        device_map="auto",
        trust_remote_code=True,
        low_cpu_mem_usage=low_cpu_mem_usage,
    )
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

# Ensure tokenizer has a pad token (some tokenizers don't). Use eos_token as pad if missing.
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# Enable gradient checkpointing only on CUDA (MPS + meta-params can cause backward errors)
if _device == "cuda":
    try:
        model.gradient_checkpointing_enable()
    except Exception:
        pass

print("Applying LoRA...")
lora_config = LoraConfig(
    r=16,
    lora_alpha=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)
model = get_peft_model(model, lora_config)

# ------------------------------
# Load Training Data
# ------------------------------
print("Loading train & validation datasets...")

dataset = load_dataset("json", data_files="train.jsonl", split="train")
val_dataset = load_dataset("json", data_files="valid.jsonl", split="train")

# Tokenize datasets for causal language modeling
def tokenize_function(examples):
    return tokenizer(examples["text"], truncation=True, max_length=MAX_SEQ_LENGTH)

print("Tokenizing datasets...")
tokenized_train = dataset.map(tokenize_function, batched=True, remove_columns=dataset.column_names)
tokenized_val = val_dataset.map(tokenize_function, batched=True, remove_columns=val_dataset.column_names)

data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

# ------------------------------
# Trainer (transformers)
# ------------------------------
training_args = TrainingArguments(
    output_dir="llama-3.1-8b-cansat-lora",
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    warmup_steps=10,
    learning_rate=LR,
    lr_scheduler_type="cosine",
    num_train_epochs=2,
    logging_steps=10,
    bf16=False,
    fp16=False,
    fp16_full_eval=False,
    optim="adamw_torch",
    use_mps_device=True,  # Enable Metal Performance Shaders for Apple Silicon
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_train,
    eval_dataset=tokenized_val,
    data_collator=data_collator,
)

print("Starting training...")
trainer.train()

print("Saving final LoRA adapter...")
# For PEFT/LoRA, save the adapter weights with `save_pretrained`
model.save_pretrained("llama-3.1-8b-cansat-lora-final")

print("Done.")