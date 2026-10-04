"""Central configuration, loaded from environment variables / .env."""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))


@dataclass(frozen=True)
class Settings:
    # --- LLM ---
    llm_provider: str = os.getenv("LLM_PROVIDER", "anthropic")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "claude-sonnet-5-5")
    llm_max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "4096"))
    max_input_chars: int = int(os.getenv("MAX_INPUT_CHARS", "60000"))

    # --- OCR ---
    ocr_provider: str = os.getenv("OCR_PROVIDER", "tesseract")  # tesseract | textract | document_ai
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    min_chars_per_page: int = int(os.getenv("MIN_CHARS_PER_PAGE", "40"))

    # --- Storage / queue ---
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'pipeline.db'}")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # --- Pipeline behaviour ---
    confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.85"))
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))

    # --- Email ingestion (IMAP) ---
    imap_host: str = os.getenv("IMAP_HOST", "")
    imap_user: str = os.getenv("IMAP_USER", "")
    imap_password: str = os.getenv("IMAP_PASSWORD", "")
    imap_folder: str = os.getenv("IMAP_FOLDER", "INBOX")

    # --- Paths ---
    raw_dir: Path = DATA_DIR / "raw_documents"
    extracted_dir: Path = DATA_DIR / "extracted"
    review_dir: Path = DATA_DIR / "review_queue"
    schema_dir: Path = DATA_DIR / "schemas"
    ground_truth_dir: Path = DATA_DIR / "ground_truth"


settings = Settings()

for _p in (settings.raw_dir, settings.extracted_dir, settings.review_dir,
           settings.schema_dir, settings.ground_truth_dir):
    _p.mkdir(parents=True, exist_ok=True)