"""Type / required-field validation using Pydantic."""
from pydantic import BaseModel, ValidationError


def validate_schema(model_cls: type[BaseModel], data: dict) -> tuple[BaseModel | None, list[str]]:
    try:
        return model_cls.model_validate(data), []
    except ValidationError as exc:
        errors = [f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()]
        return None, errors