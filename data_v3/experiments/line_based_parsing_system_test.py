import pandas as pd
from typing_extensions import Any, List, Dict
from loguru import logger
from tqdm import tqdm
from .utils import (
    clean_query,
    build_schema_maps,
    convert_actual_code_to_modified_dict,
    convert_modified_to_actual_code_string
)
from .line_based_parsing import (
    convert_to_lines,
    parse_line_based_query
)


def clean_modified_dict(modified_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Cleans the modified dictionary by removing empty values.
    """
    cleaned_dict = {}
    for key, value in modified_dict.items():
        if value:
            cleaned_dict[key] = value
    return {k: v for k, v in cleaned_dict.items() if v}


def modify_single_row(mongo_query: str, schema: Dict[str, Any]) -> str:
    """
    Modifies a single MongoDB query string based on the provided schema and schema maps.
    """
    try:
        # Clean the query
        mongo_query = clean_query(mongo_query)
        # Build schema maps
        in2out, out2in = build_schema_maps(schema)
        # Convert the actual code to modified code
        modified_query = convert_actual_code_to_modified_dict(mongo_query, out2in)
        # Collection Name
        collection_name = schema["collections"][0]["name"]
        # Convert the modified code back to actual code
        reconstructed_query = convert_modified_to_actual_code_string(modified_query, in2out, collection_name)
        # Clean the reconstructed query
        reconstructed_query = clean_query(reconstructed_query)
        if reconstructed_query != mongo_query:
            return None, None, None, None
        else:
            return modified_query, collection_name, in2out, out2in
    except Exception as _:
        return None, None, None, None


def modify_all_rows(mongo_queries: List[str], schemas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Modifies all MongoDB queries based on the provided schemas.
    """
    modified_queries = []
    for _, (mongo_query, schema) in tqdm(enumerate(zip(mongo_queries, schemas)), total=len(mongo_queries), desc="Modifying Queries"):
        modified_query, collection_name, in2out, out2in = modify_single_row(mongo_query, schema)
        if modified_query:
            modified_queries.append({
                "modified_query": modified_query,
                "collection_name": collection_name,
                "in2out": in2out,
                "out2in": out2in
            })
    return modified_queries


def test_line_based_parsing(modified_query: Dict[str, Any]):
    """
    Tests the line-based parsing of a modified MongoDB query.
    """
    try:
        modified_query = clean_modified_dict(modified_query)
        lines = convert_to_lines(modified_query)
        reconstructed_query = parse_line_based_query(lines)
        if modified_query != reconstructed_query:
            logger.error(f"failed for input: {modified_query}\n lines: {lines}\n reconstructed_query: {reconstructed_query}")
            raise AssertionError(f"Line-based parsing failed for query: {modified_query}")
    except Exception as e:
        logger.error(f"Error in line-based parsing: {e}")
        raise e

def test_all_line_based_parsing(modified_queries: List[Dict[str, Any]]):
    """
    Tests the line-based parsing for all modified MongoDB queries.
    """
    for query in tqdm(modified_queries, desc="Testing Line-based Parsing", total=len(modified_queries)):
        modified_query = query["modified_query"]
        test_line_based_parsing(modified_query)


if __name__ == "__main__":
    df = pd.read_csv("./data_v3/data_v2.csv")
    logger.info(f"Total Queries: {len(df)}")
    mongo_queries = df["mongo_query"].tolist()
    mongo_queries = [clean_query(query) for query in mongo_queries]
    schemas = df["schema"].apply(eval).tolist()
    # print 0th query and schema
    # logger.debug(f"0th query: {mongo_queries[0]}")
    # logger.debug(f"0th schema: {schemas[0]}")
    # exit()
    # logger.info(f"Modifying queries...")
    modified_queries = modify_all_rows(mongo_queries, schemas)
    logger.info(f"Total Valid queries: {len(modified_queries)}")
    # test line parsing
    logger.info(f"Testing line-based parsing...")
    test_all_line_based_parsing(modified_queries)
    logger.info(f"All tests passed.")