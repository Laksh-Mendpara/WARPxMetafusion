from dataset_util import get_data
from trainer_utils import get_trainer
from model_util import (
    load_model,
    get_param_details
)

def main():
    train_data_path = "./data_v2/data_v1.csv"
    eval_data_path = "./data_v2/eval_data_v1.csv"
    train_data_path = "./data_v2/data_v1.csv"
    eval_data_path = "./data_v2/eval_data_v1.csv"

    config = {
        "num_train_epochs": 1,
        "per_device_train_batch_size": 2,
        "learning_rate": 1.37266e-6,
        "weight_decay": 0.00345076,
        "lr_scheduler_type": "cosine_with_restarts",
        "lora_alpha": 256,
        "warmup_ratio": 0.199927,
        "lora_dropout": 0.0650687,
        "output_dir": "outputs_try01"
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

    #####
    print(tokenizer.decode(trainer.train_dataset[5]["input_ids"]))
    print(tokenizer.decode(trainer.eval_dataset[5]["input_ids"]))
    #####
    exit()

    trainer.train()

    print("Training completed...")

    model.save_pretrained_gguf(
        "out_try01", 
        tokenizer, 
        quantization_method = ["q4_k_m", "q8_0"]
    )
    
    # model.push_to_hub(
    #     "Diwanshuydv/qwen2.5-0.5B-coder-Instruct-sft-final-test", # Change hf to your username!
    #     tokenizer,
    #     token = "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", # Get a token at https://huggingface.co/settings/tokens
    # )

if __name__=="__main__":
    main()
