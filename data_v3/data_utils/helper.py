from typing import Any, Dict, Tuple, List
from loguru import logger
import json
import re


def normalize_number(match):
        num_str = match.group(0)
        if '.' in num_str:
            # Normalize float by removing trailing zeros and decimal point if needed
            return str(float(num_str))
        return num_str  # Leave integers as is


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
    # Normalize the query string
    query = re.sub(r'(?<!["\w])(-?\d+\.\d+)(?!["\w])', normalize_number, query)
    return query


def extract_field_paths(properties: Dict[str, Any], prefix: str = "") -> Dict[str, str]:
    """
    Recursively extract all leaf property names to full dot-paths
    from a Mongo JSON Schema 'properties' dict.
    """
    paths: Dict[str, str] = {}
    for key, val in properties.items():
        current = prefix + key
        # If nested object, recurse
        if val.get("bsonType") == "object" and "properties" in val:
            paths.update(extract_field_paths(val["properties"], current + "."))
        else:
            paths[key] = current
    return paths


def build_schema_maps(schema: Dict[str, Any]) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    From a full JSON Schema, return two maps:
      - input_to_output: flat key -> nested field path
      - output_to_input: nested field path -> flat key
    """
    props = schema["collections"][0]["document"]["properties"]
    input_to_output = extract_field_paths(props)
    output_to_input = {v: k for k, v in input_to_output.items()}
    return input_to_output, output_to_input


def set_nested(d: Dict[str, Any], keys: List[str], value: Any) -> None:
    """
    Helper to set a nested value in a dict given a list of keys.
    """
    for k in keys[:-1]:
        d = d.setdefault(k, {})
    d[keys[-1]] = value


def dot_notation_to_nested(dot: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a dict with dot-notation keys to nested dict structure.
    E.g. {"a.b": v} -> {"a": {"b": v}}
    """
    out: Dict[str, Any] = {}
    for key, val in dot.items():
        parts = key.split('.')
        set_nested(out, parts, val)
    return out


def nested_to_dot(d: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
    """
    Convert nested dict to dot-notation keys. Treat operator-dicts as leaves.
    """
    out: Dict[str, Any] = {}
    for k, v in d.items():
        new_pref = f"{prefix}.{k}" if prefix else k
        # operator-dict leaf?
        if isinstance(v, dict) and v and all(str(kk).startswith("$") for kk in v):
            out[new_pref] = v
        elif isinstance(v, dict):
            out.update(nested_to_dot(v, new_pref))
        else:
            out[new_pref] = v
    return out


def modified_to_actual_query(modified: Dict[str, Any],
                            input_to_output: Dict[str, str]) -> Dict[str, Any]:
    """
    Convert a flat filter dict (flat_key -> value/operator) into
    a nested Mongo query dict according to the schema map.
    If a key is not in the schema, treat it as dot notation.
    """
    query: Dict[str, Any] = {}
    for flat_key, val in modified.items():
        if flat_key in input_to_output:
            path = input_to_output[flat_key].split('.')
            set_nested(query, path, val)
        else:
            # fallback: treat as dot notation
            set_nested(query, flat_key.split('.'), val)
    return query


def actual_to_modified_query(actual: Dict[str, Any],
                             output_to_input: Dict[str, str]) -> Dict[str, Any]:
    """
    Flatten a nested Mongo query dict back into flat_key -> value/operator.
    Operator-dicts (keys starting with $) are treated as leaves.
    If a path is not in output_to_input mapping, preserve it as-is.
    """
    flat: Dict[str, Any] = {}

    def recurse(d: Any, prefix: str = "") -> None:
        # operator-dict leaf
        if isinstance(d, dict) and d and all(k.startswith("$") for k in d):
            if prefix in output_to_input:
                flat[output_to_input[prefix]] = d
            else:
                # If not in mapping, preserve the original dot notation path
                flat[prefix] = d
            return
            
        # leaf non-dict
        if not isinstance(d, dict):
            if prefix in output_to_input:
                flat[output_to_input[prefix]] = d
            else:
                # If not in mapping, preserve the original dot notation path
                flat[prefix] = d
            return
            
        # recurse deeper
        for k, v in d.items():
            new_pref = f"{prefix}.{k}" if prefix else k
            recurse(v, new_pref)

    recurse(actual)
    return flat


def build_query_and_options(
    modified: Dict[str, Any],
    input_to_output: Dict[str, str]
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    From a flat input dict that may include filter fields plus
    special options (limit, skip, sort, projection), return:
      - nested Mongo filter dict
      - options dict with keys: limit, skip, sort, projection
    """
    # extract special keys
    options: Dict[str, Any] = {}
    for opt in ("limit", "skip", "sort", "projection"):  # in this order
        if opt in modified:
            options[opt] = modified.pop(opt)

    # build nested filter
    query = modified_to_actual_query(modified, input_to_output)
    return query, options


def convert_modified_to_actual_code_string(
    modified_input: dict,
    in2out: dict,
    collection_name: str = "events"
) -> str:
    """
    Converts a modified (flat) dict into a MongoDB code string.
    Omits the projection argument if opts['projection'] is empty.
    Prints filter in dot-notation to match db.find syntax.
    """
    import re

    # Remove internal metadata fields before processing
    modified_input = {k: v for k, v in modified_input.items() if not k.startswith('_')}
    
    filter_dict, opts = build_query_and_options(modified_input.copy(), in2out)

    # 1) dot-ify the filter dict
    dot_filter = nested_to_dot(filter_dict)
    filter_str = json.dumps(dot_filter, separators=(",", ":"))
    
    # 2) Convert date strings back to appropriate MongoDB date format
    # This regex matches ISO date strings like "2024-01-01T00:00:00Z"
    date_pattern = r'"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)"'
    
    # Check if there was a newDate string in the original query
    # If so, we need to preserve that format instead of using ISODate
    if "newDate" in modified_input.get("_original_query_format", ""):
        filter_str = re.sub(date_pattern, r'newDate("\1")', filter_str)
    else:
        # Default to ISODate format
        filter_str = re.sub(date_pattern, r'ISODate("\1")', filter_str)

    # 3) Restore special time expressions that might have been converted
    time_expr_pattern = r'"(newDate\.getTime\(\)-\d+)"'
    filter_str = re.sub(time_expr_pattern, r'\1', filter_str)

    # 4) only include projection if non-empty
    projection = opts.get("projection", None)
    projection_str = ""
    if projection:
        projection_str = json.dumps(projection, separators=(',', ':'))
        # Also convert date strings in projection if any
        if "newDate" in modified_input.get("_original_query_format", ""):
            projection_str = re.sub(date_pattern, r'newDate("\1")', projection_str)
        else:
            projection_str = re.sub(date_pattern, r'ISODate("\1")', projection_str)

    parts = [f"db.{collection_name}.find({filter_str}"
             + (f", {projection_str}" if projection else "")
             + ")"]

    # 5) chain optional methods
    if opts.get("sort"):
        # Handle different sort formats
        sort_value = opts['sort']
        if isinstance(sort_value, list):
            # Convert array format to object format
            sort_obj = {}
            for key, direction in sort_value:
                sort_obj[key] = direction
            sort_value = sort_obj
            
        # For sort parameters, we want to preserve the MongoDB format exactly
        # Convert the sort object to a string without quotes around the entire thing
        if isinstance(sort_value, dict):
            sort_items = []
            for k, v in sort_value.items():
                sort_items.append(f'"{k}":{v}')
            sort_str = '{' + ','.join(sort_items) + '}'
        else:
            sort_str = str(sort_value)
            
        parts.append(f".sort({sort_str})")
        
    if opts.get("skip"):
        parts.append(f".skip({opts['skip']})")
        
    if opts.get("limit"):
        parts.append(f".limit({opts['limit']})")

    return "".join(parts)


def convert_actual_code_to_modified_dict(actual_code: str, out2in: dict) -> dict:
    """
    Converts an actual MongoDB query string into a modified flat dictionary.
    WARNING: This assumes the input is sanitized and safe (e.g., evaluated from a trusted source).
    """
    import ast
    import re
    import json
    from datetime import datetime, timedelta

    # Store original number strings
    original_numbers = {}

    def store_number_strings(s: str) -> str:
        def replace_number(match):
            num_str = match.group(0)
            # Only store if it has a decimal point (to preserve trailing zeros)
            if '.' in num_str:
                try:
                    num = float(num_str)
                    # Store the longest representation for this float
                    key = str(num)
                    if key not in original_numbers or len(num_str) > len(original_numbers[key]):
                        original_numbers[key] = num_str
                except ValueError:
                    pass
            return num_str

        # Match numbers with optional decimal places and trailing zeros
        number_pattern = r'-?\d+\.\d+'
        re.sub(number_pattern, replace_number, s)
        return s

    def preprocess_mongo_syntax(query_str):
        store_number_strings(query_str)
        
        # Replace ISODate("..."), ISODate('...') with the date string
        query_str = re.sub(r'ISODate\("([^"]+)"\)', r'"\1"', query_str)
        query_str = re.sub(r"ISODate\('([^']+)'\)", r'"\1"', query_str)

        # Handle newDate(newDate().getTime()-<expr>)
        def newdate_minus_expr(match):
            expr = match.group(1)
            try:
                # Evaluate the expression safely (only numbers and operators)
                ms = int(eval(expr, {"__builtins__": None}, {}))
                from datetime import datetime, timedelta
                dt = datetime.utcnow() + timedelta(milliseconds=ms)
                return '"' + dt.strftime('%Y-%m-%dT%H:%M:%SZ') + '"'
            except Exception:
                return '"1970-01-01T00:00:00Z"'  # fallback
        query_str = re.sub(r'newDate\(newDate\(\)\.getTime\(\)([-+*/0-9 ]+)\)', newdate_minus_expr, query_str)

        # Replace newDate() with current UTC time
        from datetime import datetime
        now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        query_str = re.sub(r'newDate\(\)', f'"{now}"', query_str)

        # Replace newDate(expr) with a string (handle both quote types)
        query_str = re.sub(r'newDate\("([^"]+)"\)', r'"\1"', query_str)
        query_str = re.sub(r"newDate\('([^']+)'\)", r'"\1"', query_str)
        query_str = re.sub(r'newDate\((.*?)\)', r'"\1"', query_str)

        # Fix unbalanced brackets
        if query_str.count('{') > query_str.count('}'):
            query_str += "}" * (query_str.count('{') - query_str.count('}'))
        return query_str

    # Extract filter dictionary from find() call using regex
    def extract_filter_dict(code):
        # Match db.collection.find(...) pattern
        find_pattern = r'db\.[^.]+\.find\((.*?)(?:\)|,\s*{)'
        find_match = re.search(find_pattern, code)
        if not find_match:
            raise ValueError("Could not extract filter parameters from find() call")
        
        filter_str = find_match.group(1)
        
        # If empty, return empty dict
        if not filter_str.strip():
            return {}
            
        try:
            # Try parsing as JSON
            return json.loads(filter_str)
        except json.JSONDecodeError:
            # Try with ast.literal_eval
            try:
                return ast.literal_eval(filter_str)
            except:
                # Last resort - try fixing common issues and retry
                fixed_str = filter_str.replace("'", '"')
                try:
                    return json.loads(fixed_str)
                except:
                    raise ValueError(f"Could not parse filter dictionary: {filter_str}")

    # Extract projection dictionary from find() call using regex
    def extract_projection_dict(code):
        # Match find(..., {projection}) pattern
        proj_pattern = r'find\([^{]*({[^}]*})[^{]*,\s*{([^}]*)}\s*\)'
        proj_match = re.search(proj_pattern, code)
        if not proj_match:
            return None
            
        proj_str = proj_match.group(2)
        try:
            # Try parsing as JSON
            return json.loads(proj_str.replace("'", '"'))
        except:
            # Try with ast.literal_eval
            try:
                return ast.literal_eval(proj_str)
            except:
                return None

    # Extract method parameters using regex for cases where ast.literal_eval fails
    def extract_method_params(code, method_name):
        # Look for .method_name({...}) or .method_name([...]) or .method_name(123) pattern
        pattern = fr'\.{method_name}\s*\((.*?)\)(?:\.|\s*$)'
        match = re.search(pattern, code)
        if not match:
            return None
            
        param_str = match.group(1).strip()
        
        # Empty parameter
        if not param_str:
            return None
            
        # Try to handle different parameter types
        try:
            # Simple number?
            if param_str.isdigit():
                return int(param_str)
                
            # JSON object or array?
            try:
                # Handle MongoDB format with double quotes
                return json.loads(param_str.replace("'", '"'))
            except json.JSONDecodeError:
                # If direct JSON parsing fails, try to use ast.literal_eval
                try:
                    return ast.literal_eval(param_str)
                except:
                    # Return as is if all else fails
                    return param_str
        except Exception as e:
            # Return None if all parsing fails
            logger.warning(f"Failed to parse parameter for {method_name}: {e}")
            return None

    # Pre-process the query
    preprocessed_code = preprocess_mongo_syntax(actual_code)
    
    try:
        # Try to use our more robust regex-based parsing first
        filter_dict = extract_filter_dict(preprocessed_code)
        projection = extract_projection_dict(preprocessed_code)
        
        # Handle empty projection
        options = {"projection": projection} if projection else {}
        
        # Extract sort, limit and skip parameters
        sort_param = extract_method_params(preprocessed_code, "sort") 
        if sort_param is not None:
            options["sort"] = sort_param
            
        limit_param = extract_method_params(preprocessed_code, "limit")
        if limit_param is not None:
            options["limit"] = int(limit_param) if isinstance(limit_param, (int, str)) else limit_param
            
        skip_param = extract_method_params(preprocessed_code, "skip")
        if skip_param is not None:
            options["skip"] = int(skip_param) if isinstance(skip_param, (int, str)) else skip_param
        
        # Convert actual filter_dict back to modified
        flat_filter = actual_to_modified_query(filter_dict, out2in)
        
        # Merge projection, sort, limit into modified if relevant
        for key in ("projection", "sort", "skip", "limit"):
            if key in options and options[key] is not None:
                flat_filter[key] = options[key]
                
        # Add original number strings to the result
        flat_filter['_original_numbers'] = original_numbers
        
        return flat_filter
        
    except Exception as e:
        # Fall back to traditional AST-based parsing if regex fails
        try:
            node = ast.parse(preprocessed_code.strip(), mode='eval')
            if not isinstance(node.body, ast.Call) or not hasattr(node.body.func, 'attr') or node.body.func.attr != "find":
                raise ValueError("Expected .find(...) style query")

            # extract find(filter, projection)
            args = node.body.args
            filter_dict = ast.literal_eval(args[0])
            projection = ast.literal_eval(args[1]) if len(args) > 1 else None

            # extract chained methods: sort, skip, limit
            options = {"projection": projection} if projection else {}
            current = node.body
            while isinstance(current, ast.Call):
                func = current.func
                if hasattr(func, "attr"):
                    if func.attr == "sort":
                        options["sort"] = ast.literal_eval(current.args[0])
                    elif func.attr == "skip":
                        options["skip"] = ast.literal_eval(current.args[0])
                    elif func.attr == "limit":
                        options["limit"] = ast.literal_eval(current.args[0])
                current = func.value if hasattr(func, "value") else None

            # Convert actual filter_dict back to modified
            flat_filter = actual_to_modified_query(filter_dict, out2in)

            # Merge projection, sort, limit into modified if relevant
            for key in ("projection", "sort", "skip", "limit"):
                if key in options:
                    flat_filter[key] = options[key]

            return flat_filter
        except Exception as nested_e:
            raise ValueError(f"Failed to parse MongoDB query string: {e}. AST fallback also failed: {nested_e}")
        

# -------------------- Example Usage --------------------
if __name__ == "__main__":
    # Example JSON Schema
    schema = {
      "collections": [{
        "name": "events",
        "document": {
          "properties": {
            "event_id": {"bsonType": "int"},
            "timestamp": {"bsonType": "int"},
            "severity_level": {"bsonType": "int"},
            "camera_id": {"bsonType": "int"},
            "vehicle_details": {"bsonType": "object", "properties": {
              "license_plate_number": {"bsonType": "string"},
              "vehicle_type": {"bsonType": "string"},
              "color": {"bsonType": "string"}
            }},
            "person_details": {"bsonType": "object", "properties": {
              "match_id": {"bsonType": "int"},
              "age": {"bsonType": "int"},
              "gender": {"bsonType": "string"},
              "clothing_description": {"bsonType": "string"}
            }},
            "location": {"bsonType": "object", "properties": {
              "latitude": {"bsonType": "double"},
              "longitude": {"bsonType": "double"}
            }},
            "sensor_readings": {"bsonType": "object", "properties": {
              "temperature": {"bsonType": "double"},
              "speed": {"bsonType": "double"},
              "distance": {"bsonType": "double"}
            }},
            "incident_type": {"bsonType": "string"}
          }
        }
      }],
      "version": 1
    }

    # Build mappings once
    in2out, out2in = build_schema_maps(schema)

    # Flat user input including filters + options
    modified_input = {
        "license_plate_number": {"$regex": "^MH12"},
        "timestamp": {"$gte": 1684080000, "$lte": 1684166400},
        "severity_level": 3,
        "limit": 50,
        "skip": 10,
        "sort": [("timestamp", -1)],
        "projection": {
            "vehicle_details.license_plate_number": 1,
            "timestamp": 1,
            "_id": 0
        }
    }

    # Build actual nested query + options
    filter_dict, opts = build_query_and_options(modified_input.copy(), in2out)

    print("filter_dict =", filter_dict)
    print("options     =", opts)
    # You can then do:
    # cursor = (
    #   db.events.find(filter_dict, opts.get("projection"))
    #                 .sort(opts.get("sort", []))
    #                 .skip(opts.get("skip", 0))
    #                 .limit(opts.get("limit", 0))
    # )