import os
import re
import json
import random
import argparse
import time
from collections import Counter
from typing import Dict, Tuple, List
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from dotenv import load_dotenv
from loguru import logger
from tqdm import tqdm
from openai import OpenAI

from .config_v3 import (
    Model,
    SCHEMA_NL_GEN_SYS_PROMPT,
    SCHEMA_NL_GEN_USER_PROMPT,
    MONGO_GEN_SYS_PROMPT,
    MONGO_GEN_USER_PROMPT
)
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def clean_response(response: str) -> str:
    # Precompiled regex for cleaning responses
    CLEAN_REGEX = re.compile(r"^(`{3}json)?|(`{3})?$")
    """Cleans OpenAI response strings."""
    return CLEAN_REGEX.sub("", response).strip()

def get_mongo_query(schema: str, nl_query: str, additional_info: str) -> Tuple[str, str, str, str]:
    """Generates a MongoDB query from a natural language query using OpenAI."""
    try:
        response = client.chat.completions.create(
            model=Model,
            messages=[
                {"role": "system", "content": MONGO_GEN_SYS_PROMPT},
                {"role": "user", "content": MONGO_GEN_USER_PROMPT.format(
                    schema=schema, 
                    nl_query=nl_query,
                    additional_info=additional_info
                    )
                }
            ],
            temperature=0.2,
            top_p=0.8
        ).choices[0].message.content
        response = json.loads(clean_response(response))
        generated_query = response["mongodb_query"]
        return schema, generated_query, nl_query, additional_info
    except Exception as e:
        logger.error(f"Error generating MongoDB query: {e}")
        return None, None, None, None  # Return None if an error occurs

def generate_batch_schema_NL(predefined_schemas: List[str], probas: List[float]) -> Tuple[str, List[Dict[str, str]]]:
    """Generates a batch of natural language queries and their corresponding schemas."""
    # select 2 random schemas from the list
    # selected_schemas = random.sample(predefined_schemas, 2)
    selected_schemas = random.choices(predefined_schemas, weights=probas, k=1)

    for _ in range(3):  # Retry mechanism instead of recursion       
        try:
            response = client.chat.completions.create(
                model=Model,
                messages=[
                    {"role": "system", "content": SCHEMA_NL_GEN_SYS_PROMPT},
                    {
                        "role": "user", 
                        "content": SCHEMA_NL_GEN_USER_PROMPT.format(
                            schema=selected_schemas[0],
                        )
                    }
                ],
                temperature=1.3,
                top_p=0.95,
            ).choices[0].message.content

            response = json.loads(clean_response(response))
            schema, nl_queries = response["schema"], response["nl_queries"]
            schema = json.dumps(schema)
            return schema, nl_queries
        except Exception as e:
            logger.warning(f"Error generating schema, retrying... {e}")
            time.sleep(2)  # Small delay before retrying

    logger.error("Failed to generate schema after retries.")
    return None, None  # Return None if all attempts fail

def get_one_batch(data_path: str, predefined_schemas: List[str], probas: List[float]) -> List[Tuple[str, str, str]]:
    """Processes one batch of natural language queries into MongoDB queries."""
    schema, nl_queries = generate_batch_schema_NL(predefined_schemas=predefined_schemas, probas=probas)
    if not nl_queries or not schema:
        return []  # Avoid processing if we failed to generate queries

    results = []
    with ThreadPoolExecutor() as executor:
        future_to_query = {executor.submit(get_mongo_query, schema, q["query"], q["additional_info"]): q for q in nl_queries}
        for future in as_completed(future_to_query):
            results.append(future.result())

    # Remove None results
    results = [result for result in results if result and all(result)]

    # Append results to CSV without reloading full dataset
    df_temp = pd.DataFrame(results, columns=["schema", "mongo_query", "natural_language_query", "additional_info"])
    df_temp.to_csv(data_path, mode='a', index=False, header=False)

    return results

def run_all_batch(data_path: str, total_batch: int) -> None:
    """Runs multiple batches of data generation."""
    predefined_schemas_df1 = pd.read_csv("./data/schema.csv")
    predefined_schemas_df2 = pd.read_csv("./data/schema2.csv")
    predefined_schemas_df = pd.concat([predefined_schemas_df1, predefined_schemas_df2], ignore_index=True)
    predefined_schemas = predefined_schemas_df['schema'].unique().tolist()
    valid_schemas = []
    for i, s in enumerate(predefined_schemas):
        try:
            parsed_schemas = json.loads(s)
            # Check for latitude and longitude in the schema
            if 'latitude' in s or 'longitude' in s:
                logger.warning(f"Schema contains latitude or longitude at index {i}")
                continue
            valid_schemas.append(json.dumps(parsed_schemas))
        except json.JSONDecodeError:
            logger.warning(f"Invalid schema at index {i}")
            continue
    logger.debug(f"Total valid schemas: {len(valid_schemas)}")

    # Step 1: Extract collection names (assuming valid_schemas is list of JSON strings)
    collection_names = [json.loads(s)["collections"][0]["name"] for s in valid_schemas]

    # Step 2: Split each collection_name into tokens
    tokens_for_each_schema = [name.split('_')[0] for name in collection_names]

    # Step 3: Count in how many schemas each token appears (document frequency)
    token_doc_freq = Counter()
    for token in tokens_for_each_schema:
        token_doc_freq[token] += 1

    # Optional: smoothing constant to avoid div by zero
    SMOOTHING = 0

    # Step 4: Calculate schema scores based on token rarity
    schema_scores = []
    for token in tokens_for_each_schema:
        df = token_doc_freq[token]
        # Token score: rarer tokens get higher scores
        token_score = 1 / (df + SMOOTHING)
        schema_scores.append(token_score)

    # Step 5: Normalize schema scores to get probabilities
    total_score = sum(schema_scores)
    if total_score > 0:
        probas = [score / total_score for score in schema_scores]
    else:
        probas = [0] * len(schema_scores)

    # print final collection names and their probabilities
    for name, prob in zip(collection_names, probas):
        logger.info(f"predefined collection name: {name}, probability: {prob:.3f}")
    
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(get_one_batch, data_path, valid_schemas, probas) for _ in range(total_batch)]
        for _ in tqdm(as_completed(futures), total=total_batch, desc="Processing batches"):
            pass  # No need to collect results, as they are already saved

def main():
    parser = argparse.ArgumentParser(description="Generate dataset for training.")
    parser.add_argument("--output_path", type=str, required=True, help="Path of output CSV.")
    parser.add_argument("--total_batch", type=int, required=True, help="Total batches, each containing 20 datapoints.")
    args = parser.parse_args()

    # Ensure output file exists
    if not os.path.exists(args.output_path):
        pd.DataFrame(columns=["schema", "mongo_query", "natural_language_query", "additional_info"]).to_csv(args.output_path, index=False)

    run_all_batch(args.output_path, args.total_batch)
    logger.info(f"Data saved to {args.output_path}")

if __name__ == "__main__":
    main()
