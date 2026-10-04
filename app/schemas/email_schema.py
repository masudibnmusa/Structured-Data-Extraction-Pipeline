from datetime import datetime
from typing import Literal

from pydantic import Field

from app.schemas.base_schema import BaseExtraction


class EmailRecord(BaseExtraction):
    sender: str
    recipients: list[str] = Field(default_factory=list)
    cc: list[str] = Field(default_factory=list)
    subject: str
    sent_at: datetime | None = Field(default=None, description="ISO 8601 datetime")
    summary: str = Field(description="One or two sentence summary")
    category: Literal["inquiry", "complaint", "order", "invoice", "support", "other"]
    action_items: list[str] = Field(default_factory=list)
    requires_response: bool