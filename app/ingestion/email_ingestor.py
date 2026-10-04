"""Pull unread emails from an IMAP inbox and save them as .eml files."""
import hashlib
import imaplib
from pathlib import Path

from app.config import settings
from app.utils.logger import get_logger

log = get_logger(__name__)


def fetch_unseen(limit: int = 50) -> list[Path]:
    if not (settings.imap_host and settings.imap_user):
        raise RuntimeError("Set IMAP_HOST, IMAP_USER and IMAP_PASSWORD in .env")

    saved: list[Path] = []
    with imaplib.IMAP4_SSL(settings.imap_host) as imap:
        imap.login(settings.imap_user, settings.imap_password)
        imap.select(settings.imap_folder)
        _, data = imap.search(None, "UNSEEN")
        for num in data[0].split()[:limit]:
            _, msg_data = imap.fetch(num, "(RFC822)")
            raw = msg_data[0][1]
            path = settings.raw_dir / f"email_{hashlib.sha256(raw).hexdigest()[:16]}.eml"
            if not path.exists():
                path.write_bytes(raw)
            saved.append(path)
    log.info("Fetched %d new emails", len(saved))
    return saved