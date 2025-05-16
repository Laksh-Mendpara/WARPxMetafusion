import pandas as pd
from typing_extensions import Any, List, Dict
from tqdm import tqdm
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
    return query

def test_single_row(mongo_query: str, schema: Dict[str, Any]):
    try:
        in2out, out2in = build_schema_maps(schema)
        # Convert the actual MongoDB query to a modified flat dictionary
        modified_dict = convert_actual_code_to_modified_dict(mongo_query, out2in)
        # Convert the modified flat dictionary back to an actual MongoDB query string
        collection_name = schema["collections"][0]["name"]
        converted_query = convert_modified_to_actual_code_string(modified_dict, in2out, collection_name)
        # Check if the converted query matches the original query
        # clean the converted query
        converted_query = clean_query(converted_query)
        # assert converted_query == mongo_query, f"Converted query does not match the original query.\nOriginal: {mongo_query}\nConverted: {converted_query}"
        if converted_query != mongo_query:
            logger.error(f"Converted query does not match the original query.\nOriginal: {mongo_query}\nConverted: {converted_query}")
            # check the difference between the two queries
            original_set = set(mongo_query.split())
            converted_set = set(converted_query.split())
            diff = original_set.symmetric_difference(converted_set)
            logger.error(f"Difference: {diff}")
            raise AssertionError(f"Converted query does not match the original query.\nOriginal: {mongo_query}\nConverted: {converted_query}")


        return modified_dict, converted_query
    except ValueError as e:
        logger.error(f"ValueError: {e}")
        logger.debug(f"Mongo query: {mongo_query}")
        return None, None
    except KeyError as e:
        logger.error(f"KeyError: {e}")
        logger.debug(f"Mongo query: {mongo_query}")
        return None, None
        

def test_all_rows(mongo_queries: List[str], schemas: Dict[str, Any]):
    for i, (mongo_query, schema) in tqdm(enumerate(zip(mongo_queries, schemas)), desc="Testing all rows", total=len(mongo_queries)):
        try:
            test_single_row(mongo_query, schema)
        except AssertionError as e:
            logger.error(f"Test failed for query {i}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error for query {i}: {e}")
            raise

if __name__ == "__main__":
    csv_path = "./data_v3/data_v1.csv"
    df = pd.read_csv(csv_path)
    mongo_queries = df["mongo_query"].tolist()
    schemas = df["schema"].apply(eval).tolist()  # Assuming schema is stored as a string representation of a dictionary
    # Clean the queries
    mongo_queries = [clean_query(query) for query in mongo_queries]

    ## indices to remove
    indices_to_remove = [14]
    # Remove the indices from the lists
    mongo_queries = [query for i, query in enumerate(mongo_queries) if i not in indices_to_remove]
    schemas = [schema for i, schema in enumerate(schemas) if i not in indices_to_remove]

    # Test all rows
    # test_all_rows(mongo_queries, schemas)
    # Test a single 0th row
    # logger.info("Testing single row")
    for i in range(50):
        modified_query, converted_query =  test_single_row(mongo_queries[i], schemas[i])
        print(i)
        # logger.info(f"Mongo query: {mongo_queries[i]}")
        # logger.info(f"Modified query: {modified_query}")
        # logger.info(f"Reconstructed query: {converted_query}")
        # logger.info("--------------------------------------------------------------")
        # logger.info(f"Schema: {schemas[i]}")
