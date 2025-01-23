from openai import OpenAI
import os
from typing_extensions import List, Dict
import pandas as pd
from loguru import logger
from generate_sql_query import get_sql_query
from generate_text_query import get_text_query
from tqdm import tqdm
import argparse
from concurrent.futures import ProcessPoolExecutor
from dotenv import load_dotenv
load_dotenv()

def load_schema(schema_csv_path: str)-> List[str]:
    df = pd.read_csv(schema_csv_path)
    return df['schema'].values

def gen_single_schema_data(
        schema: str,
        args: argparse.ArgumentParser.parse_args
    ) -> List[List[str]]:
    
    # Submit tasks to executor
    with ProcessPoolExecutor() as executor:
        sql_queries_temp = [executor.submit(get_sql_query, schema, i) for i in range(1, 6)]
        
        # Use as_completed to process results as they are completed
        sql_queries_temp = [i.result() for i in tqdm(sql_queries_temp, total=5, desc="Generating SQL queries ")]


    sql_queries_temp = [item for sublist in sql_queries_temp for item in sublist]
    data = []
    logger.debug(f"len - {len(sql_queries_temp)}")

    # Submit tasks to executor for text queries
    with ProcessPoolExecutor() as executor:
        text_queires = [executor.submit(get_text_query, schema, i) for i in sql_queries_temp]
        
        # Use as_completed to process results as they are completed
        data = [i.result() for i in tqdm(text_queires, total=len(sql_queries_temp), desc="Generating text queries.")]
    
    df = pd.read_csv(args.output_csv_path)
    df_temp = pd.DataFrame(data, columns=['schema', 'sql_query', 'natural_language_query'])

    df = pd.concat([df, df_temp], ignore_index=True)
    df.to_csv(args.output_csv_path, index=False)

    return data

if __name__=="__main__":
    parser = argparse.ArgumentParser(description="Generate data for training the model.")
    parser.add_argument("--schema_csv_path", type=str, default="data/schema.csv", help="Path to the schema csv file.")
    parser.add_argument("--output_csv_path", type=str, default="data/raw_data.csv", help="Path to the output csv file.")
    args = parser.parse_args()

    if not os.path.exists(args.output_csv_path):
        df = pd.DataFrame(columns=['schema', 'sql_query', 'natural_language_query'])
        df.to_csv(args.output_csv_path, index=False)

    for schema in load_schema(args.schema_csv_path):
        gen_single_schema_data(schema, args)
