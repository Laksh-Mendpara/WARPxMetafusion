import pandas as pd
from typing_extensions import Any, List, Dict
from loguru import logger
from tqdm import tqdm
from .helper import (
    clean_query,
    build_schema_maps,
    convert_actual_code_to_modified_dict,
    convert_modified_to_actual_code_string
)
from .line_based_parsing import (
    clean_modified_dict,
    convert_to_lines,
    parse_line_based_query
)
from .schema_utils import schema_to_line_based


def modify_single_row_base_form(mongo_query: str, schema: Dict[str, Any]) -> str:
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
            return None, None, None, None, None, None
        else:
            return mongo_query, modified_query, collection_name, in2out, out2in, schema
    except Exception as _:
        return None, None, None, None, None, None


def modify_all_rows_base_from(mongo_queries: List[str], schemas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Modifies all MongoDB queries based on the provided schemas.
    """
    modified_queries = []
    for _, (mongo_query, schema) in tqdm(enumerate(zip(mongo_queries, schemas)), total=len(mongo_queries), desc="Modifying Queries"):
        mongo_query, modified_query, collection_name, in2out, out2in, schema = modify_single_row_base_form(mongo_query, schema)
        if modified_query is not None:
            modified_queries.append({
                "mongo_query": mongo_query,
                "modified_query": modified_query,
                "collection_name": collection_name,
                "in2out": in2out,
                "out2in": out2in,
                "schema": schema
            })
    return modified_queries


def modify_line_based_parsing(modified_query_data: str) -> Dict[str, Any]:
    """
    Tests the line-based parsing of a modified MongoDB query.
    """
    try:
        modified_query = clean_modified_dict(modified_query_data["modified_query"])
        lines = convert_to_lines(modified_query)
        reconstructed_query = parse_line_based_query(lines)
        if modified_query != reconstructed_query:
            return None
        else:
            modified_query_data["line_based_query"] = lines
            return modified_query_data
    except Exception as e:
        return None


def modify_all_line_based_parsing(modified_queries: List[Dict[str, Any]]):
    """
    Tests the line-based parsing for all modified MongoDB queries.
    """
    line_based_queries = []
    for query_data in tqdm(modified_queries, desc="Testing Line-based Parsing", total=len(modified_queries)):
        line_based_query = modify_line_based_parsing(query_data)
        if line_based_query:
            line_based_queries.append(line_based_query)
    return line_based_queries


def modify_all_schema(query_data: List[Dict[str, Any]]) -> List[str]:
    """
    Converts all schemas to line-based format.
    """
    final_data = []
    for query in tqdm(query_data, desc="Converting Schemas to Line-based Format", total=len(query_data)):
        # try:
        line_based_schema = schema_to_line_based(query["schema"])
        # if line_based_schema:
        query["line_based_schema"] = line_based_schema
        final_data.append(query)
        # except Exception as e:
        #     pass
        # logger.debug(f"Line-based schema: {line_based_schema}")
    return final_data


def load_csv(file_path: str) -> pd.DataFrame:
    """
    Loads a CSV file into a pandas DataFrame.
    """
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Loaded CSV file: {file_path}")
        return df
    except Exception as e:
        logger.error(f"Error loading CSV file: {e}")
        raise e
    

def modify_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Modifies a DataFrame by applying the modify_all_rows function.
    """
    logger.info("Modifying DataFrame...")
    logger.debug(f"input DataFrame length: {len(df)}")
    mongo_queries = df["mongo_query"].tolist()
    schemas = df["schema"].apply(eval).tolist()
    modified_queries = modify_all_rows_base_from(mongo_queries, schemas)
    logger.debug(f"Modified queries length: {len(modified_queries)}")
    line_based_queries = modify_all_line_based_parsing(modified_queries)
    logger.debug(f"Line-based queries length: {len(line_based_queries)}")
    final_data = modify_all_schema(line_based_queries)
    logger.debug(f"Modified schemas length: {len(final_data)}")
    return final_data

def main(final_data: List[Dict[str, Any]]):
    # try reconstructing original query from line-based query
    for i in range(len(final_data)):
        index_allowed = [746]
        if i in index_allowed:
            continue
        original_query = final_data[i]["mongo_query"]
        line_based_query = final_data[i]["line_based_query"]
        # reconstructed modified query
        reconstructed_modified_query = parse_line_based_query(line_based_query)
        # reconstructed original query
        reconstructed_original_query = convert_modified_to_actual_code_string(reconstructed_modified_query, final_data[i]["in2out"], final_data[i]["collection_name"])
        if original_query != clean_query(reconstructed_original_query):
            
            logger.error(f"index: {i}")
            logger.error(f"Original query: {original_query}")
            logger.error(f"Reconstructed original query: {reconstructed_original_query}")
            logger.error(f"Modified query: {final_data[i]['modified_query']}")
            logger.error(f"Reconstructed modified query: {reconstructed_modified_query}")
            logger.error(f"Line-based query: {line_based_query}")
            # logger.error(f"Schema: {final_data[i]['schema']}")
            logger.warning("--------------------------------------------------")
            assert original_query == clean_query(reconstructed_original_query), f"Original query does not match reconstructed original query at index {i}"
    exit(0)
        

if __name__ == "__main__":
    pdf_path = "./data_v3/data_v2.csv"
    df = load_csv(pdf_path)
    final_data = modify_dataframe(df)
    # main(final_data)
    logger.info(f"Final data length: {len(final_data)}")
    logger.debug(f"Final data type: {final_data[0]}\n\n")

    for i, (query_data) in enumerate(final_data):
        logger.debug(f"Line-based query {i}: {query_data['line_based_query']}")
        logger.debug(f"Modified schema {i}: {query_data['line_based_schema']}\n\n\n\n")
        if i > 3:
            break
