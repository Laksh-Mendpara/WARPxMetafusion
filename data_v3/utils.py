from typing import Any, Dict, Tuple, List
from loguru import logger
import json
import re


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
    """
    query: Dict[str, Any] = {}
    for flat_key, val in modified.items():
        if flat_key not in input_to_output:
            continue
        path = input_to_output[flat_key].split('.')
        set_nested(query, path, val)
    return query


def actual_to_modified_query(actual: Dict[str, Any],
                             output_to_input: Dict[str, str]) -> Dict[str, Any]:
    """
    Flatten a nested Mongo query dict back into flat_key -> value/operator.
    Operator-dicts (keys starting with $) are treated as leaves.
    """
    flat: Dict[str, Any] = {}

    def recurse(d: Any, prefix: str = "") -> None:
        # operator-dict leaf
        if isinstance(d, dict) and d and all(k.startswith("$") for k in d):
            if prefix in output_to_input:
                flat[output_to_input[prefix]] = d
            return
        # leaf non-dict
        if not isinstance(d, dict):
            if prefix in output_to_input:
                flat[output_to_input[prefix]] = d
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
    filter_dict, opts = build_query_and_options(modified_input.copy(), in2out)

    # 1) dot-ify the filter dict
    dot_filter = nested_to_dot(filter_dict)
    filter_str = json.dumps(dot_filter, separators=(",", ":"))

    # 2) only include projection if non-empty
    projection = opts.get("projection", {})
    parts = [f"db.{collection_name}.find({filter_str}"
             + (f", {json.dumps(projection, separators=(',', ':'))}" if projection else "")
             + ")"]

    # 3) chain optional methods
    if opts.get("sort"):
        parts.append(f".sort({json.dumps(opts['sort'], separators=(',', ':'))})")
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

    # Parse using AST and extract .find() args
    try:
        node = ast.parse(actual_code.strip(), mode='eval')
        if not isinstance(node.body, ast.Call) or not hasattr(node.body.func, 'attr') or node.body.func.attr != "find":
            raise ValueError("Expected db.<collection>.find(...) style query")

        # extract find(filter, projection)
        args = node.body.args
        filter_dict = ast.literal_eval(args[0])
        projection = ast.literal_eval(args[1]) if len(args) > 1 else {}

        # extract chained methods: sort, skip, limit
        options = {"projection": projection}
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

    except Exception as e:
        raise ValueError(f"Failed to parse MongoDB query string: {e}")


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
