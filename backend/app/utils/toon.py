"""
TOON (Token Oriented Object Notation) utilities.

TOON is a compact serialization format designed to reduce token usage
when communicating with LLMs. It achieves ~30-50% token savings compared
to JSON by:
- Using single-character delimiters instead of JSON syntax
- Omitting quotes around strings where possible
- Using compact representations for common patterns

Format specification:
- Objects: key:value pairs separated by |
- Arrays: values separated by ;
- Nested objects: enclosed in {}
- Nested arrays: enclosed in []
- Strings with special chars: enclosed in ""
- Numbers, booleans, null: as-is

Example:
JSON: {"name": "Dell Laptop", "price": 1299.99, "quantity": 5}
TOON: name:Dell Laptop|price:1299.99|quantity:5
"""

import json
import re
from typing import Any, Dict, List, Union


# Characters that require quoting in TOON strings
SPECIAL_CHARS = set('|:;{}[]"\n\r\t')


def needs_quoting(value: str) -> bool:
    """Check if a string value needs to be quoted in TOON format."""
    if not value:
        return True
    return any(c in SPECIAL_CHARS for c in value)


def quote_string(value: str) -> str:
    """Quote a string for TOON format, escaping internal quotes."""
    escaped = value.replace('\\', '\\\\').replace('"', '\\"')
    return f'"{escaped}"'


def unquote_string(value: str) -> str:
    """Remove quotes and unescape a TOON string."""
    if value.startswith('"') and value.endswith('"'):
        inner = value[1:-1]
        return inner.replace('\\"', '"').replace('\\\\', '\\')
    return value


def encode_value(value: Any) -> str:
    """Encode a Python value to TOON format."""
    if value is None:
        return "null"
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, str):
        if needs_quoting(value):
            return quote_string(value)
        return value
    elif isinstance(value, dict):
        return "{" + dict_to_toon(value) + "}"
    elif isinstance(value, (list, tuple)):
        return "[" + list_to_toon(value) + "]"
    else:
        # Fallback: convert to string
        str_val = str(value)
        if needs_quoting(str_val):
            return quote_string(str_val)
        return str_val


def dict_to_toon(data: Dict[str, Any]) -> str:
    """Convert a dictionary to TOON format (without outer braces)."""
    pairs = []
    for key, value in data.items():
        encoded_value = encode_value(value)
        pairs.append(f"{key}:{encoded_value}")
    return "|".join(pairs)


def list_to_toon(data: List[Any]) -> str:
    """Convert a list to TOON format (without outer brackets)."""
    return ";".join(encode_value(item) for item in data)


def json_to_toon(data: Union[Dict, List, str]) -> str:
    """
    Convert JSON data to TOON format.

    Args:
        data: Either a Python dict/list or a JSON string

    Returns:
        TOON formatted string

    Example:
        >>> json_to_toon({"vendor": "Dell", "items": [{"name": "Laptop", "price": 999}]})
        'vendor:Dell|items:[{name:Laptop|price:999}]'
    """
    if isinstance(data, str):
        data = json.loads(data)

    if isinstance(data, dict):
        return dict_to_toon(data)
    elif isinstance(data, list):
        return list_to_toon(data)
    else:
        return encode_value(data)


def decode_value(value: str) -> Any:
    """Decode a TOON value to Python type."""
    value = value.strip()

    if not value:
        return ""

    # Null
    if value == "null":
        return None

    # Boolean
    if value == "true":
        return True
    if value == "false":
        return False

    # Quoted string
    if value.startswith('"') and value.endswith('"'):
        return unquote_string(value)

    # Nested object
    if value.startswith('{') and value.endswith('}'):
        return toon_to_dict(value[1:-1])

    # Nested array
    if value.startswith('[') and value.endswith(']'):
        return toon_to_list(value[1:-1])

    # Try to parse as number
    try:
        if '.' in value:
            return float(value)
        return int(value)
    except ValueError:
        pass

    # Plain string
    return value


def split_toon_pairs(toon_str: str, delimiter: str) -> List[str]:
    """
    Split a TOON string by delimiter, respecting nested structures and quotes.
    """
    parts = []
    current = []
    depth_brace = 0
    depth_bracket = 0
    in_quotes = False
    escape_next = False

    for char in toon_str:
        if escape_next:
            current.append(char)
            escape_next = False
            continue

        if char == '\\':
            current.append(char)
            escape_next = True
            continue

        if char == '"' and not escape_next:
            in_quotes = not in_quotes
            current.append(char)
            continue

        if in_quotes:
            current.append(char)
            continue

        if char == '{':
            depth_brace += 1
            current.append(char)
        elif char == '}':
            depth_brace -= 1
            current.append(char)
        elif char == '[':
            depth_bracket += 1
            current.append(char)
        elif char == ']':
            depth_bracket -= 1
            current.append(char)
        elif char == delimiter and depth_brace == 0 and depth_bracket == 0:
            parts.append(''.join(current))
            current = []
        else:
            current.append(char)

    if current:
        parts.append(''.join(current))

    return parts


def toon_to_dict(toon_str: str) -> Dict[str, Any]:
    """Convert TOON format to a dictionary."""
    if not toon_str.strip():
        return {}

    result = {}
    pairs = split_toon_pairs(toon_str, '|')

    for pair in pairs:
        if ':' not in pair:
            continue
        # Split on first colon only (value may contain colons)
        key, _, value = pair.partition(':')
        key = key.strip()
        if key:
            result[key] = decode_value(value)

    return result


def toon_to_list(toon_str: str) -> List[Any]:
    """Convert TOON array format to a list."""
    if not toon_str.strip():
        return []

    items = split_toon_pairs(toon_str, ';')
    return [decode_value(item) for item in items if item.strip()]


def toon_to_json(toon_str: str) -> Union[Dict, List]:
    """
    Convert TOON format to Python dict/list (JSON-compatible).

    Args:
        toon_str: TOON formatted string

    Returns:
        Python dict or list

    Example:
        >>> toon_to_json('vendor:Dell|items:[{name:Laptop|price:999}]')
        {'vendor': 'Dell', 'items': [{'name': 'Laptop', 'price': 999}]}
    """
    toon_str = toon_str.strip()

    # Check if it's an array at top level
    if toon_str.startswith('[') and toon_str.endswith(']'):
        return toon_to_list(toon_str[1:-1])

    # Check if it's an object with braces
    if toon_str.startswith('{') and toon_str.endswith('}'):
        return toon_to_dict(toon_str[1:-1])

    # Default: treat as object without braces
    return toon_to_dict(toon_str)


def estimate_token_savings(json_data: Union[Dict, List, str]) -> Dict[str, Any]:
    """
    Estimate token savings when using TOON vs JSON format.

    Args:
        json_data: JSON data (dict, list, or JSON string)

    Returns:
        Dict with json_chars, toon_chars, savings_percent, and estimated_tokens
    """
    if isinstance(json_data, str):
        json_str = json_data
        data = json.loads(json_data)
    else:
        json_str = json.dumps(json_data)
        data = json_data

    toon_str = json_to_toon(data)

    json_chars = len(json_str)
    toon_chars = len(toon_str)
    savings_percent = ((json_chars - toon_chars) / json_chars * 100) if json_chars > 0 else 0

    # Rough token estimate (1 token ≈ 4 chars for English text)
    json_tokens_est = json_chars / 4
    toon_tokens_est = toon_chars / 4

    return {
        "json_chars": json_chars,
        "toon_chars": toon_chars,
        "savings_percent": round(savings_percent, 1),
        "json_tokens_est": round(json_tokens_est),
        "toon_tokens_est": round(toon_tokens_est),
        "tokens_saved_est": round(json_tokens_est - toon_tokens_est),
    }
