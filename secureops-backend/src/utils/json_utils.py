from datetime import datetime, date
from typing import Any

def make_json_safe(obj: Any) -> Any:
    """
    Recursively convert objects to JSON-serializable formats.
    Handles datetime and date objects by converting them to ISO format strings.
    """
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()

    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}

    if isinstance(obj, list):
        return [make_json_safe(v) for v in obj]
    
    if isinstance(obj, tuple):
        return [make_json_safe(v) for v in obj]

    return obj
