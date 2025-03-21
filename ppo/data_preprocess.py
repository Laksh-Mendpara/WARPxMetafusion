import os
import argparse
import pandas as pd
import datasets
import json
from verl.utils.hdfs_io import copy, makedirs
from config.prompt_config import MODEL_PROMPT, SYSTEM_PROMPT


def process_row(example, idx, data_source, split):
    """
    Convert each row into the required conversational and metadata format.
    """
    schema = example.pop("schema")
    nl_query = example.pop("natural_language_query")
    mongo_query = example.pop("mongo_query")

    prompt = MODEL_PROMPT.format(schema=schema, natural_language_query=nl_query)

    data = {
        "data_source": data_source,
        "prompt": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
            # {"role": "assistant", "content": mongo_query}
        ],
        "ability": "query_generation",
        "reward_model": {
            "style": "rule",
            "ground_truth": mongo_query
        },
        "extra_info": {
            "split": split,
            "index": idx,
            "schema": schema,
            "natural_language_query": nl_query,
            "mongo_query": mongo_query
        }
    }
    return data


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv_file', required=True, help="Input CSV file with columns: schema, natural_language_query, mongo_query")
    parser.add_argument('--file_name', required=True)
    parser.add_argument('--hdfs_dir', default=None)
    parser.add_argument('--split', default='train', help="Dataset split name (e.g., train, test)")

    args = parser.parse_args()

    df = pd.read_csv(args.csv_file)
    dataset = datasets.Dataset.from_pandas(df)

    data_source = "local/nlp2mongo"

    dataset = dataset.map(
        lambda example, idx: process_row(example, idx, data_source, args.split),
        with_indices=True
    )

    local_dir="ppo/data_parquet"
    parquet_path = os.path.join(local_dir, args.file_name)
    dataset.to_parquet(parquet_path)
    print(f"Saved parquet to {parquet_path}")

    if args.hdfs_dir is not None:
        makedirs(args.hdfs_dir)
        copy(src=local_dir, dst=args.hdfs_dir)
