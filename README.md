# Structured Data Extraction Pipeline

Turn messy, unstructured documents (invoices, emails, contracts) into clean, validated, structured JSON, reliably and at scale.

This project is not just "call an LLM with a prompt." It is a production-style pipeline built around **reliability**: strict schemas, validation, confidence scoring, human review for uncertain results, and asynchronous batch processing with retries.

---

## Overview

Real-world documents are inconsistent: different layouts, OCR noise, missing fields, multiple formats. This pipeline ingests them from multiple sources and extracts data into a **strict JSON schema per document type**.

**Core idea:**

> Define a strict schema per document type → classify incoming documents → extract fields via LLM structured output → validate against the schema → flag low-confidence extractions for human review → store clean results.

---

## Key Features

- **Multi-source ingestion**: file upload, email inbox (IMAP/API), REST API, raw text
- **OCR support**: Tesseract, AWS Textract, or Google Document AI for scanned docs and images
- **Document classification**: automatically detects invoice, contract, or email and routes to the right schema and prompt
- **Schema-enforced extraction**: LLM structured output / function calling, not free-text parsing
- **Layered validation**: type checks, required fields, value ranges, and cross-field business rules (e.g., line items must sum to total)
- **Confidence scoring**: flags uncertain, missing, or inconsistent fields
- **Human review queue**: low-confidence records go to reviewers instead of silently entering the database
- **Async batch processing**: queue-based workers with retries for transient failures and malformed JSON
- **Containerized**: one `docker-compose` file for the app, Redis, and the database

---

## How It Works

1. **Ingestion**: accept PDFs, scanned images, emails, and raw text
2. **OCR (if needed)**: scanned documents are converted to text
3. **Classification**: detect document type (invoice, contract, email)
4. **Schema selection**: map the document type to its schema and prompt
5. **Extraction**: LLM call with structured output to produce schema-conformant JSON
6. **Validation**: schema checks, then business-rule checks
7. **Confidence scoring**: flag fields that are uncertain, missing, or inconsistent
8. **Routing**: high-confidence results go to storage; low-confidence go to human review
9. **Storage**: validated records are saved to the database
10. **Scaling**: Celery/RQ workers process documents asynchronously with retries

---

## Architecture & Data Flow

```
Raw document (PDF / image / email)
            │
            ▼
   ocr_processor.py            (only if scanned)
            │
            ▼
   doc_classifier.py ──► schema_router.py     (pick schema + prompt)
            │
            ▼
   extractor.py                (LLM structured output → JSON)
            │
            ▼
   schema_validator.py ──► business_rule_validator.py
            │
            ▼
   confidence_scorer.py
            │
     ┌──────┴───────────────┐
     │                      │
high confidence        low confidence
     │                      │
     ▼                      ▼
db_writer.py        review_queue ──► human review ──► db_writer.py
```

---

## Project Structure

```
extraction-pipeline/
│
├── app/
│   ├── __init__.py
│   ├── main.py                        # Entry point (API server / batch runner)
│   ├── config.py                      # API keys, schema paths, confidence thresholds
│   │
│   ├── ingestion/
│   │   ├── document_loader.py         # Load PDFs/images/emails/raw text
│   │   ├── ocr_processor.py           # OCR for scanned docs (Textract/Document AI)
│   │   └── email_ingestor.py          # Pull from email inbox (IMAP/API)
│   │
│   ├── classification/
│   │   ├── doc_classifier.py          # Detect document type
│   │   └── schema_router.py           # Map doc type -> schema/prompt
│   │
│   ├── schemas/
│   │   ├── base_schema.py             # Shared fields/validators
│   │   ├── invoice_schema.py          # Invoice schema
│   │   ├── contract_schema.py         # Contract schema
│   │   └── email_schema.py            # Email schema
│   │
│   ├── extraction/
│   │   ├── extractor.py               # LLM call w/ structured output
│   │   ├── prompt_templates.py        # Per-schema extraction prompts
│   │   └── llm_client.py              # Claude/GPT API wrapper
│   │
│   ├── validation/
│   │   ├── schema_validator.py        # Type/required-field checks (Pydantic)
│   │   ├── business_rule_validator.py # Cross-field checks
│   │   └── confidence_scorer.py       # Flag uncertain/missing fields
│   │
│   ├── review_queue/
│   │   ├── queue_manager.py           # Route low-confidence records
│   │   └── review_ui.py               # Interface to approve/correct extractions
│   │
│   ├── storage/
│   │   ├── db_writer.py               # Save validated records
│   │   └── models.py                  # DB models (SQLAlchemy)
│   │
│   ├── pipeline/
│   │   ├── pipeline_runner.py         # Orchestrates full flow per document
│   │   └── batch_processor.py         # Queue-based processing (Celery/RQ)
│   │
│   └── utils/
│       ├── retry_handler.py           # Retry failed LLM calls / malformed JSON
│       └── logger.py
│
├── data/
│   ├── raw_documents/                 # Incoming docs
│   ├── extracted/                     # Clean JSON outputs
│   ├── review_queue/                  # Flagged records awaiting review
│   └── schemas/                       # Schema definition files
│
├── tests/
│   ├── test_doc_classifier.py
│   ├── test_extractor.py
│   ├── test_schema_validator.py
│   ├── test_business_rule_validator.py
│   └── test_pipeline_runner.py
│
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── docker-compose.yml                 # App + Redis + DB
├── README.md
└── run.sh
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| LLM | Claude / GPT (structured output, function calling) |
| Schemas & validation | Pydantic |
| OCR | Tesseract, AWS Textract, Google Document AI |
| API server | FastAPI |
| Queue / workers | Celery or RQ with Redis |
| Database | PostgreSQL via SQLAlchemy |
| Review UI | Streamlit or FastAPI + lightweight frontend |
| Containers | Docker, Docker Compose |
| Testing | pytest |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- An LLM API key (Anthropic or OpenAI)
- (Optional) AWS or Google Cloud credentials for managed OCR

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/masudibnmusa/Structured-Data-Extraction-Pipeline.git
cd extraction-pipeline

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# then edit .env with your keys
```

### Run with Docker

```bash
docker-compose up --build
```

This starts the API server, a Redis queue, a worker, and the database.

---

## Configuration

Set these in `.env` (see `.env.example`):

| Variable | Description | Example |
|---|---|---|
| `LLM_PROVIDER` | LLM provider to use | `anthropic` |
| `LLM_API_KEY` | API key for the provider | `sk-...` |
| `LLM_MODEL` | Model used for extraction | `your-model-name` |
| `OCR_PROVIDER` | `tesseract`, `textract`, or `document_ai` | `tesseract` |
| `DATABASE_URL` | Database connection string | `postgresql://user:pass@db:5432/extraction` |
| `REDIS_URL` | Queue broker | `redis://redis:6379/0` |
| `CONFIDENCE_THRESHOLD` | Minimum score to auto-accept | `0.85` |
| `MAX_RETRIES` | Retries for failed LLM calls | `3` |

---

## Usage

### Process a single document (CLI)

```bash
python -m app.main extract --file data/raw_documents/invoice_001.pdf
```

### Process a batch

```bash
python -m app.main batch --dir data/raw_documents/
```

### Via the API

```bash
curl -X POST http://localhost:8000/documents \
  -F "file=@data/raw_documents/invoice_001.pdf"
```

```bash
# Check status / fetch result
curl http://localhost:8000/documents/<document_id>
```

### Launch the review UI

```bash
streamlit run app/review_queue/review_ui.py
```

> The commands above show the intended interface. Adjust them to match your actual entry points as you build.

---

## Example Schema & Output

### Invoice schema (Pydantic)

```python
from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field

class LineItem(BaseModel):
    description: str
    quantity: Decimal = Field(ge=0)
    unit_price: Decimal = Field(ge=0)
    amount: Decimal = Field(ge=0)

class Invoice(BaseModel):
    vendor_name: str
    invoice_number: str
    invoice_date: date
    due_date: date | None = None
    currency: str = Field(min_length=3, max_length=3)
    line_items: list[LineItem]
    subtotal: Decimal
    tax: Decimal = Decimal("0")
    total: Decimal
```

### Example output

```json
{
  "document_id": "a3f9c2e1",
  "document_type": "invoice",
  "status": "accepted",
  "confidence": 0.94,
  "data": {
    "vendor_name": "Acme Supplies Ltd.",
    "invoice_number": "INV-2025-0412",
    "invoice_date": "2025-03-14",
    "due_date": "2025-04-13",
    "currency": "USD",
    "line_items": [
      { "description": "Widget A", "quantity": 10, "unit_price": 25.00, "amount": 250.00 },
      { "description": "Widget B", "quantity": 4, "unit_price": 12.50, "amount": 50.00 }
    ],
    "subtotal": 300.00,
    "tax": 24.00,
    "total": 324.00
  },
  "flags": [],
  "meta": {
    "schema_version": "1.0",
    "prompt_version": "invoice_v1",
    "model": "your-model-name"
  }
}
```

---

## Validation & Confidence Scoring

Validation happens in layers:

1. **Schema validation**: types, required fields, formats (Pydantic)
2. **Business rules**: cross-field checks, for example:
   - Line item amounts sum to the subtotal
   - `subtotal + tax = total`
   - `due_date` is on or after `invoice_date`
   - Currency codes are valid ISO 4217
3. **Confidence scoring**: combines several signals:
   - **Source grounding**: does each extracted value actually appear in the source text?
   - **Validation results**: failed or borderline business rules lower confidence
   - **Missing required fields**
   - **Model self-reported confidence** (used as a weak, supporting signal)
   - **Optional multi-run agreement** for high-stakes fields

Records scoring below `CONFIDENCE_THRESHOLD`, or failing any hard validation rule, are routed to the review queue.

---

## Human-in-the-Loop Review

- Flagged records appear in a review queue with the original document and extracted fields side by side
- Reviewers approve or correct values
- Approved records are written to the database
- Corrections are saved and can be reused as few-shot examples or added to the evaluation set

---

## Evaluation

Reliability should be measured, not assumed.

- Keep a labeled ground-truth set under `data/ground_truth/` (30 to 50 documents is a good start)
- Run the evaluation script to get **field-level precision, recall, and exact-match accuracy**
- Compare prompts, models, and schema versions against the same set before shipping changes

```bash
python -m evaluation.run --dataset data/ground_truth/ --report reports/latest.json
```

---

## Testing

```bash
pytest tests/ -v
```

Tests cover the classifier, extractor, schema validator, business-rule validator, and the full pipeline runner. Use mocked LLM responses for unit tests so they are fast and deterministic.

---

## Security & Privacy

Invoices and contracts often contain sensitive information.

- Never commit `.env` or API keys
- Encrypt data at rest and in transit
- Redact or minimize PII before logging
- Define a retention policy for raw documents and extracted records
- Check your LLM provider's data-handling and retention terms before processing sensitive documents

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes and add tests
4. Open a pull request

---

## License

MIT .