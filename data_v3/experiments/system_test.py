import pandas as pd
from typing_extensions import Any, List, Dict
from tqdm import tqdm
import json
import re
from loguru import logger
from .utils import (
    convert_actual_code_to_modified_dict,
    convert_modified_to_actual_code_string,
    build_schema_maps   
)

def clean_query(query: str) -> str:
    """
    Cleans the MongoDB query string by removing unnecessary whitespace and formatting.

    to do:
    - replace ' with "
    - remove all spaces
    - strip the query
    - convert '''<query>''' to <query>
    - remove \n
    - remove empty brackets {}
    """
    # replace \' with "
    query = query.replace("'", "\"")
    # Remove all spaces
    query = query.replace(" ", "")
    # Strip the query
    query = query.strip()
    # Convert '''<query>''' to <query>
    if query.startswith("'''") and query.endswith("'''"):
        query = query[3:-3]
    # Remove \n
    query = query.replace("\n", "")
    # Remove empty brackets {}
    query = query.replace("{}", "")
    # Replace .toArray() with ""
    query = query.replace(".toArray()", "")
    return query


def clean_query2(query_str: str) -> str:
    """
    Normalize numeric literals in a MongoDB query string by stripping unnecessary trailing zeros
    from floating-point numbers without modifying the overall structure of the query.
    """
    # Regex to find float literals (e.g., 40.712800, -74.0060)
    def normalize_number(match):
        num_str = match.group(0)
        if '.' in num_str:
            # Normalize float by removing trailing zeros and decimal point if needed
            return str(float(num_str))
        return num_str  # Leave integers as is

    # Match numbers (float or int) not enclosed in quotes
    return re.sub(r'(?<!["\w])(-?\d+\.\d+)(?!["\w])', normalize_number, query_str)


def test_single_row(mongo_query: str, schema: Dict[str, Any]):
    try:
        mongo_query = clean_query(mongo_query)
        mongo_query = clean_query2(mongo_query)
        in2out, out2in = build_schema_maps(schema)
        # Convert the actual MongoDB query to a modified flat dictionary
        modified_dict = convert_actual_code_to_modified_dict(mongo_query, out2in)
        # Convert the modified flat dictionary back to an actual MongoDB query string
        collection_name = schema["collections"][0]["name"]
        converted_query = convert_modified_to_actual_code_string(modified_dict, in2out, collection_name)
        # Check if the converted query matches the original query
        # clean the converted query
        converted_query = clean_query(converted_query)
        converted_query = clean_query2(converted_query)
        # assert converted_query == mongo_query, f"Converted query does not match the original query.\nOriginal: {mongo_query}\nConverted: {converted_query}"
        if converted_query != mongo_query:
            logger.error(f"Converted query does not match the original query.\nOriginal: {mongo_query}\nModified: {modified_dict}\n Reconstructed: {converted_query}")
            # raise AssertionError(f"Converted query does not match the original query.\nOriginal: {mongo_query}\nConverted: {converted_query}")
            return None, None, None, None
        return mongo_query, modified_dict, in2out, out2in
    except ValueError as e:
        logger.error(f"ValueError: {e}")
        logger.debug(f"Mongo query: {mongo_query}")
        return None, None, None, None
    except KeyError as e:
        logger.error(f"KeyError: {e}")
        logger.debug(f"Mongo query: {mongo_query}")
        return None, None, None, None
        

def test_all_rows(mongo_queries: List[str], schemas: Dict[str, Any]):
    final_data = []
    for i, (mongo_query, schema) in tqdm(enumerate(zip(mongo_queries, schemas)), desc="Testing all rows", total=len(mongo_queries)):
        mongo_query, converted_query, in2out, out2in = test_single_row(mongo_query, schema)
        if mongo_query is not None and converted_query is not None and in2out is not None and out2in is not None:
            final_data.append({
                "mongo_query": mongo_query,
                "converted_query": converted_query
            })
    return final_data

if __name__ == "__main__":
    csv_path = "./data_v3/data_v2.csv"
    df = pd.read_csv(csv_path)
    mongo_queries = df["mongo_query"].tolist()
    schemas = df["schema"].apply(eval).tolist()  # Assuming schema is stored as a string representation of a dictionary
    # Clean the queries
    mongo_queries = [clean_query(query) for query in mongo_queries]

    ## indices to remove
    indices_to_remove = []
    # Remove the indices from the lists
    mongo_queries = [query for i, query in enumerate(mongo_queries) if i not in indices_to_remove]
    schemas = [schema for i, schema in enumerate(schemas) if i not in indices_to_remove]

    # Test all rows
    final_data = test_all_rows(mongo_queries, schemas)
    logger.info(f"Final data lenght: {len(final_data)}")
    # Test a single 0th row
    # logger.info("Testing single row")
    # for i in range(15):
    #     modified_query, modified_query, in2out, out2in =  test_single_row(mongo_queries[i], schemas[i])
    #     print(i)
    #     logger.info(f"Mongo query: {mongo_queries[i]}")
    #     logger.info(f"Modified query: {modified_query}")
    #     logger.info(f"Reconstructed query: {modified_query}")
    #     logger.info(f"in2out: {in2out}")
    #     logger.info(f"out2in: {out2in}")
    #     logger.info(f"Schema: {schemas[i]}")
    #     logger.info("--------------------------------------------------------------")
