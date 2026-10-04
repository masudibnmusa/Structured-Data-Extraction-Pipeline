"""Queue-based processing at scale using Celery + Redis.

Start a worker with:  celery -A app.pipeline.batch_processor.celery_app worker --loglevel=info
"""
from dataclasses import asdict
from pathlib import Path

from celery import Celery

from app.config import settings
from app.pipeline.pipeline_runner import process_document
from app.storage.models import init_db

celery_app = Celery("extraction", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_acks_late=True,               # re-deliver if a worker dies mid-task
    worker_prefetch_multiplier=1,      # LLM calls are slow; don't hoard tasks
    task_track_started=True,
)

SUPPORTED = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".txt", ".md", ".eml"}


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    dont_autoretry_for=(ValueError, FileNotFoundError),  # permanent failures
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    retry_kwargs={"max_retries": settings.max_retries},
)
def process_document_task(self, path: str) -> dict:
    init_db()
    return asdict(process_document(path))


def enqueue_directory(directory: str | Path) -> list[str]:
    paths = sorted(p for p in Path(directory).iterdir()
                   if p.is_file() and p.suffix.lower() in SUPPORTED)
    return [process_document_task.delay(str(p)).id for p in paths]