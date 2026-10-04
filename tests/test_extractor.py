from app.extraction.extractor import extract
from fakes import INVOICE_TEXT, FakeClient, invoice_data


def test_extract_calls_llm_with_schema_tool():
    client = FakeClient({"record_invoice": invoice_data()})
    out = extract(INVOICE_TEXT.format(number="INV-001"), "invoice", client)
    assert out["invoice_number"] == "INV-001"
    assert client.calls == ["record_invoice"]