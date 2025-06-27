from bson.objectid import ObjectId
from bson.errors import InvalidId

def validate_object_id(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        raise ValueError("Invalid ObjectId format.")
