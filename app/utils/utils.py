from datetime import datetime
from bson import ObjectId
from typing import Any, Dict

def to_serializable(data: Any) -> Any:
    """Convert data to JSON serializable format."""
    if isinstance(data, dict):
        return {key: to_serializable(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [to_serializable(item) for item in data]
    elif isinstance(data, datetime):
        return data.isoformat()
    elif isinstance(data, ObjectId):
        return str(data)
    else:
        return data