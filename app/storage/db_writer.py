"""Persist and query extraction records."""
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.storage.models import Record, SessionLocal


class DuplicateDocumentError(Exception):
    pass


def _to_dict(r: Record) -> dict:
    return {c.name: getattr(r, c.name) for c in Record.__table__.columns}


def save_record(**fields) -> dict:
    with SessionLocal() as session:
        record = Record(**fields)
        session.add(record)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            raise DuplicateDocumentError(fields.get("doc_hash"))
        return _to_dict(record)


def get_record(record_id: str) -> dict | None:
    with SessionLocal() as session:
        r = session.get(Record, record_id)
        return _to_dict(r) if r else None


def get_by_hash(doc_hash: str) -> dict | None:
    with SessionLocal() as session:
        r = session.scalar(select(Record).where(Record.doc_hash == doc_hash))
        return _to_dict(r) if r else None


def list_by_status(status: str, limit: int = 100) -> list[dict]:
    with SessionLocal() as session:
        rows = session.scalars(
            select(Record).where(Record.status == status).order_by(Record.created_at).limit(limit)
        ).all()
        return [_to_dict(r) for r in rows]


def update_record(record_id: str, **fields) -> dict:
    with SessionLocal() as session:
        r = session.get(Record, record_id)
        if r is None:
            raise KeyError(record_id)
        for k, v in fields.items():
            setattr(r, k, v)
        session.commit()
        return _to_dict(r)