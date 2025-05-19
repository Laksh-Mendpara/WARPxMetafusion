import pandas as pd
from datasets import Dataset
from typing import List, Dict, Any
from loguru import logger
from data_v3.data_utils.utils import (
    modify_dataframe as modify_dataframe_v3
)
from .config.prompt_config import (
    MODEL_PROMPT, 
    SYSTEM_PROMPT
)
from .config.prompt_config_v3 import (
    MODEL_PROMPT_V3,
    SYSTEM_PROMPT_V3
)
from unsloth.chat_templates import (
    get_chat_template,
    standardize_sharegpt
)


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

def load_data_from_csv_v3(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    modified_data = modify_dataframe_v3(df)
    df_modified = pd.DataFrame(modified_data)
    # only take key - line_based_query, line_based_schema, natural_language_query, additional_info
    df_modified = df_modified[["line_based_query", "line_based_schema", "natural_language_query", "additional_info"]]
    df_modified.rename(columns={
        "line_based_query": "mongo_query",
        "line_based_schema": "schema"
    }, inplace=True)
    df_modified["prompt"] = df_modified.apply(
        lambda x: MODEL_PROMPT_V3.format(
            schema=x["schema"],
            natural_language_query=x["natural_language_query"],
            additional_info=x["additional_info"]
        ), axis=1
    )
    df_modified = df_modified.sample(frac=1).reset_index(drop=True)
    return df_modified

def get_data_in_req_format(df: pd.DataFrame) -> Dataset:
    conversation = df.apply(lambda row: [
        {'from': 'human', 'value': row['prompt']},
        {'from': 'gpt', 'value': row['mongo_query']}
    ], axis=1).tolist()
    return Dataset.from_dict({"conversations": conversation})

def convert_to_chat_template(dataset: Dataset, tokenizer: Any, system_prompt: str) -> Dataset:
    dataset = standardize_sharegpt(dataset)
    tokenizer = get_chat_template(
        tokenizer,
        chat_template = "qwen-2.5",
        system_message = system_prompt
    )
    def formatting_prompts_func(examples):
        convos = examples["conversations"]
        texts = [tokenizer.apply_chat_template(convo, tokenize = False, add_generation_prompt = False) for convo in convos]
        return {"text" : texts}
    dataset = dataset.map(formatting_prompts_func, batched = True,)
    return dataset

def get_data(file_path: str, tokenizer: Any, approach_v3: bool) -> Dataset:
    if approach_v3:
        df = load_data_from_csv_v3(file_path)
        system_prompt = SYSTEM_PROMPT_V3
    else:
        df = load_data_from_csv(file_path)
        system_prompt = SYSTEM_PROMPT
    dataset = get_data_in_req_format(df)
    dataset = convert_to_chat_template(dataset, tokenizer, system_prompt)
    return dataset
