"""OCR for scanned PDFs and images. Provider is chosen with OCR_PROVIDER."""
import io
from pathlib import Path

from app.config import settings
from app.utils.logger import get_logger

log = get_logger(__name__)


def _tesseract(img) -> str:
    import pytesseract

    return pytesseract.image_to_string(img)


def _textract(img) -> str:
    import boto3

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    client = boto3.client("textract", region_name=settings.aws_region)
    resp = client.detect_document_text(Document={"Bytes": buf.getvalue()})
    return "\n".join(b["Text"] for b in resp["Blocks"] if b["BlockType"] == "LINE")


def _ocr_pil(img) -> str:
    provider = settings.ocr_provider
    if provider == "tesseract":
        return _tesseract(img)
    if provider == "textract":
        return _textract(img)
    if provider == "document_ai":
        raise NotImplementedError("Add a Google Document AI implementation here.")
    raise ValueError(f"Unknown OCR_PROVIDER: {provider}")


def ocr_image(path: Path) -> str:
    from PIL import Image

    with Image.open(path) as img:
        return _ocr_pil(img)


def ocr_pdf(path: Path) -> str:
    from pdf2image import convert_from_path

    pages = convert_from_path(str(path), dpi=300)
    log.info("OCR on %s (%d pages, provider=%s)", path.name, len(pages), settings.ocr_provider)
    return "\n\n".join(f"--- page {i} ---\n{_ocr_pil(p)}" for i, p in enumerate(pages, 1))