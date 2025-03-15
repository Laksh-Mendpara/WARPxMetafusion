import pandas as pd
from datasets import Dataset
from typing import List, Dict, Any
from config.prompt_config import MODEL_PROMPT, SYSTEM_PROMPT
from unsloth.chat_templates import (
    get_chat_template,
    standardize_sharegpt
)
from loguru import logger

def load_data_from_csv(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    df["prompt"] = df.apply(
        lambda x: MODEL_PROMPT.format(
            schema=x["schema"],
            natural_language_query=x["natural_language_query"]
        ), axis=1
    )
    df = df.sample(frac=1).reset_index(drop=True)
    return df

def get_data_in_req_format(df: pd.DataFrame) -> Dataset:
    conversation = df.apply(lambda row: [
        {'from': 'human', 'value': row['prompt']},
        {'from': 'gpt', 'value': row['mongo_query']}
    ], axis=1).tolist()
    return Dataset.from_dict({"conversations": conversation})

def convert_to_chat_template(dataset: Dataset, tokenizer: Any):
    dataset = standardize_sharegpt(dataset)
    tokenizer = get_chat_template(
        tokenizer,
        chat_template = "qwen-2.5",
        system_message = SYSTEM_PROMPT
    )
    def formatting_prompts_func(examples):
        convos = examples["conversations"]
        texts = [tokenizer.apply_chat_template(convo, tokenize = False, add_generation_prompt = False) for convo in convos]
        return {"text" : texts}
    dataset = dataset.map(formatting_prompts_func, batched = True,)
    return dataset

def get_data(file_path: str, tokenizer: Any) -> Dataset:
    df = load_data_from_csv(file_path)
    dataset = get_data_in_req_format(df)
    dataset = convert_to_chat_template(dataset, tokenizer)
    return dataset
