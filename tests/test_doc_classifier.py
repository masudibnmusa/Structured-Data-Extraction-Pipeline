from app.classification.doc_classifier import classify_document
from fakes import INVOICE_TEXT, FakeClient

EMAIL = "From: a@x.com\nTo: b@y.com\nSubject: Hello\n\nPlease reply.\nRegards, A"


def test_heuristics_classify_invoice_without_llm():
    client = FakeClient({})
    assert classify_document(INVOICE_TEXT.format(number="X"), client) == "invoice"
    assert client.calls == []


def test_heuristics_classify_email():
    assert classify_document(EMAIL, FakeClient({})) == "email"


def test_ambiguous_text_falls_back_to_llm():
    client = FakeClient({"classify_document": {"doc_type": "contract"}})
    assert classify_document("hello world", client) == "contract"
    assert client.calls == ["classify_document"]