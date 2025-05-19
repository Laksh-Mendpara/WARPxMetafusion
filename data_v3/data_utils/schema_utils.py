from typing import Dict, Any


def schema_to_line_based(schema: dict) -> str:
    """
    Converts a schema dictionary to a line-based format:
    field  // description and format (str, int, ...)
    Only shows field names without parent prefix (e.g. 'age' instead of 'involved_persons.age')
    """
    def get_type(info):
        return info.get("bsonType") or info.get("type") or ""

    def process_properties(properties: dict) -> list:
        lines = []
        for field, info in properties.items():
            typ = get_type(info)
            desc = info.get("description", "")
            fmt = info.get("format", "")
            
            # Compose type/format string
            type_fmt = typ
            if fmt:
                type_fmt += f", {fmt}"
                
            # Compose comment
            comment = desc.strip()
            if type_fmt:
                comment = f"{comment} ({type_fmt})" if comment else f"({type_fmt})"
                
            lines.append(f"{field}  // {comment}" if comment else field)
            
            # Recursively process nested objects and arrays, but only add the field names without prefix
            if typ == "object" and "properties" in info:
                for nested_line in process_properties(info["properties"]):
                    lines.append(nested_line)
            elif typ == "array" and "items" in info:
                items = info["items"]
                if get_type(items) == "object" and "properties" in items:
                    for nested_line in process_properties(items["properties"]):
                        lines.append(nested_line)
                    
        return lines

    collections = schema.get("collections", [])
    if not collections:
        return ""
    collection = collections[0]
    # Support both "document" and direct "properties"
    if "document" in collection and "properties" in collection["document"]:
        properties = collection["document"]["properties"]
    else:
        properties = collection.get("properties", {})
    return "\n".join(process_properties(properties))
