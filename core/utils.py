from bson import ObjectId
from typing import Any, Dict, List

def to_serializable(doc: Dict[str, Any]) -> Dict[str, Any]:
    for k, v in doc.items():
        if isinstance(v, ObjectId):
            doc[k] = str(v)
        elif isinstance(v, List):
            doc[k] = [str(x) if isinstance(x, ObjectId) else x for x in v]
    return doc