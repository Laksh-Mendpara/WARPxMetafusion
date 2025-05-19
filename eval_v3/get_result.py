from llama_cpp import Llama
from llama_cpp.llama_grammar import LlamaGrammar
from typing import Dict, List, Any
from loguru import logger
from data_v3.data_utils.utils import (
    modify_dataframe as modify_dataframe_v3
)
from data_v3.data_utils.line_based_parsing import (
    parse_line_based_query
)
from data_v3.data_utils.base_conversion_utils import (
    build_schema_maps,
    convert_modified_to_actual_code_string
)
from sft.config.prompt_config_v3 import (
    SYSTEM_PROMPT_V3,
    MODEL_PROMPT_V3
)
from tqdm import tqdm
import pandas as pd
import argparse


def load_model(model_path: str) -> Llama:
    logger.info(f"Loading model from {model_path}")

    return Llama(
        model_path=model_path,
        verbose=False,
        # n_gpu_layers=-1, # Uncomment to use GPU acceleration
        # seed=1337, # Uncomment to set a specific seed
        n_ctx=1024, # Uncomment to increase the context window,
    )

def get_output(llm: Llama, grammar_path: str, query_data: Dict[str, Any]) -> str:
    logger.info(f"Generating output")

    if grammar_path is not None:
        grammar = LlamaGrammar.from_file(grammar_path)
    else:
        grammar=None

    prompt = MODEL_PROMPT_V3.format(
        schema=query_data["line_based_schema"],
        natural_language_query=query_data["natural_language_query"],
        additional_info=query_data["additional_info"],
    )


    return llm.create_chat_completion(
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ],
        grammar=grammar,
        max_tokens=100,
    )["choices"][0]["message"]["content"]

def load_test_data(file_path: str) -> list:
    df = pd.read_csv(file_path)
    modified_data = modify_dataframe_v3(df)
    return modified_data

def get_test_output(llm: Llama, grammar_path:str, data_path: str) -> pd.DataFrame:
    data = load_test_data(data_path)
    for index, query_data in tqdm(enumerate(data), desc="Generating Outputs", total=len(data)):
        output = get_output(llm, grammar_path, query_data)
        logger.debug(f"Output: {output}")
        data[index]['output'] = output
    return data

def convert_line_parsed_to_mongo(line_parsed: str, schema: Dict[str, Any]) -> str:
    try:
        modified_query = parse_line_based_query(line_parsed)
        collection_name = schema["collections"][0]["name"]
        in2out, _ = build_schema_maps(schema)
        reconstructed_query = convert_modified_to_actual_code_string(modified_query, in2out, collection_name)
        return reconstructed_query
    except Exception as e:
        logger.error(f"Error converting line parsed to MongoDB query: {e}")
        return ""

def reconstruct_original_query(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for index, query_data in tqdm(enumerate(data), desc="Reconstructing Original Queries", total=len(data)):
        line_parsed = query_data["output"]
        schema = query_data["schema"]
        reconstructed_query = convert_line_parsed_to_mongo(line_parsed, schema)
        data[index]["reconstructed_query"] = reconstructed_query
    return data

if __name__=="__main__":

    parser = argparse.ArgumentParser(description='Calculate result for a model')
    parser.add_argument('--model_path', type=str, help='Path of GGUF Model', required=True)
    parser.add_argument('--grammar', type=str, help='Grammar file', default=None)
    parser.add_argument('--data_path', type=str, help='Data file path', required=True)
    parser.add_argument('--output_path', type=str, help='Output file path', required=True) 
    args = parser.parse_args()

    llm = load_model(args.model_path)
    output = get_test_output(llm, args.grammar, args.data_path)
    output = reconstruct_original_query(output)
    df = pd.DataFrame(output)
    logger.info(f"Columns: {df.columns}")
    logger.info(f"Output: {df.head()}")
    df.to_csv(args.output_path, index=False)