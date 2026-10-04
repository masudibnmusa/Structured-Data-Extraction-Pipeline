"""Map a document type to its Pydantic schema and prompt."""
from app.extraction.prompt_templates import PROMPTS
from app.schemas.base_schema import BaseExtraction
from app.schemas.contract_schema import Contract
from app.schemas.email_schema import EmailRecord
from app.schemas.invoice_schema import Invoice

SCHEMA_REGISTRY: dict[str, type[BaseExtraction]] = {
    "invoice": Invoice,
    "contract": Contract,
    "email": EmailRecord,
}
DOC_TYPES = tuple(SCHEMA_REGISTRY)


def get_schema(doc_type: str) -> type[BaseExtraction]:
    try:
        return SCHEMA_REGISTRY[doc_type]
    except KeyError:
        raise ValueError(f"Unknown document type: {doc_type!r}. Known: {DOC_TYPES}")


def route(doc_type: str) -> tuple[type[BaseExtraction], str]:
    return get_schema(doc_type), PROMPTS[doc_type]