from openai import OpenAI
import os
from typing_extensions import List, Dict
import pandas as pd
from loguru import logger
from tqdm import tqdm
import random
import argparse
from config import(
    DATA_CHECK_SYS_PROMPT,
    DATA_CHECK_USER_PROMPT
)
from concurrent.futures import ProcessPoolExecutor
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def check_single_data(schema: str, natural_query: int, mongo_query: int) -> int:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "developer", "content": DATA_CHECK_SYS_PROMPT},
            {
                "role": "user",
                "content": DATA_CHECK_USER_PROMPT.format(
                    schema=schema,
                    natural_language_query=natural_query,
                    mongo_query=mongo_query
                )
            }
        ]
    ).choices[0].message.content
    
    try:
        return int(response)
    except ValueError:
        logger.error(f"Error in response: {response}")
        return 0


def check_data(data_path: str, sample_size: int | None) -> float:
    data = pd.read_csv(data_path)
    data = data.to_dict(orient="records")
    if sample_size is not None:
        data = random.sample(data, sample_size)
    correct_data = 0
    total_data = len(data)
    with ProcessPoolExecutor() as executor:
        result = [executor.submit(
            check_single_data, 
            d["schema"], 
            d["natural_language_query"], 
            d["mongo_query"]
            ) for d in data]
        result = [r.result() for r in tqdm(result, total=total_data, desc="Checking data correctness")]
        correct_data = sum(result)

    return correct_data/total_data


if __name__=="__main__":
    parser = argparse.ArgumentParser(description="Check generated data for training the model.")
    parser.add_argument("--data_csv_path", type=str, default="data/final_data.csv", help="Path to the data csv file.")
    parser.add_argument("--sample_size", type=int, default=None, help="Number of samples to check.")
    args = parser.parse_args()

    if not os.path.exists(args.data_csv_path):
        raise FileNotFoundError(f"File not found at {args.data_csv_path}")
    
    result = check_data(args.data_csv_path, args.sample_size)
    logger.info(f"Data correctness: {result*100:.2f}%")
