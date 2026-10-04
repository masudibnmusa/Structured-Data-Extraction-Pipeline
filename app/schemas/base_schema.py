"""Shared schema pieces."""
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

SCHEMA_VERSION = "1.0"

# 3-letter ISO 4217 code, normalised to upper-case
Currency = Annotated[str, StringConstraints(min_length=3, max_length=3, to_upper=True)]


class BaseExtraction(BaseModel):
    """Parent class for every document schema."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)