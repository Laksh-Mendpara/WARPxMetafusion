from dataset_util import get_data
from trainer_utils import get_trainer
from model_util import (
    load_model,
    get_param_details
)

def main():
    train_data_path = "data/data_v6.csv"
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

    train_data = get_data(
        file_path=train_data_path,
        tokenizer=tokenizer
    )

    eval_data = get_data(
        file_path=eval_data_path,
        tokenizer=tokenizer
    )

    trainer = get_trainer(
        model=model,
        train_dataset=train_data,
        eval_dataset=eval_data,
        tokenizer=tokenizer,
        config=config
    )

    trainer.train()

    print("Training completed...")

    # model.save_pretrained_gguf(
    #     "qwen0.5_512_fine_model_tuned_ins", 
    #     tokenizer, 
    #     quantization_method = ["q4_k_m", "q8_0"]
    # ) 
    
    # tokenizer.save_pretrained_gguf("qwen0.5_512_fine_model_tuned")
    
    model.push_to_hub(
        "Diwanshuydv/qwen2.5-0.5B-coder-Instruct-_NL2MONGODB_fin_tuned", # Change hf to your username!
        tokenizer,
        token = "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", # Get a token at https://huggingface.co/settings/tokens
    )

if __name__=="__main__":
    main()
