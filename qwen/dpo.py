from dataset_util import get_data
from trl import DPOConfig, DPOTrainer
from trainer_utils import get_trainer
from unsloth import is_bfloat16_supported
from model_util import (
    load_model,
    get_param_details
)
from datasets import Dataset
import pandas as pd 


def load_dpo_data(file_path):
    df = pd.read_csv(file_path)
    
    chosen = df.apply(lambda row: [
        {
            'role': 'user', 
            'content': f"""
            You are a specialist in translating natural language instructions into precise, efficient MongoDB queries. Follow the given database schema exactly—do not invent or modify field names or collections—and produce only the simplest query that fulfills the request.
            Schema: {row['schema']}
            NL Query: {row['natural_language_query']}
            MONGODB Query:
            """
        },
        {
            'role': 'assistant', 
            'content': row['corret_mongo_query']
        }
    ], axis=1).tolist()


    rejected = df.apply(lambda row: [
        {
            'role': 'user', 
            'content': f"""
            You are a specialist in translating natural language instructions into precise, efficient MongoDB queries. Follow the given database schema exactly—do not invent or modify field names or collections—and produce only the simplest query that fulfills the request.
            Schema: {row['schema']}
            NL Query: {row['natural_language_query']}
            MONGODB Query:
            """},
        {
            'role': 'assistant', 
            'content': row['incorrect_mongo_query']
        }], axis=1).tolist()
    

    return Dataset.from_dict({"chosen": chosen, "rejected": rejected})


def main():

    train_data_path = "/data/meta/WARPxMetafusion/data/dpo_data_1600.csv"
    eval_data_path = "/data/meta/WARPxMetafusion/data/eval_dpo_data.csv"

    config = {
        "model_name": "Diwanshuydv/qwen2.5-0.5B-coder-Instruct-_NL2MONGODB_fin_tuned",
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

    train_dataset = load_dpo_data(train_data_path)
    eval_dataset = load_dpo_data(eval_data_path)

    training_args = DPOConfig(
        output_dir="Qwen2-0.5B-DPO_ v0.0", 
        logging_steps=1,
        eval_strategy="steps",
        eval_steps=10,
        per_device_train_batch_size=4,
        gradient_accumulation_steps= 1,
        warmup_steps= 5,
        num_train_epochs= 1,
        learning_rate= 3e-4,
        fp16= not is_bfloat16_supported(),
        bf16= is_bfloat16_supported(),
        optim= "adamw_8bit",
        weight_decay= 0.01,
        lr_scheduler_type= "linear",
        seed= 3407,
    )

    trainer = DPOTrainer(
        model=model, 
        args=training_args, 
        processing_class=tokenizer, 
        train_dataset=train_dataset,
        eval_dataset=eval_dataset
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
        "Diwanshuydv/qwen2.5-0.5B-coder-Instruct-_NL2MONGODB_DPO", # Change hf to your username!
        tokenizer,
        quantization_method = ["q4_k_m", "q8_0"],
        token = "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", # Get a token at https://huggingface.co/settings/tokens
    )

if __name__=="__main__":
    main()
