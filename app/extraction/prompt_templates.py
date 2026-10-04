"""Per-schema extraction prompts."""

PROMPT_VERSION = "v1"

COMMON_RULES = """You are a precise data-extraction engine.
Rules:
- Extract ONLY information that is explicitly present in the document.
- Never guess or invent values. If a field is not present, use null (or omit it if optional).
- Dates must be ISO 8601 (YYYY-MM-DD). Numbers must be plain numbers without currency symbols or thousands separators.
- The text may contain OCR noise (e.g. 0/O, 1/l confusion); use context to read values correctly, but do not fabricate.
- Always respond by calling the provided tool."""

PROMPTS = {
    "invoice": COMMON_RULES + """

Document type: INVOICE.
- vendor_name is the company issuing the invoice (not the customer being billed).
- Capture every line item with quantity, unit_price and amount.
- subtotal is before tax; total is the final amount due.""",
    "contract": COMMON_RULES + """

Document type: CONTRACT / AGREEMENT.
- List every party with its role if stated.
- termination_summary and payment_terms should be brief, faithful summaries (1-2 sentences).""",
    "email": COMMON_RULES + """

Document type: EMAIL.
- sender and recipients should be email addresses when available, otherwise names.
- summary: 1-2 sentences. action_items: concrete requests or tasks only.""",
}

CLASSIFIER_PROMPT = """Classify the document into exactly one type:
- invoice: bills, invoices, receipts requesting payment
- contract: agreements, terms, NDAs, service contracts
- email: email messages or email threads
Respond by calling the provided tool."""