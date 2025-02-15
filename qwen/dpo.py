from dataset_util import get_data
from trl import DPOConfig, DPOTrainer
from trainer_utils import get_trainer
from model_util import (
    load_model,
    get_param_details
)
from datasets import load_dataset

def main():
    train_data_path = "data/data_v5.csv"
    eval_data_path = "data/eval_data_v4.csv"

    config = {
        "num_train_epochs": 1,
        "per_device_train_batch_size": 8,
        "learning_rate": 7.54132e-06,
        "weight_decay": 0.0502397,
        "lr_scheduler_type": "cosine_with_restarts",
        "lora_alpha": 32,
        "warmup_ratio": 0.197403,
        "lora_dropout": 0.0742568,
        "output_dir": "outputs"
    }

    model, tokenizer = load_model(config=config)

    train_dataset = load_dataset("trl-lib/ultrafeedback_binarized", split="train")

    training_args = DPOConfig(
        output_dir="Qwen2-0.5B-DPO", 
        logging_steps=10
    )

    trainer = DPOTrainer(
        model=model, 
        args=training_args, 
        processing_class=tokenizer, 
        train_dataset=train_dataset
    )
    trainer.train()

    print("Training completed...")

    # model.save_pretrained_gguf(
    #     "qwen0.5_512_fine_model_tuned_ins", 
    #     tokenizer, 
    #     quantization_method = ["q4_k_m", "q8_0"]
    # ) 
    
    # tokenizer.save_pretrained_gguf("qwen0.5_512_fine_model_tuned")
    
    model.push_to_hub_gguf(
        "Diwanshuydv/qwen2.5-0.5B-coder-Instruct-_NL2MONGODB_fin_tuned", # Change hf to your username!
        tokenizer,
        quantization_method = ["q4_k_m", "q8_0"],
        token = "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", # Get a token at https://huggingface.co/settings/tokens
    )

if __name__=="__main__":
    main()
