from bson.errors import InvalidId
from bson.objectid import ObjectId


def validate_object_id(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        raise ValueError("Invalid ObjectId format.")
