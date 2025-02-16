import sqlite3
import pandas as pd
import argparse
from typing_extensions import List, Dict
from pathlib import Path
import os
from loguru import logger

def split_schemas_by_create_table(schema_list: List[str]) -> List[str]:
    
    split_schemas = []
    
    for schema in schema_list:
        # Split the current schema string by "CREATE TABLE"
        tables = schema.split("CREATE TABLE")
        
        for table in tables:
            if table.strip():  # Ignore empty or whitespace-only entries
                # Re-add "CREATE TABLE" to the table schema and strip extra spaces
                split_schemas.append("CREATE TABLE " + table.strip())
    return list(set(split_schemas))

def check_schema_accuracy(
        schemas : List[str],
        db_path : str,
    ) -> float:
    connection = sqlite3.connect(db_path)
    crsr = connection.cursor()

    incorrect_schemas = 0
    for schema in schemas:
        try:
            crsr.execute(schema)
        except Exception as e:
            logger.error(f"Error in schema: {schema}")
            logger.error(e)
            print("/n/n/n")
            incorrect_schemas += 1
    
    connection.close()
    return 1 - (incorrect_schemas / len(schemas))

def check_sql_query_accuracy(
        queries : List[str],
        db_path : str,
    ) -> float:
    connection = sqlite3.connect(db_path)
    crsr = connection.cursor()

    incorrect_queries = 0
    for query in queries:
        try:
            crsr.execute(query)
        except Exception as e:
            logger.error(f"Error in query: {query}")
            logger.error(e)
            print("/n/n/n")
            incorrect_queries += 1
    
    connection.close()
    return 1 - (incorrect_queries / len(queries))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_path", default="data/final_data.csv", type=str)
    parser.add_argument("--db_path", default="temp.db", type=str)
    args = parser.parse_args()
    
    if os.path.exists(args.db_path):
        os.remove(args.db_path)
    Path(args.db_path).touch()

    df = pd.read_csv(args.data_path)
    schemas = df['schema'].values
    unique_schemas = split_schemas_by_create_table(list(set(schemas)))
    res_schema = check_schema_accuracy(unique_schemas, args.db_path)
    
    sql_queries = df['sql_query'].values
    unique_sql_queries = list(set(sql_queries))
    res_query = check_sql_query_accuracy(unique_sql_queries, args.db_path)
    
    logger.info(f"Schema Accuracy: {res_schema}")
    logger.info(f"Query Accuracy: {res_query}")
