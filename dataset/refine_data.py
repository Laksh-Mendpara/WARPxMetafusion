from openai import OpenAI
import os
from typing_extensions import List, Dict
import pandas as pd
from loguru import logger
from tqdm import tqdm
import json
import argparse
from config import(
    DATA_REFINE_SYS_PROMPT,
    DATA_REFINE_USER_PROMPT,
)
from concurrent.futures import ProcessPoolExecutor
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def refine_single_data(database_id: str, schema: str, natural_query: int, mongo_query: int) -> int:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "developer", "content": DATA_REFINE_SYS_PROMPT},
            {
                "role": "user",
                "content": DATA_REFINE_USER_PROMPT.format(
                    schema=schema,
                    natural_language_query=natural_query,
                    mongo_query=mongo_query
                )
            }
        ]
    ).choices[0].message.content
    
    try:
        response = json.loads(response)
        return (
            database_id,
            schema, 
            response['adjusted_mongo_query'], 
            response['adjusted_natural_language_query']
        )
    except Exception as e:
        logger.error(f"Error in refining data: {e}")
        return (database_id, schema, mongo_query, natural_query)


def refine_data(data_path: str, outupt_data_path:str) -> pd.DataFrame:
    data = pd.read_csv(data_path)
    logger.warning(f"{data.columns}")
    data = data.to_dict(orient="records")
    
    with ProcessPoolExecutor() as executor:
        result = [executor.submit(
            refine_single_data, 
            d["database_id"],
            d["schema"], 
            d["natural_language_query"], 
            d["mongo_query"]
            ) for d in data]
        result = [r.result() for r in tqdm(result, total=len(data), desc="Refining data")]

    result = pd.DataFrame(result)
    result.columns = ["database_id", "schema", "mongo_query", "natural_language_query"]
    result.to_csv(outupt_data_path, index=False)
    return result

if __name__=="__main__":
    parser = argparse.ArgumentParser(description="Check generated data for training the model.")
    parser.add_argument("--data_csv_path", type=str, default="data/raw_data.csv", help="Path to the data csv file.")
    parser.add_argument("--output_data_csv_path", type=str, default="data/final_data.csv", help="Path to save the refined data.")
    args = parser.parse_args()

    if not os.path.exists(args.data_csv_path):
        raise FileNotFoundError(f"File not found at {args.data_csv_path}")
    
    result = refine_data(args.data_csv_path, args.output_data_csv_path)
    