import re
import ast
import json
from loguru import logger
from typing import Any, Dict, List, Union
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

def parse_mongosh_query(query_str: str) -> tuple[str, str, Dict[str, Any]]:
    """
    Parses a MongoDB shell query string with advanced handling for complex queries.
    """
    # Enhanced regex to handle more complex query formats
    query_pattern = re.match(
        r"db\.(\w+)\.(find|aggregate|update|deleteMany|deleteOne|insertOne|insertMany)\s*\((.*)\)(?:\.sort\((.*)\))?", 
        query_str.strip(), 
        re.DOTALL
    )
    
    if not query_pattern:
        raise ValueError(f"Invalid or unsupported query format: {query_str}")
    
    # Extract groups
    groups = query_pattern.groups()
    collection = groups[0]
    operation = groups[1]
    params_str = groups[2].strip()
    sort_str = groups[3] if len(groups) > 3 and groups[3] else None
    
    # Clean up params string
    params_str = params_str.rstrip(';')
    
    def parse_mongodb_query(query_str: str) -> Any:
        """
        Advanced parsing for MongoDB queries with nested structures and operators
        """
        # Preprocess the query string to handle complex nested structures
        def preprocess_query(s: str) -> str:
            # Handle nested brackets and quotes
            s = s.replace('\n', ' ')  # Remove newlines
            
            # Balance brackets by removing extra closing brackets
            bracket_count = 0
            balanced_s = []
            for char in s:
                if char == '{':
                    bracket_count += 1
                elif char == '}':
                    bracket_count -= 1
                
                if bracket_count >= 0:
                    balanced_s.append(char)
            
            return ''.join(balanced_s)
        
        # Preprocess the query
        processed_query = preprocess_query(query_str)
        
        # Try parsing methods in order of complexity
        parsing_methods = [
            # Method 1: Direct JSON parsing with preprocessing
            lambda q: json.loads(
                re.sub(r'(\w+):', r'"\1":', 
                    re.sub(r'\$(\w+)', r'"\$\1"', 
                        re.sub(r"(?<!\\)'(.*?)(?<!\\)'", r'"\1"', q)
                    )
                )
            ),
            # Method 2: AST literal evaluation
            ast.literal_eval,
            # Method 3: Fallback custom parsing
            lambda q: ast.parse(f"x = {q}").body[0].value
        ]
        
        # Try each parsing method
        for method in parsing_methods:
            try:
                return method(processed_query)
            except Exception as e:
                logger.debug(f"Parsing method failed: {method.__name__}, Error: {e}")
        
        raise ValueError(f"Failed to parse query: {processed_query}")
    
    try:
        # Parse main parameters
        params = parse_mongodb_query(params_str)
        
        # Parse sort parameters if exists
        sort_params = None
        if sort_str:
            sort_params = parse_mongodb_query(sort_str)
        
        return collection, operation, {
            'params': params,
            'sort': sort_params
        }
    
    except Exception as e:
        logger.warning(f"Error parsing query parameters: {e}")
        raise ValueError(f"Error parsing query parameters: {e}")

def execute_pymongo_query(
    database_name: str, 
    query_str: str, 
    connection_uri: str = "mongodb://localhost:27017/"
) -> Union[List[Dict[str, Any]], Any]:
    """
    Execute the parsed MongoDB shell query using PyMongo.
    """
    client = MongoClient(connection_uri)
    try:
        db: Database = client[database_name]
        
        # Parse the mongosh query
        collection_name, operation, query_details = parse_mongosh_query(query_str)
        collection: Collection = db[collection_name]
        
        # Execute operations with comprehensive error handling
        if operation == "find":
            query = query_details['params']
            sort = query_details.get('sort')
            
            cursor = collection.find(query)
            if sort:
                cursor = cursor.sort(list(sort.items()))
            
            return list(cursor)
        
        elif operation == "aggregate":
            return list(collection.aggregate(query_details['params']))
        
        elif operation == "insertOne":
            return collection.insert_one(query_details['params']).inserted_id
        
        elif operation == "insertMany":
            return collection.insert_many(query_details['params']).inserted_ids
        
        elif operation == "deleteOne":
            return collection.delete_one(query_details['params']).deleted_count
        
        elif operation == "deleteMany":
            return collection.delete_many(query_details['params']).deleted_count
        
        elif operation == "update":
            filter_query = query_details['params'][0]
            update_query = query_details['params'][1]
            return collection.update_many(filter_query, update_query).modified_count
        
        else:
            raise ValueError(f"Unsupported operation: {operation}")
    
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise
    finally:
        # Ensure connection is closed
        client.close()

def main():
    """Example Usage"""
    queries = [
        "db.employees.find({ department: 'Sales' })",
        "db.leaveRecords.find({ status: 'approved' });",
        "db.employees.aggregate([ { $lookup: { from: 'leaveRecords', localField: '_id', foreignField: 'employeeId', as: 'leaveInfo' } }, { $project: { firstName: 1, lastName: 1, leaveStatus: { $ifNull: [ { $arrayElemAt: ['$leaveInfo.status', 0] }, 'No Leave Record' ] } } } ])",
        "db.employees.find({ status: 'active', department: 'Engineering' }).sort({ hireDate: 1 })"
    ]
    
    database_name = "hr_management"
    
    for query in queries:
        try:
            logger.info(f"Executing: {query}")
            result = execute_pymongo_query(database_name, query)
            logger.info(f"Result: {result}")
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
        print("-" * 80)

if __name__ == "__main__":
    main()
