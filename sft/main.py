from .dataset_util import get_data
from .trainer_utils import get_trainer
from .model_util import (
    load_model,
    get_param_details
)

def main():
    train_data_path = "./data_v3/data_v2.csv"
    eval_data_path = "./data_v3/eval_data_v2.csv"

    # train_data_path = "./data_v2/data_v1.csv"
    # eval_data_path = "./data_v2/eval_data_v1.csv"

    config = {
        # "num_train_epochs": 1,
        # "per_device_train_batch_size": 2,
        # "learning_rate": 1.37266e-6,
        # "weight_decay": 0.00345076,
        # "lr_scheduler_type": "cosine_with_restarts",
        # "lora_alpha": 256,
        # "warmup_ratio": 0.199927,
        # "lora_dropout": 0.0650687,
        # "output_dir": "outputs_try00s",
        # 'model_name': 'unsloth/Qwen2.5-Coder-1.5B-Instruct', 
        # 'num_train_epochs': 2, 
        # 'per_device_train_batch_size': 2, 
        # 'learning_rate': 4.718380793118908e-05, 
        # 'weight_decay': 1.0804946625058698e-05, 
        # 'lr_scheduler_type': 'cosine_with_restarts', 
        # 'lora_alpha': 16, 
        # 'warmup_ratio': 0.07141668035341375, 
        # 'lora_dropout': 0.11702589586723894, 
        # 'output_dir': '/home/raid/metafusion/WARPxMetafusion/outputs/num_train_epochs_2_per_device_train_batch_size_2_learning_rate_4.718380793118908e-05_weight_decay_1.0804946625058698e-05_lr_scheduler_type_cosine_with_restarts_lora_alpha_16_warmup_ratio_0.07141668035341375_lora_dropout_0.11702589586723894_'
    }

    model, tokenizer = load_model(config=config)

    approach_v3 = True

    train_data = get_data(
        file_path=train_data_path,
        tokenizer=tokenizer,
        approach_v3=approach_v3,
    )

    eval_data = get_data(
        file_path=eval_data_path,
        tokenizer=tokenizer,
        approach_v3=approach_v3,
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
