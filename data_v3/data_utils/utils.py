import pandas as pd
from typing_extensions import Any, List, Dict
from loguru import logger
from .helper import (
    clean_query,
    build_schema_maps,
    convert_actual_code_to_modified_dict,
    convert_modified_to_actual_code_string
)

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
        modified_query = convert_actual_code_to_modified_dict(mongo_query, in2out)
        # Collection Name
        collection_name = schema["collections"][0]["name"]
        # Convert the modified code back to actual code
        reconstructed_query = convert_modified_to_actual_code_string(modified_query, out2in, collection_name)
        # Clean the reconstructed query
        reconstructed_query = clean_query(reconstructed_query)
        if reconstructed_query == mongo_query:
            return modified_query, collection_name, in2out, out2in
        else:
            logger.error(f"Reconstructed query does not match the original query.\nOriginal: {mongo_query}\nReconstructed: {reconstructed_query}")
            return None, None, None, None
    except Exception as e:
        logger.error(f"Error processing query: {mongo_query}\nError: {e}")
        return None, None, None, None


def modify_all_rows(mongo_queries: List[str], schemas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Modifies all MongoDB queries based on the provided schemas.
    """
    modified_queries = []
    for i, (mongo_query, schema) in enumerate(zip(mongo_queries, schemas)):
        modified_query, collection_name, in2out, out2in = modify_single_row(mongo_query, schema)
        if modified_query and collection_name and in2out and out2in:
            modified_queries.append({
                "modified_query": modified_query,
                "collection_name": collection_name,
                "in2out": in2out,
                "out2in": out2in
            })
    return modified_queries
