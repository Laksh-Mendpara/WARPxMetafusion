from unsloth import is_bfloat16_supported
from config.model_config import fast_model_config

training_argument = {
    "per_device_train_batch_size": 64,
    "gradient_accumulation_steps": 1,
    "warmup_steps": 5,
    "num_train_epochs": 1,
    "learning_rate": 3e-5,
    "fp16": not is_bfloat16_supported(),
    "bf16": is_bfloat16_supported(),
    "logging_steps": 1,
    # "optim": "adamw_8bit",
    "weight_decay": 0.01,
    "lr_scheduler_type": "linear",
    "seed": 3407,
    "output_dir": "/home/raid3/MetaFusion/WARPxMetafusion/outputs",
    "report_to": "none",
    # "report_to": "tensorboard",
    "eval_strategy": "steps",
    "eval_steps": 50,
    # "max_steps": 100,
}

sft_argument = {
    "dataset_text_field": "text",
    "max_seq_length": fast_model_config["max_seq_length"],
    "dataset_num_proc": 2,
    "packing": False
}
