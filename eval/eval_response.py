from config import (
    CHECK_SYS_PROMPT,
    CHECK_USER_PROMPT
)
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from loguru import logger
import pandas as pd
from tqdm import tqdm
import argparse
from os import walk
import os

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def eval_single_response(query1: str, query2: str, schema: str) -> int:
    """
    Evaluates two MongoDB queries against a given database schema
    and determines if they will return the same result.

    Returns:
    - 1 if both queries retrieve the same result.
    - 0 if either query is incorrect or both return no result.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": CHECK_SYS_PROMPT},
                {"role": "user", "content": CHECK_USER_PROMPT.format(
                    schema=schema, query_1=query1, query_2=query2
                )}
            ],
            temperature=0
        )

        result = response.choices[0].message.content.strip()
        
        if result in {"0", "1"}:
            return int(result)
        else:
            logger.error(f"Unexpected response: {result}")
            return 0
    except Exception as e:
        logger.error(f"Error during LLM evaluation: {e}")
        return 0

def eval_csv(file_path: str):
    """
    Evaluates responses in a CSV file containing MongoDB queries and schemas.

    Returns:
    - Accuracy score (fraction of correct matches).
    """
    logger.info(f"Evaluating responses in {file_path}")
    
    df = pd.read_csv(file_path)
    logger.info(f"Loaded {len(df)} rows from CSV")

    results = []
    
    with ThreadPoolExecutor() as executor:
        future_to_query = {
            executor.submit(eval_single_response, row["mongo_query"], row["output"], row["schema"]): index
            for index, row in df.iterrows()
        }

        for future in tqdm(as_completed(future_to_query), total=len(df), desc="Evaluating responses"):
            try:
                results.append(future.result())
            except Exception as e:
                logger.error(f"Error processing a query: {e}")
                results.append(0)  # Default to 0 if error occurs

    accuracy = sum(results) / len(results) if results else 0
    return accuracy

def run_all_eval(dir_path: str) -> None:
    res = {}
    for (dpath, _, files) in walk(dir_path):
        for fname in files:
            fpath = os.path.join(dpath, fname)
            print (fpath)
            ac = eval_csv(fpath)
            res[fpath] = ac
    return res


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', required=True, help="path of response csv directory")
    parser.add_argument('--is_single', default=False, help="path of response csv directory")
    args = parser.parse_args()
    # csv_path = "output/microsoft_phi-2_q8_output.csv"
    if not args.is_single:
        result = run_all_eval(args.path)
        # logger.info(f"Accuracy: {result}")
        for (k, v) in result.items():
            print (f"{k}  -- {v}")
    else:
        acc = eval_csv(args.path)
        print (f"Accuracy: {acc}")
