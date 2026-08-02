from sqlalchemy import TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB
from pydantic import BaseModel
from typing import Any

class PydanticType(TypeDecorator):
    """
    Automatically converts Pydantic models to JSONB and back.
    """
    impl = JSONB
    cache_ok = True

    def __init__(self, pydantic_model: type[BaseModel]):
        self.pydantic_model = pydantic_model

    def process_bind_param(self, value: Any, dialect) -> dict:
        if value is not None:
            if isinstance(value, self.pydantic_model):
                return value.model_dump()
            return value
        return None

    def process_result_value(self, value: Any, dialect) -> BaseModel:
        if value is not None:
            return self.pydantic_model.model_validate(value)
        return None