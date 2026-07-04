from pydantic import BaseModel
from sqlalchemy import TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB

class PydanticJSONB(TypeDecorator):
    impl = JSONB
    cache_ok = True

    def __init__(self, pydantic_model: type[BaseModel]):
        super().__init__()
        self.pydantic_model = pydantic_model

    def process_bind_param(self, value, dialect):
        """Convert Pydantic model to a raw Python dict before sending to Postgres."""
        if value is None:
            return None
        if isinstance(value, self.pydantic_model):
            return value.model_dump()
        return value

    def process_result_value(self, value, dialect):
        """Convert raw Postgres JSONB data back into a typed Pydantic model on load."""
        if value is None:
            return None
        return self.pydantic_model.model_validate(value)