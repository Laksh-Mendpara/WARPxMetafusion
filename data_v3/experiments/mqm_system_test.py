import pandas as pd
import pytest
import re
from typing import Any, Dict
from loguru import logger
from .mqm import (
    convert_mongo_to_pymongo, 
    reconstruct_mongo_query 
)

# --------------------- UTILITY -------------------------

def clean_query(query: str) -> str:
    query = query.strip()
    if query.startswith("'''") and query.endswith("'''"):
        query = query[3:-3]

    query = query.replace("'", "\"")
    query = query.replace("\n", "").strip()
    query = query.replace("+00:00", "")
    query = query.replace("{}", "")

    parts = re.split(r'(".*?")', query)
    parts = [p if i % 2 else p.replace(" ", "") for i, p in enumerate(parts)]
    query = ''.join(parts)

    if ".find" in query and not query.startswith("db.event.find"):
        parts = query.split(".find", 1)
        query = "db.event.find" + parts[1]

    def quote_keys_in_dict(match):
        content = match.group(1)
        content = re.sub(r'(?<!["])(\b[a-zA-Z_][a-zA-Z0-9_.]*\b)(?=\s*:)', r'"\1"', content)
        return f'{{{content}}}'

    query = re.sub(r'\{([^{}]*)\}', quote_keys_in_dict, query)
    query = query.replace("\\\"", "\"")
    query = re.sub(r'0(?=[,}])', '', query)

    if query.endswith(".toArray()"):
        query = query[:-11]

    if "find(" in query:
        open_count = query.count("(")
        close_count = query.count(")")
        if open_count > close_count:
            query += ")" * (open_count - close_count)

    return query

# --------------------- CORE TEST -------------------------

def check_single_query(mongo_query: str, schema: Dict[str, Any]):
    mongo_query = clean_query(mongo_query)
    modified_dict = convert_mongo_to_pymongo(mongo_query)
    converted_query = reconstruct_mongo_query(modified_dict)
    converted_query = clean_query(converted_query)

    if converted_query != mongo_query:
        logger.error(f"Converted query does not match the original query.\nOriginal: {mongo_query}\nConverted: {converted_query}")
        diff = set(mongo_query.split()).symmetric_difference(set(converted_query.split()))
        logger.error(f"Difference: {diff}")
        raise AssertionError(f"Mismatch between original and converted query.\nOriginal: {mongo_query}\nConverted: {converted_query}")
    
    return modified_dict, converted_query

# --------------------- TEST DATA -------------------------

def load_test_data():
    csv_path = "./data_v3/data_v1.csv"
    df = pd.read_csv(csv_path)
    mongo_queries = df["mongo_query"].tolist()
    schemas = df["schema"].apply(eval).tolist()

    # Remove failing/irrelevant indices
    # indices_to_remove = [14, 58, 433, 972, 1152, 1189, 1788, 1906]
    indices_to_remove = []
    filtered_data = [
        (clean_query(mongo_queries[i]), schemas[i])
        for i in range(len(mongo_queries))
        if i not in indices_to_remove
    ]
    return filtered_data

# --------------------- PYTEST -------------------------

@pytest.mark.parametrize("mongo_query,schema", load_test_data())
def test_query_conversion(mongo_query, schema):
    check_single_query(mongo_query, schema)
