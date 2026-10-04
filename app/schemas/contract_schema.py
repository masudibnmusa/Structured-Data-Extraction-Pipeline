from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.base_schema import BaseExtraction, Currency


class Party(BaseModel):
    name: str
    role: str | None = Field(default=None, description="e.g. Client, Supplier, Licensor")


class Contract(BaseExtraction):
    title: str
    parties: list[Party] = Field(min_length=2)
    effective_date: date | None = Field(default=None, description="ISO 8601 date")
    end_date: date | None = Field(default=None, description="ISO 8601 date")
    governing_law: str | None = None
    payment_terms: str | None = None
    termination_summary: str | None = Field(default=None, description="One or two sentences")
    auto_renewal: bool | None = None
    contract_value: Decimal | None = None
    currency: Currency | None = None