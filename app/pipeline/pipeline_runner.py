"""Orchestrates the full flow for one document."""
import json
from dataclasses import dataclass, field
from pathlib import Path

from app.classification.doc_classifier import classify_document
from app.classification.schema_router import route
from app.config import settings
from app.extraction.extractor import extract
from app.extraction.prompt_templates import PROMPT_VERSION
from app.ingestion.document_loader import load_document
from app.review_queue.queue_manager import enqueue
from app.schemas.base_schema import SCHEMA_VERSION
from app.storage.db_writer import DuplicateDocumentError, get_by_hash, save_record
from app.utils.logger import get_logger
from app.validation.business_rule_validator import validate_business_rules
from app.validation.confidence_scorer import score_confidence
from app.validation.schema_validator import validate_schema

log = get_logger(__name__)


@dataclass
class PipelineResult:
    record_id: str
    status: str
    doc_type: str
    confidence: float
    flags: list[str] = field(default_factory=list)
    duplicate: bool = False


def _from_existing(rec: dict) -> PipelineResult:
    return PipelineResult(rec["id"], rec["status"], rec["doc_type"],
                          rec["confidence"], rec["flags"], duplicate=True)


def process_document(path: str | Path, client=None) -> PipelineResult:
    path = Path(path)
    doc = load_document(path)
    if not doc.text.strip():
        raise ValueError(f"No text could be extracted from {path.name}")

    # Idempotency: the same file is never processed twice.
    if existing := get_by_hash(doc.doc_hash):
        log.info("Duplicate document %s -> record %s", path.name, existing["id"])
        return _from_existing(existing)

    doc_type = classify_document(doc.text, client)
    schema_cls, _ = route(doc_type)
    raw = extract(doc.text, doc_type, client)

    instance, schema_errors = validate_schema(schema_cls, raw)
    issues = validate_business_rules(doc_type, instance) if instance else []
    report = score_confidence(raw, doc.text, issues, schema_errors)

    flags = ([f"schema:{e}" for e in schema_errors]
             + [f"rule:{i}" for i in issues] + report.flags)
    needs_review = bool(schema_errors) or report.score < settings.confidence_threshold
    status = "needs_review" if needs_review else "accepted"

    try:
        record = save_record(
            doc_hash=doc.doc_hash,
            source_path=str(path),
            doc_type=doc_type,
            status=status,
            confidence=report.score,
            data=instance.model_dump(mode="json") if instance else raw,
            flags=flags,
            meta={
                "schema_version": SCHEMA_VERSION,
                "prompt_version": PROMPT_VERSION,
                "model": settings.llm_model,
                "source_type": doc.source_type,
                "used_ocr": doc.used_ocr,
                "grounded_ratio": report.grounded_ratio,
            },
            source_text=doc.text,
        )
    except DuplicateDocumentError:  # lost a race with another worker
        return _from_existing(get_by_hash(doc.doc_hash))

    if needs_review:
        enqueue(record)
    else:
        (settings.extracted_dir / f"{record['id']}.json").write_text(
            json.dumps(record, indent=2, default=str))

    log.info("Processed %s -> %s (%s, confidence %.2f)", path.name, status, doc_type, report.score)
    return PipelineResult(record["id"], status, doc_type, report.score, flags)