from .config import (
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
import json


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
        # logger.info(f"LLM response: {result}")
        result = json.loads(result)

        is_correct = result.get("is_correct")
        reason_for_fail = result.get("reason_for_fail")
        
        return int(is_correct), reason_for_fail
    except Exception as e:
        logger.error(f"Error during LLM evaluation: {e}")
        return 0, "LLM error"

def eval_csv(file_path: str, eval_report_prefix: str = None, eval_dir: str = None, output_path: str = None) -> float:
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
            executor.submit(eval_single_response, row["mongo_query"], row["reconstructed_query"], row["schema"]): index
            for index, row in df.iterrows()
        }

        for future in tqdm(as_completed(future_to_query), total=len(df), desc="Evaluating responses"):
            try:
                results.append(future.result())
            except Exception as e:
                logger.error(f"Error processing a query: {e}")
                results.append(0)  # Default to 0 if error occurs

    # accuracy = sum(results) / len(results) if results else 0
    # return accuracy
    correct_count = sum(1 for result in results if result[0] == 1)
    total_count = len(results)
    accuracy = correct_count / total_count if total_count > 0 else 0
    logger.info(f"Accuracy: {accuracy:.2%} ({correct_count}/{total_count})")
    if output_path is not None:
        logger.info(f"Saving results to {output_path}")
        df.to_csv(output_path, index=False)
    if eval_report_prefix is not None:
        # report path = eval_report/"input_file_name"+"_eval_report_prefice.csv" 
        input_file_name = os.path.basename(file_path).split(".")[0]
        output_file_name = f"{input_file_name}_eval_report_{eval_report_prefix}.csv"
        output_file_path = os.path.join(eval_dir, output_file_name)
        df = pd.DataFrame(results, columns=["is_correct", "reason_for_fail"])
        df.to_csv(output_file_path, index=False)
    return accuracy

def run_all_eval(dir_path: str, eval_report_prefix: str = None, eval_dir: str = None) -> None:
    res = {}
    for (dpath, _, files) in walk(dir_path):
        for fname in files:
            fpath = os.path.join(dpath, fname)
            print (fpath)
            ac = eval_csv(fpath, eval_report_prefix, eval_dir)
            res[fpath] = ac
    return res


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', required=True, help="path of response csv directory")
    parser.add_argument('--is_single', default=False, help="path of response csv directory")
    parser.add_argument('--output_path', default=None, help="output path of response csv directory")
    parser.add_argument('--eval_dir', default=None, help="eval report dir name")
    parser.add_argument('--eval_report_prefix', default=None, help="prefix of eval report")

    args = parser.parse_args()

    ## if one of eval_dir and eval_report_prefix is None give error
    if (args.eval_dir is None) != (args.eval_report_prefix is None):
        raise ValueError("give both value of eval_dir and prefix")
    
    if (args.eval_dir is None) != (args.eval_report_prefix is None):
        raise ValueError("give both value of eval_dir and prefix")

    # csv_path = "output/microsoft_phi-2_q8_output.csv"
    if not args.is_single:
        result = run_all_eval(args.path, args.eval_report_prefix, args.eval_dir)
        # logger.info(f"Accuracy: {result}")
        for (k, v) in result.items():
            print (f"{k}  -- {v}")
    else:
        acc = eval_csv(args.path, args.eval_report_prefix, args.eval_dir, args.output_path)
        print (f"Accuracy: {acc}")
