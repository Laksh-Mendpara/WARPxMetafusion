from openai import OpenAI
import os
import pandas as pd
import json
import argparse
import time
import re
from dotenv import load_dotenv
from loguru import logger
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Tuple, List
from config_v2 import (
    Model,
    SCHEMA_NL_GEN_SYS_PROMPT,
    SCHEMA_NL_GEN_USER_PROMPT,
    MONGO_GEN_SYS_PROMPT,
    MONGO_GEN_USER_PROMPT
)
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Precompiled regex for cleaning responses
CLEAN_REGEX = re.compile(r"^(`{3}json)?|(`{3})?$")

def clean_response(response: str) -> str:
    """Cleans OpenAI response strings."""
    return CLEAN_REGEX.sub("", response).strip()

def get_mongo_query(schema: Dict, nl_query: str) -> Tuple[str, str, str]:
    """Generates a MongoDB query from a natural language query using OpenAI."""
    try:
        response = client.chat.completions.create(
            model=Model,
            messages=[
                {"role": "system", "content": MONGO_GEN_SYS_PROMPT},
                {"role": "user", "content": MONGO_GEN_USER_PROMPT.format(schema=str(schema), nl_query=str(nl_query))}
            ],
            temperature=0.2,
            top_p=0.8
        ).choices[0].message.content
        return schema, clean_response(response), nl_query
    except Exception as e:
        logger.error(f"Error generating MongoDB query: {e}")
        return schema, "", nl_query

def generate_batch_schema_NL() -> Tuple[str, List[str]]:
    """Generates a batch of natural language queries and their corresponding schemas."""
    for _ in range(3):  # Retry mechanism instead of recursion
        try:
            response = client.chat.completions.create(
                model=Model,
                messages=[
                    {"role": "system", "content": SCHEMA_NL_GEN_SYS_PROMPT},
                    {"role": "user", "content": SCHEMA_NL_GEN_USER_PROMPT}
                ],
                temperature=1.3,
                top_p=0.9
            ).choices[0].message.content

            response = json.loads(clean_response(response))
            schema, nl_queries = response["schema"], response["nl_queries"]
            schema = json.dumps(schema)
            logger.debug(f"Generated {len(nl_queries)} queries.")
            return schema, nl_queries
        except Exception as e:
            logger.warning(f"Error generating schema, retrying... {e}")
            time.sleep(2)  # Small delay before retrying

    logger.error("Failed to generate schema after retries.")
    return "", []  # Return empty data instead of retrying indefinitely

def get_one_batch(data_path: str) -> List[Tuple[str, str, str]]:
    """Processes one batch of natural language queries into MongoDB queries."""
    schema, nl_queries = generate_batch_schema_NL()
    if not nl_queries:
        return []  # Avoid processing if we failed to generate queries

    results = []
    with ThreadPoolExecutor() as executor:
        future_to_query = {executor.submit(get_mongo_query, schema, q): q for q in nl_queries}
        for future in as_completed(future_to_query):
            results.append(future.result())

    # Append results to CSV without reloading full dataset
    df_temp = pd.DataFrame(results, columns=["schema", "mongo_query", "natural_language_query"])
    df_temp.to_csv(data_path, mode='a', header=not os.path.exists(data_path), index=False)

    return results

def run_all_batch(data_path: str, total_batch: int) -> None:
    """Runs multiple batches of data generation."""
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(get_one_batch, data_path) for _ in range(total_batch)]
        for _ in tqdm(as_completed(futures), total=total_batch, desc="Processing batches"):
            pass  # No need to collect results, as they are already saved

def main():
    parser = argparse.ArgumentParser(description="Generate dataset for training.")
    parser.add_argument("--output_path", type=str, required=True, help="Path of output CSV.")
    parser.add_argument("--total_batch", type=int, required=True, help="Total batches, each containing 10 datapoints.")
    args = parser.parse_args()

    # Ensure output file exists
    if not os.path.exists(args.output_path):
        pd.DataFrame(columns=["schema", "mongo_query", "natural_language_query"]).to_csv(args.output_path, index=False)

    run_all_batch(args.output_path, args.total_batch)
    logger.info(f"Data saved to {args.output_path}")

if __name__ == "__main__":
    main()
