from pydantic import field_validator

class ReviewValidatorMixin:
    @field_validator('user_id')
    @classmethod
    def user_id_required(cls, v):
        if not v or not v.strip():
            raise ValueError('User ID is required for a review (anonymous reviews are not allowed)')
        return v

    @field_validator('username')
    @classmethod
    def username_required(cls, v):
        if not v or not v.strip():
            raise ValueError('Username is required for a review (anonymous reviews are not allowed)')
        return v

    @field_validator('rating')
    @classmethod
    def rating_valid(cls, v):
        if v is not None and (v < 1 or v > 5):
            raise ValueError('Rating must be between 1 and 5')
        return v

    @field_validator('comment')
    @classmethod
    def comment_valid(cls, v):
        if v is not None and len(v) > 1000:
            raise ValueError('Comment can be up to 1000 characters')
        return v
