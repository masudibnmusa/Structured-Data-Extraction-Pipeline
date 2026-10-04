from app.pipeline.pipeline_runner import process_document
from app.review_queue import queue_manager
from fakes import INVOICE_TEXT, FakeClient, invoice_data


def _write(tmp_path, number):
    p = tmp_path / f"{number}.txt"
    p.write_text(INVOICE_TEXT.format(number=number))
    return p


def test_clean_invoice_is_accepted(tmp_path):
    client = FakeClient({"record_invoice": invoice_data("INV-001")})
    result = process_document(_write(tmp_path, "INV-001"), client)
    assert result.status == "accepted"
    assert result.confidence >= 0.85
    assert not result.duplicate


def test_same_document_is_not_processed_twice(tmp_path):
    client = FakeClient({"record_invoice": invoice_data("INV-002")})
    path = _write(tmp_path, "INV-002")
    first = process_document(path, client)
    second = process_document(path, client)
    assert second.duplicate and second.record_id == first.record_id
    assert client.calls.count("record_invoice") == 1


def test_inconsistent_invoice_goes_to_review_then_approved(tmp_path):
    client = FakeClient({"record_invoice": invoice_data("INV-003", total=999.00)})
    result = process_document(_write(tmp_path, "INV-003"), client)
    assert result.status == "needs_review"
    assert any(f.startswith("rule:") for f in result.flags)

    fixed = invoice_data("INV-003", total=324.00)
    updated = queue_manager.approve(result.record_id, fixed, reviewer="tester")
    assert updated["status"] == "reviewed"