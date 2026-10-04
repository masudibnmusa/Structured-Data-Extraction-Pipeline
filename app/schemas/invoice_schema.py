from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.base_schema import BaseExtraction, Currency


class LineItem(BaseModel):
    description: str
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal


class Invoice(BaseExtraction):
    vendor_name: str = Field(description="Company issuing the invoice")
    invoice_number: str
    invoice_date: date = Field(description="ISO 8601 date, YYYY-MM-DD")
    due_date: date | None = Field(default=None, description="ISO 8601 date, YYYY-MM-DD")
    currency: Currency = Field(description="3-letter ISO 4217 code, e.g. USD")
    line_items: list[LineItem] = Field(min_length=1)
    subtotal: Decimal
    tax: Decimal = Decimal("0")
    total: Decimal