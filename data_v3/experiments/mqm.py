import re
import math
import json
from datetime import datetime, timedelta
from dateutil import parser
from typing import Tuple, Dict, Any


# --------------------------
# Helper Functions
# --------------------------

def clean_js_dates(query: str) -> str:
    """Convert JavaScript Date() to Python datetime expressions"""
    def replace_date(match):
        inner = match.group(1).strip()
        if 'getTime()' in inner:
            parts = inner.replace('getTime()', '').split('-')
            if len(parts) > 1:
                delta_expr = parts[1].replace('*', ' ').replace('/', ' ')
                numbers = [int(n) for n in delta_expr.split() if n.isdigit()]
                if numbers:
                    ms = math.prod(numbers)
                    return f'(datetime.utcnow() - timedelta(milliseconds={ms}))'
        return 'datetime.utcnow()'
    
    return re.sub(
        r'new\s*Date\(\s*(.*?)\s*\)',
        replace_date,
        query,
        flags=re.DOTALL | re.IGNORECASE
    )

def parse_iso_date(s: str) -> datetime:
    """Convert ISODate arguments to datetime objects"""
    try:
        return parser.parse(s)
    except parser.ParserError:
        raise ValueError(f"Invalid date format: {s}")

# --------------------------
# Conversion Function
# --------------------------

def convert_mongo_to_pymongo(mongo_query: str) -> Dict[str, Any]:
    """Convert raw MongoDB query to PyMongo-compatible dictionary"""
    # First, check if the query is malformed (missing closing brackets)
    # Count the number of opening and closing brackets/braces/parentheses
    opening_count = mongo_query.count('{') + mongo_query.count('[') + mongo_query.count('(')
    closing_count = mongo_query.count('}') + mongo_query.count(']') + mongo_query.count(')')
    
    # If brackets don't match, we need to fix the query
    if opening_count != closing_count:
        # Try to fix by adding missing closing braces
        if mongo_query.count('{') > mongo_query.count('}'):
            mongo_query = mongo_query + '}'*(mongo_query.count('{') - mongo_query.count('}'))
        if mongo_query.count('[') > mongo_query.count(']'):
            mongo_query = mongo_query + ']'*(mongo_query.count('[') - mongo_query.count(']'))
        if mongo_query.count('(') > mongo_query.count(')'):
            mongo_query = mongo_query + ')'*(mongo_query.count('(') - mongo_query.count(')'))
    
    # Store whether the original query ends with a closing parenthesis
    ends_with_closing_paren = mongo_query.strip().endswith(')')
    
    # First capture any math expressions in the query and replace them with placeholders
    math_expressions = {}
    expression_count = 0
    
    def replace_math_expression(match):
        nonlocal expression_count
        placeholder = f"__MATH_EXPR_{expression_count}__"
        expression_count += 1
        expression = match.group(0)
        math_expressions[placeholder] = expression
        return placeholder
    
    # Find expressions like 34.0522+0.01 or -118.2437-0.01
    # Look for numeric values with + or - operations
    expr_pattern = r'(\d+\.\d+|\d+)([+\-]\d+\.\d+|\d+)'
    cleaned_query = re.sub(expr_pattern, replace_math_expression, mongo_query)
    
    eval_ctx = {
        'datetime': datetime,
        'timedelta': timedelta,
        'ISODate': parse_iso_date,
        'math': math,
        '__builtins__': None
    }
    
    # Add math expression placeholders to the eval context
    for placeholder, _ in math_expressions.items():
        eval_ctx[placeholder] = placeholder  # Add as string to prevent evaluation

    cleaned_query = clean_js_dates(cleaned_query)

    components = {
        'filter': {},
        'projection': None,
        'sort': [],
        'limit': None,
        'ends_with_closing_paren': ends_with_closing_paren,
        'math_expressions': math_expressions,
        'operation': 'find'  # Default operation
    }
    
    # Check if this is a countDocuments query
    if 'countDocuments' in cleaned_query:
        components['operation'] = 'countDocuments'
        count_pattern = r'\.countDocuments\(\s*(.*?)\s*\)'
        count_match = re.search(count_pattern, cleaned_query, re.DOTALL)
        
        if count_match:
            filter_content = count_match.group(1).strip()
            
            # Try to parse the filter as JSON first
            try:
                # Replace ISODate with a placeholder
                iso_pattern = r'ISODate\("([^"]+)"\)'
                
                def replace_iso(match):
                    date_str = match.group(1)
                    return f'"__ISO_DATE__{date_str}__"'
                
                fixed_filter = re.sub(iso_pattern, replace_iso, filter_content)
                
                # Try to parse as JSON
                components['filter'] = json.loads(fixed_filter)
                
                # Replace placeholders back with actual ISODate objects
                def process_dates(obj):
                    if isinstance(obj, dict):
                        for k, v in obj.items():
                            if isinstance(v, str) and v.startswith('__ISO_DATE__') and v.endswith('__'):
                                date_str = v.replace('__ISO_DATE__', '').replace('__', '')
                                obj[k] = parse_iso_date(date_str)
                            else:
                                process_dates(v)
                    elif isinstance(obj, list):
                        for i, item in enumerate(obj):
                            if isinstance(item, (dict, list)):
                                process_dates(item)
                    return obj
                
                components['filter'] = process_dates(components['filter'])
            except (json.JSONDecodeError, SyntaxError):
                try:
                    components['filter'] = eval(filter_content, eval_ctx)
                except (SyntaxError, TypeError):
                    # If both fail, save the original filter string for reconstruction
                    components['filter'] = {}
                    components['original_filter'] = filter_content
            # Always save the original filter string for robust reconstruction
            components['original_filter'] = filter_content
            
            return components

    # Extract find() clause with improved regex for nested structures
    # We need to handle complex queries with operators like $or that have arrays
    try:
        # First approach: Extract the entire filter object using json.loads
        # Extract content between find( and the matching )
        find_pattern = r'\.find\(\s*(.*?)\s*\)'
        find_match = re.search(find_pattern, cleaned_query, re.DOTALL)
        
        if find_match:
            filter_content = find_match.group(1).strip()
            
            # Check if there's a projection (second argument)
            projection_str = None
            if ',' in filter_content:
                # Find the position of the last top-level comma
                # We need to handle nested structures carefully
                bracket_count = 0
                last_comma_pos = -1
                
                for i, char in enumerate(filter_content):
                    if char == '{' or char == '[':
                        bracket_count += 1
                    elif char == '}' or char == ']':
                        bracket_count -= 1
                    elif char == ',' and bracket_count == 0:
                        last_comma_pos = i
                
                if last_comma_pos != -1:
                    filter_str = filter_content[:last_comma_pos].strip()
                    projection_str = filter_content[last_comma_pos + 1:].strip()
                else:
                    filter_str = filter_content
            else:
                filter_str = filter_content
            
            # Handle empty filter case
            if filter_str.strip() == '':
                components['filter'] = {}
            else:
                # Try to parse the filter as JSON first
                try:
                    # Replace ISODate with a placeholder
                    iso_pattern = r'ISODate\("([^"]+)"\)'
                    
                    def replace_iso(match):
                        date_str = match.group(1)
                        return f'"__ISO_DATE__{date_str}__"'
                    
                    fixed_filter = re.sub(iso_pattern, replace_iso, filter_str)
                    
                    # Try to parse as JSON
                    components['filter'] = json.loads(fixed_filter)
                    
                    # Replace placeholders back with actual ISODate objects
                    def process_dates(obj):
                        if isinstance(obj, dict):
                            for k, v in obj.items():
                                if isinstance(v, str) and v.startswith('__ISO_DATE__') and v.endswith('__'):
                                    date_str = v.replace('__ISO_DATE__', '').replace('__', '')
                                    obj[k] = parse_iso_date(date_str)
                                else:
                                    process_dates(v)
                        elif isinstance(obj, list):
                            for i, item in enumerate(obj):
                                if isinstance(item, (dict, list)):
                                    process_dates(item)
                        return obj
                    
                    components['filter'] = process_dates(components['filter'])
                except (json.JSONDecodeError, SyntaxError):
                    try:
                        components['filter'] = eval(filter_str, eval_ctx)
                    except (SyntaxError, TypeError):
                        # If both fail, save the original filter string for reconstruction
                        components['filter'] = {}
                        components['original_filter'] = filter_str
                # Always save the original filter string for robust reconstruction
                components['original_filter'] = filter_str
            
            # Process projection if present
            if projection_str:
                try:
                    components['projection'] = json.loads(projection_str)
                except (json.JSONDecodeError, SyntaxError):
                    try:
                        components['projection'] = eval(projection_str, eval_ctx)
                    except (SyntaxError, TypeError):
                        components['projection'] = None
    
    except Exception as e:
        # If any error occurs, keep essential query information for reconstruction
        components['original_filter'] = mongo_query
        components['parse_error'] = str(e)

    # Extract sort clause
    sort_pattern = r'\.sort\(\s*({.*?})\s*\)'
    sort_match = re.search(sort_pattern, cleaned_query, re.DOTALL)
    if sort_match:
        sort_str = sort_match.group(1)
        # Create a safer evaluation context for sort
        sort_eval_ctx = {
            'datetime': datetime,
            'timedelta': timedelta,
            'ISODate': parse_iso_date,
            'math': math,
            '__builtins__': None
        }
        
        # Convert MongoDB sort syntax to Python dictionary using safer approach
        try:
            # Convert MongoDB sort syntax like {field:-1} to Python dict
            sort_str_fixed = re.sub(r'(\w+)\s*:\s*(-?\d+)', r'"\1": \2', sort_str)
            sort_dict = json.loads(sort_str_fixed)
            components['sort'] = [(k, v) for k, v in sort_dict.items()]
        except (json.JSONDecodeError, SyntaxError):
            # Fall back to regex based parsing if JSON conversion fails
            sort_list = []
            field_pattern = r'(\w+)\s*:\s*(-?\d+)'
            for match in re.finditer(field_pattern, sort_str):
                field, value = match.groups()
                sort_list.append((field, int(value)))
            components['sort'] = sort_list

    # Extract limit clause - FIXED: Make sure to handle any whitespace correctly
    limit_pattern = r'\.limit\(\s*(\d+)\s*\)'
    limit_match = re.search(limit_pattern, cleaned_query, re.DOTALL)
    if limit_match:
        components['limit'] = int(limit_match.group(1))
    else:
        # Try extracting limit from the original query if it wasn't found in the cleaned one
        original_limit_match = re.search(r'\.limit\(\s*(\d+)\s*\)', mongo_query, re.DOTALL)
        if original_limit_match:
            components['limit'] = int(original_limit_match.group(1))
            print(f"Extracted limit {components['limit']} from original query")

    return components

# --------------------------
# Reconstruction Function
# --------------------------

def reconstruct_mongo_query(pymongo_dict: Dict[str, Any]) -> str:
    """Convert PyMongo dictionary back to MongoDB query syntax"""
    # Check if this is a countDocuments operation
    if pymongo_dict.get('operation') == 'countDocuments':
        query = "db.event.countDocuments("
        
        # Process filter for countDocuments
        if not pymongo_dict['filter']:
            query += "{}"
        else:
            # Process the filter dictionary to handle datetime objects
            class DateTimeEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, datetime):
                        return f'ISODate("{obj.isoformat()}Z")'
                    elif isinstance(obj, list):
                        return super().default(obj)
                    return super().default(obj)
            
            processed_filter = json.dumps(pymongo_dict['filter'], cls=DateTimeEncoder)
            # Remove quotes around ISODate calls
            processed_filter = re.sub(r'"ISODate\(([^)]+)\)"', r'ISODate(\1)', processed_filter)
            
            # Restore math expressions if present
            if 'math_expressions' in pymongo_dict:
                for placeholder, expression in pymongo_dict['math_expressions'].items():
                    processed_filter = processed_filter.replace(f'"{placeholder}"', expression)
            
            query += processed_filter
        
        # Add closing parenthesis if needed
        if pymongo_dict.get('ends_with_closing_paren', True):
            query += ')'
            
        return query
    
    # If we had a parse error or complex original filter, use original filter for find part
    if 'original_filter' in pymongo_dict:
        # Build a minimal query using the original filter
        query = "db.event.find("
        
        # Add the original filter
        query += pymongo_dict['original_filter']
        
        # Close the parenthesis if needed
        if not query.endswith(')'):
            query += ')'
            
        # Add any sort/limit clauses
        if pymongo_dict['sort']:
            sort_dict = {k: v for k, v in pymongo_dict['sort']}
            sort_str = json.dumps(sort_dict)
            query += f".sort({sort_str})"
            
        if pymongo_dict['limit'] is not None:
            query += f".limit({pymongo_dict['limit']})"
            
        return query
    
    # If we have math expressions, make sure they're applied correctly
    math_expressions = pymongo_dict.get('math_expressions', {})
    
    # Custom JSON encoder to handle datetime objects
    class DateTimeEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime):
                return f'ISODate("{obj.isoformat()}Z")'
            elif isinstance(obj, list):
                return super().default(obj)
            return super().default(obj)
    
    query = "db.event.find("
    
    # Check if filter is empty - if so, don't add braces
    if not pymongo_dict['filter']:
        query += ""
    else:
        # Process the filter dictionary to handle datetime objects
        processed_filter = json.dumps(pymongo_dict['filter'], cls=DateTimeEncoder)
        # Remove quotes around ISODate calls
        processed_filter = re.sub(r'"ISODate\(([^)]+)\)"', r'ISODate(\1)', processed_filter)
        
        # Restore math expressions if present
        if math_expressions:
            for placeholder, expression in math_expressions.items():
                processed_filter = processed_filter.replace(f'"{placeholder}"', expression)
        
        query += processed_filter
    
    if pymongo_dict['projection']:
        projection_str = json.dumps(pymongo_dict['projection'])
        if not pymongo_dict['filter']:
            # Empty filter, just add projection
            query += projection_str
        else:
            # Add projection after filter
            query = query[:-1] + ', ' + projection_str + ')'
    else:
        # Check if we should add a closing parenthesis
        ends_with_closing_paren = pymongo_dict.get('ends_with_closing_paren', True)
        if ends_with_closing_paren:
            query += ')'

    if pymongo_dict['sort']:
        # Generate a fully quoted sort clause to match standard MongoDB format
        sort_dict = {k: v for k, v in pymongo_dict['sort']}
        sort_str = json.dumps(sort_dict)
        query += f".sort({sort_str})"

    if pymongo_dict['limit'] is not None:
        query += f".limit({pymongo_dict['limit']})"

    return query


# --------------------------
# Usage Example
# --------------------------

if __name__ == "__main__":
    input_query = """
    db.event.find({"timestamp": {"$gte": ISODate("2024-02-01T00:00:00Z"), "$lt": ISODate("2024-02-16T00:00:00Z")}, "severity_level": {"$gte": 2}})
    """

    # Conversion
    pymongo_fmt = convert_mongo_to_pymongo(input_query)
    print("PyMongo Format:")
    print(json.dumps(pymongo_fmt, indent=2, default=str))

    # Reconstruction
    reconstructed = reconstruct_mongo_query(pymongo_fmt)
    print("\nReconstructed Query:")
    print(reconstructed)
