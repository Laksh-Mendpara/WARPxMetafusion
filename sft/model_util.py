from unsloth import FastLanguageModel
from config.model_config import(
    fast_model_config,
    peft_model_config
)
from typing_extensions import Dict, Any

def load_fast_model():
    model, tokenizer = FastLanguageModel.from_pretrained(
        **fast_model_config
    )
    return model, tokenizer

def load_peft_model(model, config):
    merged_config = {**peft_model_config, **(config or {})}
    merged_config = {k: merged_config[k] for k in peft_model_config.keys()}
    return FastLanguageModel.get_peft_model(
        model,
        **merged_config
    )

def load_model(config: Dict[str, Any] = None):
    model, tokenizer = load_fast_model()
    model = load_peft_model(model, config)
    return model, tokenizer

def get_param_details(model: Any) -> str:
    trainable_model_params = 0
    all_model_params = 0
    for _, param in model.named_parameters():
        all_model_params += param.numel()
        if param.requires_grad:
            trainable_model_params += param.numel()
    return f"trainable model parameters: {trainable_model_params}\nall model parameters: {all_model_params}\npercentage of trainable model parameters: {100 * trainable_model_params / all_model_params:.2f}%"
