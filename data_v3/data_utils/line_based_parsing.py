from typing import Dict, Any
import ast

from typing import Any, Dict

def clean_modified_dict(modified_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Cleans the modified dictionary by removing only values that are:
    - None
    - empty list []
    - empty dict {}
    - empty string ''
    But keeps values like 0, False, etc.
    """
    def is_meaningfully_empty(value):
        return value in (None, '', []) or (isinstance(value, dict) and not value)

    return {k: v for k, v in modified_dict.items() if not is_meaningfully_empty(v)}



def convert_to_lines(query_dict):
    lines = []
    for field, condition in query_dict.items():
        if isinstance(condition, dict):
            for operator, value in condition.items():
                # Special handling for $ne with '' or []
                if operator in ['$ne', 'ne']:
                    if value == '':
                        value_str = "''"
                    elif value == []:
                        value_str = '[]'
                    elif isinstance(value, list):
                        value_str = ','.join(map(str, value))
                    elif isinstance(value, str):
                        value_str = f"'{value}'"
                    else:
                        value_str = str(int(value) if isinstance(value, float) and value.is_integer() else value)
                elif isinstance(value, list):
                    # Output lists as valid Python lists for complex cases
                    value_str = repr(value)
                elif isinstance(value, str):
                    value_str = f"'{value}'"
                else:
                    value_str = str(int(value) if isinstance(value, float) and value.is_integer() else value)
                lines.append(f"{field} {operator} {value_str}")
        else:
            if isinstance(condition, str):
                condition_str = f"'{condition}'"
            else:
                condition_str = str(condition)
            lines.append(f"{field} = {condition_str}")
    return '\n'.join(lines)


def parse_line_based_query(lines):
    query = {}
    for line in lines.strip().split('\n'):
        if not line.strip():
            continue
        parts = line.split(maxsplit=2)
        if len(parts) < 3:
            # If operator is present but value is empty, set value to empty string
            if len(parts) == 2:
                field, operator = parts
                value = ''
            else:
                continue  # Skip invalid lines
        else:
            field, operator, value = parts

        # Special handling for sort, limit, skip, etc.
        if field in {"sort", "order_by"}:
            # Handle both 'sort field value' and 'sort = {field: value}'
            if operator == "=":
                query[field] = _convert_value(value)
            else:
                if field not in query:
                    query[field] = {}
                query[field][operator] = _convert_value(value)
            continue
        if field in {"limit", "skip", "offset"}:
            query[field] = _convert_value(value)
            continue
        # Special handling for _original_numbers (parse value as string if quoted, else as number)
        if field == "_original_numbers":
            if field not in query:
                query[field] = {}
            v = value.strip()
            if (v.startswith("'") and v.endswith("'")) or (v.startswith('"') and v.endswith('"')):
                query[field][operator] = v[1:-1]
            else:
                try:
                    # Try to parse as int or float
                    query[field][operator] = int(v)
                except ValueError:
                    try:
                        query[field][operator] = float(v)
                    except ValueError:
                        query[field][operator] = v
            continue

        # Handle equality operator
        if operator == "=":
            query[field] = _convert_value(value)
            continue

        # Handle other operators
        # If operator is $in, $nin, $all and value is empty, use []
        empty_list_ops = {'in', '$in', 'nin', '$nin', 'all', '$all'}
        op_key = operator if operator.startswith('$') else f'${operator}'
        if operator in empty_list_ops and value == '':
            value_obj = []
        elif operator in {'ne', '$ne'}:
            if value.strip() == '[]':
                value_obj = []
            elif value.strip() == "''" or value.strip() == '""':
                value_obj = ''
            elif value == '':
                value_obj = []
            else:
                value_obj = _convert_value(value, operator)
        else:
            value_obj = _convert_value(value, operator)
        if field in query:
            if isinstance(query[field], dict):
                query[field][op_key] = value_obj
            else:
                raise ValueError(f"Conflict in {field}: direct value and operator")
        else:
            query[field] = {op_key: value_obj}
    return query

def _convert_value(value_str, operator=None):
    """Convert string values to appropriate types"""
    # Handle lists for $in and $all operators
    if operator in ('in', '$in', 'all', '$all'):
        s = value_str.strip()
        if s.startswith('[') and s.endswith(']'):
            try:
                return ast.literal_eval(s)
            except Exception:
                pass
        if ',' in value_str:
            return [_parse_single_value(v) for v in value_str.split(',')]
    
    # Handle regex flags (e.g., "pattern i" → "pattern" with $options: 'i')
    if operator == 'regex' and ' ' in value_str:
        pattern, *flags = value_str.split()
        return {'$regex': pattern, '$options': ''.join(flags)}
    
    return _parse_single_value(value_str)

def _parse_single_value(s):
    """Convert individual values to int/float/string/dict/bool"""
    s = s.strip()
    # Remove surrounding quotes if present
    if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
        return s[1:-1].strip()  # Always return as string if quoted
    # Handle None
    if s == 'None':
        return None
    # Try to parse as dict if it looks like one
    if (s.startswith('{') and s.endswith('}')) or (s.startswith('[') and s.endswith(']')):
        try:
            return ast.literal_eval(s)
        except Exception:
            pass
    # Handle booleans
    if s.lower() == 'true':
        return True
    if s.lower() == 'false':
        return False
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return s
