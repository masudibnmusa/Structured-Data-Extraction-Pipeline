"""Load PDFs / images / emails / raw text into a uniform LoadedDocument."""
import hashlib
from dataclasses import dataclass
from email import policy
from email.parser import BytesParser
from pathlib import Path

from app.config import settings
from app.utils.logger import get_logger

log = get_logger(__name__)

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}
TEXT_EXTS = {".txt", ".md"}


@dataclass
class LoadedDocument:
    path: Path
    text: str
    doc_hash: str
    source_type: str  # pdf | image | email | text
    used_ocr: bool = False


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_eml(path: Path) -> str:
    msg = BytesParser(policy=policy.default).parsebytes(path.read_bytes())
    body_part = msg.get_body(preferencelist=("plain", "html"))
    body = body_part.get_content() if body_part else ""
    headers = "\n".join(
        f"{h}: {msg[h]}" for h in ("From", "To", "Cc", "Subject", "Date") if msg[h]
    )
    return f"{headers}\n\n{body}"


def _load_pdf(path: Path) -> tuple[str, bool]:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages = [(p.extract_text() or "") for p in reader.pages]
    text = "\n\n".join(f"--- page {i} ---\n{t}" for i, t in enumerate(pages, 1))
    if sum(len(t.strip()) for t in pages) < settings.min_chars_per_page * max(len(pages), 1):
        from app.ingestion.ocr_processor import ocr_pdf

        log.info("%s has little embedded text; falling back to OCR", path.name)
        return ocr_pdf(path), True
    return text, False


def load_document(path: str | Path) -> LoadedDocument:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    ext = path.suffix.lower()
    doc_hash = file_hash(path)

    if ext in TEXT_EXTS:
        return LoadedDocument(path, path.read_text(errors="replace"), doc_hash, "text")
    if ext == ".eml":
        return LoadedDocument(path, _load_eml(path), doc_hash, "email")
    if ext == ".pdf":
        text, used_ocr = _load_pdf(path)
        return LoadedDocument(path, text, doc_hash, "pdf", used_ocr)
    if ext in IMAGE_EXTS:
        from app.ingestion.ocr_processor import ocr_image

        return LoadedDocument(path, ocr_image(path), doc_hash, "image", True)
    raise ValueError(f"Unsupported file type: {ext}")