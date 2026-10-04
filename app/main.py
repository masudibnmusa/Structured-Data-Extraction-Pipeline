"""Entry point: FastAPI server + CLI.

CLI:
  python -m app.main init-db
  python -m app.main extract --file data/raw_documents/invoice_001.pdf
  python -m app.main batch --dir data/raw_documents/ [--sync]
  python -m app.main serve
"""
import argparse
import json
import shutil
import uuid
from contextlib import asynccontextmanager
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.config import settings
from app.pipeline.pipeline_runner import process_document
from app.review_queue import queue_manager
from app.storage import db_writer
from app.storage.models import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Extraction Pipeline", lifespan=lifespan)


class ApprovalBody(BaseModel):
    data: dict | None = None
    reviewer: str | None = None


@app.post("/documents")
def upload_document(file: UploadFile = File(...), sync: bool = False):
    dest = settings.raw_dir / f"{uuid.uuid4().hex[:8]}_{Path(file.filename).name}"
    with open(dest, "wb") as out:
        shutil.copyfileobj(file.file, out)

    if sync:
        try:
            return asdict(process_document(dest))
        except ValueError as exc:
            raise HTTPException(422, str(exc))

    from app.pipeline.batch_processor import process_document_task
    task = process_document_task.delay(str(dest))
    return {"task_id": task.id, "status": "queued", "file": dest.name}


@app.get("/documents/{record_id}")
def get_document(record_id: str):
    rec = db_writer.get_record(record_id)
    if rec is None:
        raise HTTPException(404, "Record not found")
    return rec


@app.get("/review")
def list_review():
    return queue_manager.list_pending()


@app.post("/review/{record_id}/approve")
def approve(record_id: str, body: ApprovalBody):
    try:
        return queue_manager.approve(record_id, body.data, body.reviewer)
    except KeyError:
        raise HTTPException(404, "Record not found")
    except ValueError as exc:
        raise HTTPException(422, str(exc))


@app.post("/review/{record_id}/reject")
def reject(record_id: str):
    try:
        return queue_manager.reject(record_id)
    except KeyError:
        raise HTTPException(404, "Record not found")


@app.get("/health")
def health():
    return {"status": "ok"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Structured data extraction pipeline")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init-db")
    p_extract = sub.add_parser("extract")
    p_extract.add_argument("--file", required=True)
    p_batch = sub.add_parser("batch")
    p_batch.add_argument("--dir", required=True)
    p_batch.add_argument("--sync", action="store_true", help="process inline instead of via Celery")
    p_serve = sub.add_parser("serve")
    p_serve.add_argument("--host", default="0.0.0.0")
    p_serve.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    init_db()
    if args.cmd == "init-db":
        print("Database initialised.")
    elif args.cmd == "extract":
        print(json.dumps(asdict(process_document(args.file)), indent=2))
    elif args.cmd == "batch":
        if args.sync:
            for p in sorted(Path(args.dir).iterdir()):
                if p.is_file():
                    try:
                        print(json.dumps(asdict(process_document(p))))
                    except Exception as exc:  # keep the batch going
                        print(json.dumps({"file": p.name, "error": str(exc)}))
        else:
            from app.pipeline.batch_processor import enqueue_directory
            ids = enqueue_directory(args.dir)
            print(f"Queued {len(ids)} documents.")
    elif args.cmd == "serve":
        import uvicorn
        uvicorn.run("app.main:app", host=args.host, port=args.port)


if __name__ == "__main__":
    main()