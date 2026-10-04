class FakeClient:
    """Stands in for LLMClient. `responses` maps tool_name -> dict to return."""

    def __init__(self, responses: dict):
        self.responses = responses
        self.calls: list[str] = []

    def extract_structured(self, system, user, tool_name, json_schema, description=""):
        self.calls.append(tool_name)
        return self.responses[tool_name]


INVOICE_TEXT = """INVOICE
Acme Supplies Ltd.
Invoice Number: {number}
Invoice Date: 2025-03-14
Due Date: 2025-04-13
Widget A 10 x 25.00 = 250.00
Widget B 4 x 12.50 = 50.00
Subtotal 300.00
Tax 24.00
Total Due 324.00 USD
"""


def invoice_data(number="INV-001", total=324.00):
    return {
        "vendor_name": "Acme Supplies Ltd.",
        "invoice_number": number,
        "invoice_date": "2025-03-14",
        "due_date": "2025-04-13",
        "currency": "usd",
        "line_items": [
            {"description": "Widget A", "quantity": 10, "unit_price": 25.00, "amount": 250.00},
            {"description": "Widget B", "quantity": 4, "unit_price": 12.50, "amount": 50.00},
        ],
        "subtotal": 300.00,
        "tax": 24.00,
        "total": total,
    }