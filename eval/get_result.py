from llama_cpp import Llama
from llama_cpp.llama_grammar import LlamaGrammar
from loguru import logger
from config import (
    OUTPUT_SYS_PROMPT, 
    OUTPUT_USER_PROMPT,
    FINETUNNED_USER_PROMPT
)
from download_hf import download_model
import subprocess
import pandas as pd
import os
import argparse

def get_gguf(model_id: str) -> None:

    local_path = "models/"+model_id

    q8_name = "./ggf/" + model_id.replace('/', '_')+ "_q8_0.gguf"
    f32_name = "./ggf/" + model_id.replace('/', '_')+ "_f32.gguf"

    if os.path.exists(q8_name) and os.path.exists(f32_name):
        logger.info(f"Model already converted to gguf format")
        return q8_name, f32_name

    download_model(
        model_id=model_id,
        local_dir= local_path,
    )

    q8_cmd = f"python ./convert_hf_to_gguf.py {local_path} --outfile {q8_name} --outtype q8_0"
    f32_cmd = f"python ./convert_hf_to_gguf.py {local_path} --outfile {f32_name} --outtype f32"

    logger.info(f"Converting model to gguf format")
    subprocess.run(q8_cmd, shell=True)
    subprocess.run(f32_cmd, shell=True)

    return q8_name, f32_name    


def load_model(model_path: str) -> Llama:
    logger.info(f"Loading model from {model_path}")

    return Llama(
        model_path=model_path,
        verbose=False
        # n_gpu_layers=-1, # Uncomment to use GPU acceleration
        # seed=1337, # Uncomment to set a specific seed
        # n_ctx=2048, # Uncomment to increase the context window,
    )

def get_output(llm: Llama, grammar_path: str, schema: str, query: str) -> str:
    logger.info(f"Generating output")

    if grammar_path is not None:
        grammar = LlamaGrammar.from_file(grammar_path)
    else:
        grammar=None

    prompt = FINETUNNED_USER_PROMPT.format(
        schema=schema,
        query=query
    )

    # prompt = OUTPUT_USER_PROMPT.format(
    #                 schema=schema,
    #                 query=query
    #             )
    print(prompt)

    # return llm.create_chat_completion(
    #     messages = [
    #         {"role": "system", "content": OUTPUT_SYS_PROMPT},
    #         {
    #             "role": "user",
    #             "content": prompt
    #         }
    #     ],
    #     grammar=grammar,
    #     max_tokens=100,
    # )["choices"][0]["message"]["content"]


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
    return pd.read_csv(file_path, header=0, index_col=None)

def get_test_output(llm: Llama, grammar_path:str, data_path: str) -> pd.DataFrame:
    df = load_test_data(data_path)
    for index, row in df.iterrows():
        schema = row['schema']
        query = row['natural_language_query']

        output = get_output(llm, grammar_path, schema, query)
        logger.debug(f"Output: {output}")
        df.loc[index, 'output'] = output
    return df

def calculate_model_result(model_id: str, grammar_path: str, data_path: str) -> None:
    q8, f32 = get_gguf(model_id)
    model_name = model_id.replace('/', '_')
    q8_output_path = f"./output/{model_name}_q8_output.csv"
    f32_output_path = f"./output/{model_name}_f32_output.csv"

    logger.info(f"Calculating result for model {model_id}")

    logger.info(f"Loading model for q8")
    llm = load_model(q8)
    logger.info(f"Generating output for q8")
    output = get_test_output(llm, grammar_path, data_path)
    output.to_csv(q8_output_path, index=False)
    logger.info(f"Output saved to {q8_output_path}")

    logger.info(f"Loading model for f32")
    llm = load_model(f32)
    logger.info(f"Generating output for f32")
    output = get_test_output(llm, grammar_path, data_path)
    output.to_csv(f32_output_path, index=False)
    logger.info(f"Output saved to {f32_output_path}")


if __name__=="__main__":

    parser = argparse.ArgumentParser(description='Calculate result for a model')
    parser.add_argument('--model_id', type=str, help='Model ID', required=True)
    parser.add_argument('--grammar', type=str, help='Grammar file', default=None)
    parser.add_argument('--data_path', type=str, help='Data file path', required=True)
    parser.add_argument('--is_gguf', type=bool, help='is model_id a gguf path', default=False)
    parser.add_argument('--output_path', type=str, help='Output file path', default=None) 
    args = parser.parse_args()

    if args.is_gguf is not False:
        llm = load_model(args.model_id)
        output = get_test_output(llm, args.grammar, args.data_path)
        output.to_csv(args.output_path, index=False)
    else:
        calculate_model_result(args.model_id, args.grammar, args.data_path)
