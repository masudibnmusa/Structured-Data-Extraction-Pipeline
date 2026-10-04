"""Run LLM extraction for a document of a known type."""
from app.config import settings
from app.classification.schema_router import route
from app.extraction.llm_client import get_llm_client
from app.utils.logger import get_logger

log = get_logger(__name__)


def extract(text: str, doc_type: str, client=None) -> dict:
    schema_cls, prompt = route(doc_type)
    client = client or get_llm_client()

    if len(text) > settings.max_input_chars:
        log.warning("Document truncated from %d to %d chars", len(text), settings.max_input_chars)
        text = text[: settings.max_input_chars]

    return client.extract_structured(
        system=prompt,
        user=f"<document>\n{text}\n</document>",
        tool_name=f"record_{doc_type}",
        json_schema=schema_cls.model_json_schema(),
        description=f"Record the structured data extracted from the {doc_type}.",
    )