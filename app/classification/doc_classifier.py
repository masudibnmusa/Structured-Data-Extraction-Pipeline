"""Detect document type: cheap keyword heuristics first, LLM only when unclear."""
from app.classification.schema_router import DOC_TYPES
from app.extraction.llm_client import get_llm_client
from app.extraction.prompt_templates import CLASSIFIER_PROMPT
from app.utils.logger import get_logger

log = get_logger(__name__)

KEYWORDS = {
    "invoice": ["invoice", "subtotal", "total due", "amount due", "bill to", "due date", "invoice number"],
    "contract": ["agreement", "hereinafter", "witnesseth", "governing law", "indemnif", "terminat", "parties"],
    "email": ["from:", "to:", "subject:", "sent:", "regards", "cc:"],
}

CLASSIFY_SCHEMA = {
    "type": "object",
    "properties": {"doc_type": {"type": "string", "enum": list(DOC_TYPES)}},
    "required": ["doc_type"],
}


def heuristic_scores(text: str) -> dict[str, int]:
    low = text.lower()
    return {t: sum(k in low for k in kws) for t, kws in KEYWORDS.items()}


def classify_document(text: str, client=None) -> str:
    scores = heuristic_scores(text)
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    (best, best_n), (_, second_n) = ranked[0], ranked[1]
    if best_n >= 3 and best_n - second_n >= 2:
        log.info("Classified as %s by heuristics %s", best, scores)
        return best

    client = client or get_llm_client()
    result = client.extract_structured(
        system=CLASSIFIER_PROMPT,
        user=f"<document>\n{text[:6000]}\n</document>",
        tool_name="classify_document",
        json_schema=CLASSIFY_SCHEMA,
        description="Record the document type.",
    )
    doc_type = result.get("doc_type")
    if doc_type not in DOC_TYPES:
        raise ValueError(f"Classifier returned unknown type: {doc_type!r}")
    log.info("Classified as %s by LLM", doc_type)
    return doc_type