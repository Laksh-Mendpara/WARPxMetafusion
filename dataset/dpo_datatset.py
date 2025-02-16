from openai import OpenAI
import os
from typing_extensions import List, Dict
import pandas as pd
from loguru import logger
from error_gen import (
    schema_linking_error,
    logical_error,
    incomplete_query,
    syntax_error,
    inefficient_query,
    ambiguous_query
)
from tqdm import tqdm
import argparse
from concurrent.futures import ProcessPoolExecutor
from dotenv import load_dotenv
import time
load_dotenv()

def get_final_data(data_path: str, output_path: str) -> None:
    logger.debug(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)
    
    # type of error and its percentage
    error = {
        "schema_linking_error": 0.35,
        "logical_error": 0.25,
        "incomplete_query": 0.15,
        "syntax_error": 0.1,
        "inefficient_query": 0.1,
        "ambiguous_query": 0.05
    }
    logger.debug(f"Generating data with error distribution: {error}")

    # shuffle_df
    df = df.sample(frac=1).reset_index(drop=True)

    # get number of row for each type of error
    num_rows = {k: int(v * len(df)) for k, v in error.items()}

    # get start index for each type of error
    start_index = []
    for i in range(len(num_rows)):
        start_index.append(sum(list(num_rows.values())[:i]))
    
    final_data = []
    # get schema_link error
    logger.debug(f"Generating schema linking error.")
    with ProcessPoolExecutor() as executor:
        df_temp = df.iloc[start_index[0]:start_index[0]+num_rows['schema_linking_error']]
        result_raw = [
            executor.submit(
                schema_linking_error, 
                row['schema'], 
                row['natural_language_query'], 
                row['mongo_query']
                ) for _, row in df_temp.iterrows()
            ]
        result = [i.result() for i in tqdm(result_raw, total=len(df_temp), desc="Generating schema linking error.")]
        final_data.extend(result)
    
    # get logical error
    logger.debug(f"Generating logical error.")
    with ProcessPoolExecutor() as executor:
        df_temp = df.iloc[start_index[1]:start_index[1]+num_rows['logical_error']]
        result_raw = [
            executor.submit(
                logical_error, 
                row['schema'], 
                row['natural_language_query'], 
                row['mongo_query']
                ) for _, row in df_temp.iterrows()
            ]
        result = [i.result() for i in tqdm(result_raw, total=len(df_temp), desc="Generating logical error.")]
        final_data.extend(result)

    # get incomplete query
    logger.debug(f"Generating incomplete query.")
    with ProcessPoolExecutor() as executor:
        df_temp = df.iloc[start_index[2]:start_index[2]+num_rows['incomplete_query']]
        result_raw = [
            executor.submit(
                incomplete_query, 
                row['schema'], 
                row['natural_language_query'], 
                row['mongo_query']
                ) for _, row in df_temp.iterrows()
            ]
        result = [i.result() for i in tqdm(result_raw, total=len(df_temp), desc="Generating incomplete query.")]
        final_data.extend(result)

    # get syntax error
    logger.debug(f"Generating syntax error.")
    with ProcessPoolExecutor() as executor:
        df_temp = df.iloc[start_index[3]:start_index[3]+num_rows['syntax_error']]
        result_raw = [
            executor.submit(
                syntax_error, 
                row['schema'], 
                row['natural_language_query'], 
                row['mongo_query']
                ) for _, row in df_temp.iterrows()
            ]
        result = [i.result() for i in tqdm(result_raw, total=len(df_temp), desc="Generating syntax error.")]
        final_data.extend(result)

    # get inefficient query
    logger.debug(f"Generating inefficient query.")
    with ProcessPoolExecutor() as executor:
        df_temp = df.iloc[start_index[4]:start_index[4]+num_rows['inefficient_query']]
        result_raw = [
            executor.submit(
                inefficient_query, 
                row['schema'], 
                row['natural_language_query'], 
                row['mongo_query']
                ) for _, row in df_temp.iterrows()
            ]
        result = [i.result() for i in tqdm(result_raw, total=len(df_temp), desc="Generating inefficient query.")]
        final_data.extend(result)

    # get ambiguous query
    logger.debug(f"Generating ambiguous query.")
    with ProcessPoolExecutor() as executor:
        df_temp = df.iloc[start_index[5]:start_index[5]+num_rows['ambiguous_query']]
        result_raw = [
            executor.submit(
                ambiguous_query, 
                row['schema'], 
                row['natural_language_query'], 
                row['mongo_query']
                ) for _, row in df_temp.iterrows()
            ]
        result = [i.result() for i in tqdm(result_raw, total=len(df_temp), desc="Generating ambiguous query.")]
        final_data.extend(result)

    ## convert to df
    logger.debug(f"Converting data to DataFrame.")
    final_df = pd.DataFrame(
        final_data, 
        columns=[
            'schema', 
            'natural_language_query', 
            'corret_mongo_query', 
            'incorrect_mongo_query'
            ]
        )
    # log csv detail
    logger.debug(f"Final data shape: {final_df.shape}")
    logger.debug(f"Final data head: {final_df.head()}")
    
    # save to csv
    logger.debug(f"Saving data at {output_path}")
    final_df.to_csv(output_path, index=False)
    return final_df


def main():
    parser = argparse.ArgumentParser(description="Generate data for training the model.")
    parser.add_argument("--data_path", type=str, default="data/data.csv", help="Path to the schema csv file.")
    parser.add_argument("--output_path", type=str, default="data/dpo_data.csv", help="Path to the output csv file.")
    args = parser.parse_args()

    if not os.path.exists(args.output_path):
        df = pd.DataFrame(
            columns=[
                'database_id', 
                'schema', 
                'natural_language_query', 
                'corret_mongo_query', 
                'incorrect_mongo_query'
            ]
        )
        df.to_csv(args.output_path, index=False)
    
    output = get_final_data(args.data_path, args.output_path)
    logger.debug(f"Final data generated and saved at {args.output_path}")

if __name__=="__main__":
    main()
