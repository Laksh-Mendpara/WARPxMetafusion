fast_model_config = {
    "model_name": "unsloth/Qwen2.5-0.5B-Instruct",
    "max_seq_length": 4096,
    "dtype": None,
    "load_in_4bit": True
}

peft_model_config = {
    "r": 512,
    "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj",
                       "gate_proj", "up_proj", "down_proj",],
    "lora_alpha": 16,
    "lora_dropout": 0,
    "bias": "none",
    "use_gradient_checkpointing": "unsloth",
    "random_state": 3407,
    "use_rslora": True,
    "loftq_config": None
}