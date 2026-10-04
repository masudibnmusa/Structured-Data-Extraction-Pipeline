"""Route low-confidence records to humans and apply their decisions."""
import json

from app.classification.schema_router import get_schema
from app.config import settings
from app.storage import db_writer
from app.utils.logger import get_logger
from app.validation.schema_validator import validate_schema

log = get_logger(__name__)


def _queue_file(record_id: str):
    return settings.review_dir / f"{record_id}.json"


def enqueue(record: dict) -> None:
    _queue_file(record["id"]).write_text(json.dumps(record, indent=2, default=str))
    log.info("Record %s queued for review (%d flags)", record["id"], len(record["flags"]))


def list_pending(limit: int = 100) -> list[dict]:
    return db_writer.list_by_status("needs_review", limit)


def approve(record_id: str, corrected_data: dict | None = None, reviewer: str | None = None) -> dict:
    rec = db_writer.get_record(record_id)
    if rec is None:
        raise KeyError(record_id)

    data = corrected_data if corrected_data is not None else rec["data"]
    instance, errors = validate_schema(get_schema(rec["doc_type"]), data)
    if errors:
        raise ValueError("; ".join(errors))
    clean = instance.model_dump(mode="json")

    updated = db_writer.update_record(
        record_id,
        data=clean,
        status="reviewed",
        meta={**rec["meta"], "reviewed_by": reviewer, "corrected": corrected_data is not None},
    )

    # Feedback loop: reviewed records become ground truth for evaluation / few-shot examples.
    (settings.ground_truth_dir / f"{record_id}.json").write_text(json.dumps(
        {"doc_type": rec["doc_type"], "source_text": rec["source_text"], "expected": clean},
        indent=2, default=str))
    _queue_file(record_id).unlink(missing_ok=True)
    return updated


def reject(record_id: str, reason: str | None = None) -> dict:
    rec = db_writer.get_record(record_id)
    if rec is None:
        raise KeyError(record_id)
    updated = db_writer.update_record(
        record_id, status="rejected", meta={**rec["meta"], "reject_reason": reason})
    _queue_file(record_id).unlink(missing_ok=True)
    return updated