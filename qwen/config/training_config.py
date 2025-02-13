from unsloth import is_bfloat16_supported
from model_config import fast_model_config

training_argument = {
    "per_device_train_batch_size": 2,
    "gradient_accumulation_steps": 4,
    "warmup_steps": 5,
    "num_train_epochs": 3,
    "learning_rate": 3e-4,
    "fp16": not is_bfloat16_supported(),
    "bf16": is_bfloat16_supported(),
    "logging_steps": 1,
    "optim": "adamw_8bit",
    "weight_decay": 0.01,
    "lr_scheduler_type": "linear",
    "seed": 3407,
    "output_dir": "outputs",
    "report_to": "none"
}

sft_argument = {
    "dataset_text_field": "text",
    "max_seq_length": fast_model_config["max_seq_lenght"],
    "dataset_num_proc": 2,
    "packing": False, 
}
